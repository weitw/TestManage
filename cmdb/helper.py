# 业务逻辑代码中调用的方法，放到这儿了
from django.shortcuts import HttpResponse
from django.http import FileResponse
from django.db import models
from django.shortcuts import render
from django.utils.http import urlquote
from cmdb.craw_music import KuGou, QQMusic, download
from cmdb import models
import shutil
import time
import os
import re

BASE_DIR = os.getcwd()
MEDIA_DIR = os.path.join(BASE_DIR, 'media/')
ANOTHER_DIR = os.path.join(BASE_DIR, 'another/')
MAIN_MSG = {}  # 要传递到前端的信息。


def logger(*args):
    """将输入重定向到文件中logger.txt中,*args: 这是要写入文件的内容,元组类型"""
    try:
        with open("logger.txt", "a", encoding='utf-8') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S $"))
            for item in args:
                f.write(str(item))
                f.write('\n')
            f.write('\n')
    except Exception as e:
        print("logger中出错>>", e)


def auth(func):
    """用来装饰，在每一个类之上，用于验证用户是否已经登录过"""

    def inner(request, *args, **kwargs):
        v = request.COOKIES.get('user_type')
        # 如果get方法得不到，说明该用户未登陆过
        if not v:
            return render(request, 'login.html')
        MAIN_MSG["username"] = request.COOKIES.get("username")
        return func(request, *args, **kwargs)
    return inner


def access_permissiom(func):
    """访问权限。有些地方如果别人直接输入网址还是可以访问的，所以就增加一个权限判断"""
    def inner(request, *args, **kwargs):
        v = request.COOKIES.get('user_type')
        if not v:
            return render(request, 'login.html')
        if v not in ["Root", "Manager"]:
            return render(request, 'home.html')
        return func(request, *args, **kwargs)
    return inner


def mark_user_type(request):
    """标记用户用户类型,用于前端判断，以便显示不同的内容"""
    MAIN_MSG['user_type'] = request.COOKIES.get('user_type')
    return MAIN_MSG


def get_test_menu_files():
    """获取服务器上的作业信息，然后将每个目录和对应目录下的文件作为字典返回。{'目录1':[该目录下的文件],['目录2':[该目录下的文件]}"""
    menus = os.listdir(MEDIA_DIR)  # 得到目录下的作业菜单
    files_dict = {}
    for menu in menus:
        try:
            if os.path.isdir(MEDIA_DIR+'/'+menu):
                files_dict[menu] = os.listdir(MEDIA_DIR+'/'+menu)
        except Exception as e:
            logger("get_test_menu_files中出错>>{}".format(e))
    return files_dict  # {'目录1':[该目录下的文件],['目录2':[该目录下的文件]}


def set_user_info(request, user_type, user):
    """
    设置登录用户的信息，cookie等
    :param request:
    :param user_type: 用户类型
    :param user: 用户名
    :return: response
    """
    MAIN_MSG['user_type'] = user_type
    MAIN_MSG['username'] = user
    response = render(request, 'home.html', {'InfoHandled': MAIN_MSG})
    response.set_cookie('user_type', user_type)
    response.set_cookie('username', user)
    return response


def update_media():
    """对比当前的MEDIA_DIR中的作业和数据可hashtest中的作业是否一致，若不一致，则修改MEDIA_DIR中的作业目录"""
    try:
        old_tests = os.listdir(MEDIA_DIR)  # 类似['微机实验一', '微机实验二', '生物信息学']
        hash_test = models.StudentTestInfo.objects.all().values('test')
        new_tests = []
        for test_tuple in hash_test:
            new_tests.append(test_tuple.get('test', None))
        reports = dict(END=list())  # 主页通知的消息
        for test in old_tests:
            """如果MEDIA_DIR中的作业数据库中没有，说明是管理员删除的，所以MEDIA_DIR中相应的作业目录也删除"""
            if test not in new_tests:
                try:
                    path = os.path.join(MEDIA_DIR, test)
                    file_list = os.listdir(path)  # 得到目录下的所有文件
                    for file in file_list:
                        os.remove(os.path.join(path, file))  # 先递归的删除目录下的文件，最后删除目录
                    os.removedirs(path)
                    logger("删除了MEDIA_DIR中的作业>>{}".format(test))
                    reports["END"].append(test)
                except Exception as er:
                    logger("update_MEDIA_DIR1中出错>>{}".format(er))
                    break
        for test in new_tests:
            """如果数据库中的作业MEDIA_DIR中没有，说明是管理员新增的，所以MEDIA_DIR中也要新增相应的目录"""
            if test not in old_tests:
                try:
                    path = os.path.join(MEDIA_DIR, test)
                    os.mkdir(path)
                    logger("在MEDIA_DIR中增加了作业>>{}".format(test))
                except Exception as e:
                    logger("update_media2中出错>>{}".format(e))
                    break
        # logger("MEDIA_DIR中的作业已经更新")
        return reports
    except Exception as e:
        logger("update_media中出错>>{}".format(e))
        return None


def auto_update_mysql():
    """根据hash_test表里的作业自动更新数据库student_info表中的数据"""
    try:
        student_test_info = models.StudentTestInfo.objects.all().values('test')  # 取test列的数据，即作业名
        hash_test = models.HashTest.objects.all().values('test')  # 取test_title列的数据，作业名
        student_test_info_list = []
        hash_test_list = []
        for test_tuple in student_test_info:
            student_test_info_list.append(test_tuple.get('test', None))
        for test_tuple in hash_test:
            hash_test_list.append(test_tuple.get('test', None))
        for test in student_test_info_list:
            if test not in hash_test_list:
                """说明test没有在hash_test中，说明该作业被管理员删了,则student_test_info表中的作业也要被删除"""
                try:
                    drop_test = {"test": test}
                    models.StudentTestInfo.objects.filter(**drop_test).delete()
                    logger("student_test_info表中删除了作业>>>{}".format(test))
                except Exception as er:
                    logger("auto_update_mysql函数中出错1>>{}".format(er))
        for test in hash_test_list:
            if test not in student_test_info_list:
                """说明该test是管理员新增的,则student_test_info表中的作业也要增加"""
                try:
                    add_test = {"test": test}
                    models.StudentTestInfo.objects.create(**add_test)
                    logger("student_test_info表中增加了作业>>>{}".format(test))
                except Exception as err:
                    logger("auto_update_mysql函数中出错2>>{}".format(err))
    except Exception as err:
        logger("auto_update_mysql函数中出错3>>{}".format(err))


def get_all_files():
    """得到服务器中所有的作业列表，并返回"""
    files_dict = get_test_menu_files()  # {'目录1':[该目录下的文件],['目录2':[该目录下的文件]}
    file_list = []
    for files in files_dict.values():
        for file in files:
            file_list.append(file)
    return file_list


def update_mysql(file):
    """作业提交之后，就将数据库的信息改为1，表示用户已经提交了"""
    try:
        cmdb_hashtest_list = models.HashTest.objects.all().values('test')
        num = re.findall('.*B160905(\d\d)', file.name)[0]
        for item in cmdb_hashtest_list:
            """item类似{'test': '微机实验一'}"""
            try:
                if item.get('test') in file.name:
                    dic = {"stu_" + num: "1"}
                    models.StudentTestInfo.objects.filter(**item).update(**dic)
            except Exception as e:
                logger("update_mysql中出错>>{}".format(e))
    except:
        logger("数据库更新失败，该作业'{}'情况未变成1".format(file.name))


def get_stu_info_in_sql():
    """获取数据库userinfo中cmdb_studentinfo表的信息，并将这些信息打包返回"""
    try:
        stu_info_list = []  # 所有学生的信息，每个元素为一个字典，字典里是每个学生的信息
        test_hash_list = models.HashTest.objects.all().values('test')  # 类似[{'test':'微机实验一'}, {'test':'微机实验二'}]
        test_list = []  # 作业列表
        stu_list = ["学号", "姓名"]
        for item_dict in test_hash_list:
            stu_list.append(item_dict.get('test', None))
            test_list.append(item_dict.get('test', None))
        # print("stu_list 的结果为(这就是表头的信息)>>", stu_list)
        # logger("stu_list 的结果为(这就是表头的信息)>>{}".format(stu_list))
        stu_info_list.append(stu_list)  # stu_list是浏览器上显示学生作业情况的表格每一行的信息
        students_num_list = models.StudentInfo.objects.all().values('stu_num')
        students_name_list = models.StudentInfo.objects.all().values('stu_name')
        for i in range(0, len(students_num_list)):
            current_list = list()  # 每次循环保证这个列表里的数据就是一个学生的
            current_list.append(students_num_list[i].get('stu_num'))
            current_list.append(students_name_list[i].get('stu_name'))
            current_stu_num = students_num_list[i].get('stu_num')[7:9]
            num_index = "stu_" + current_stu_num
            test_status_list = models.StudentTestInfo.objects.all().values(num_index)
            # [{'stu_01': '0'}, {'stu_01': '1'},,,,,,]
            for row in test_status_list:
                current_list.append(row.get(num_index))
            stu_info_list.append(current_list)
        # logger("get_stu_info_in_sql函数调用成功!得到完整的学生信息")
        return stu_info_list
    except Exception as er:
        logger("get_stu_info_in_sql函数中出错>>{}".format(er))
        return None


def package_tests(download_test):
    """ download_test管理员选择的要打包下载的作业题目，比如'微机实验二' """
    try:
        tests_dict = get_test_menu_files()
        download_menu = ''
        for menu, files in tests_dict.items():
            if menu in download_test:
                download_menu = menu
                break
        zip_test_path = os.path.join(BASE_DIR, 'another/ZIP_TEST')  # 把文件打包到改路径下
        try:
            if not os.path.isdir(zip_test_path):
                os.mkdir(zip_test_path)
                logger("创建了目录>>{}".format(zip_test_path))
        except:
            pass
        path = os.path.join(MEDIA_DIR, download_menu)  # 要打包的文件所在目录
        try:
            zip_files_dir = shutil.make_archive(zip_test_path+'/' + download_test, 'zip', path)  # 返回打包文件的完整路径
            logger("文件打包的路径是>>", zip_files_dir)
            return zip_files_dir
        except Exception as e:
            logger("download_tests打包过程出错1>>{}".format(e))
            return None
    except Exception as e:
        logger("download_tests打包过程出错2>>".format(e))
        return None


def login_handle(request, user, pwd):
    try:
        result = models.SelfUser.objects.filter(username=user, password=pwd).first()  # 得到的是一个对象
        if result:
            if user == 'root':
                response = set_user_info(request, "Root", user)
            else:
                response = set_user_info(request, "Manager", user)
        else:
            """说明用户不是管理员或者超级管理员"""
            result = models.OtherUser.objects.filter(username=user, password=pwd).first()
            if result:
                """说明用户是普通用户"""
                response = set_user_info(request, "Ordinary", user)
            else:
                """用户不是也普通用户或者密码错误"""
                error_msg = "用户名或密码错误！"
                MAIN_MSG['error_msg'] = error_msg
                response = render(request, 'login.html', {"InfoHandled": MAIN_MSG})
        return response
    except:
        response = render(request, 'login.html')
        return response


def uploaded_handle(request, file_list):
    MAIN_MSG = mark_user_type(request)
    username = request.COOKIES.get('username')  # 用户的学号
    test_status = ""
    MAIN_MSG['test_status'] = test_status
    try:
        the_stu_files = []
        for file in file_list:
            if username in file:
                the_stu_files.append(file)
        MAIN_MSG["uploaded_files"] = the_stu_files
        response = render(request, 'show_uploaded_test.html', {'InfoHandled': MAIN_MSG})
        return response
    except Exception as e:
        print("出错了", e)
        response = render(request, 'test_upload.html', {'InfoHandled': MAIN_MSG})
        return response


def upload_test_handle(request, file, file_dict):
    """提交作业页面的逻辑代码"""
    MAIN_MSG = mark_user_type(request)
    try:
        stu_test_save_menu = ""  # 学生作业保存目录
        for menu, files in file_dict.items():
            if menu in file.name:  # 如果服务器中目录名（也就是作业名）包含在学生上传的作业题目中，那就把学生的作业保存到改目录下
                stu_test_save_menu = menu
                break
        if "B160905" not in file.name or stu_test_save_menu == "":
            upload_msg = "文件'{}'丢失，原因是作业命名不规范".format(file.name)
            MAIN_MSG["upload_msg"] = upload_msg
            response = render(request, 'TestUploadStatus.html', {"InfoHandled": MAIN_MSG})
            return response
        path = os.path.join(MEDIA_DIR + stu_test_save_menu + "/" + file.name)
        # logger("upload的post：学生作业保存目录", path)
        # *****************************将提交的作业保存至相应的目录***********************************
        try:
            with open(path, 'wb') as f:
                for item in file.chunks():
                    f.write(item)
        except Exception as err:
            logger("Upload中出错>1>>{}".format(err))
        # **********这儿写一个作业提交成功，将数据库中相应的信息改为1,默认为0，所以只要没有提交成功，就不需要改****************

        update_mysql(file)  # 提交成功就更新数据库，让该作业对应的值变为1

        stu_test_dict = get_test_menu_files()
        upload_msg = "作业提交成功"
        for menu, files in stu_test_dict.items():
            try:
                if menu in file.name:
                    for f in files:
                        if f == file.name:
                            upload_msg = '作业已更新!'
            except:
                upload_msg = '上传作业不能为空！'
        MAIN_MSG["upload_msg"] = upload_msg
        response = render(request, 'TestUploadStatus.html', {"InfoHandled": MAIN_MSG})
        return response
    except AttributeError:
        upload_msg = "上传作业不能为空！"
        MAIN_MSG[upload_msg] = upload_msg
        response = render(request, 'TestUploadStatus.html', {"InfoHandled": MAIN_MSG})
        return response
    except:
        upload_msg = "作业提交失败，请重新上传"
        MAIN_MSG[upload_msg] = upload_msg
        response = render(request, 'TestUploadStatus.html', {"InfoHandled": MAIN_MSG})
        return response


def download_test_handle(request, download_menu):
    MAIN_MSG = mark_user_type(request)
    if download_menu:
        zip_pack_path = package_tests(download_menu)
        logger("要下载的文件打包的绝对路径zip_pack_path>>{}".format(zip_pack_path))
        if zip_pack_path:
            try:
                # 若存在，说明返回的是已经打包好的文件路径
                file = open(zip_pack_path, 'rb')
                response = FileResponse(file)
                response['Content-Type'] = 'application/octet-stream'
                response['Content-Disposition'] = 'attachment;filename={0}'.format(urlquote(download_menu + ".zip"))
                logger("管理员下载了作业>>>{}".format(zip_pack_path))
                return response
            except Exception as err:
                logger("test_list中的post中出错1>>>{}".format(err))
                response = render(request, 'test_list.html')
                return response
        else:
            response = render(request, 'test_list.html')
            return response
    response = render(request, 'test_list.html', {"InfoHandled": MAIN_MSG})
    return response


def download_music_handle(request):
    try:
        MAIN_MSG = mark_user_type(request)
        music_name = request.POST.get("music_name")
        search_type = request.POST.get("search_type")
        song_index = request.POST.get('index')  # 用户选择要下载音乐的序号,是一个字符串
        ku_gou = KuGou()  # 实例化
        qq_music = QQMusic()
        # print(music_name, search_type, song_index)
        if music_name:
            if search_type == "kg":
                user_request, song_list = ku_gou.get_kg_music_list(music_name)
                if type(song_list) == dict:
                    # 如果是字典，说明出错了，那么就把错误信息返回去
                    MAIN_MSG['error_msg'] = song_list
                    response = render(request, "music_download.html", {"InfoHandled": MAIN_MSG})
                    return response
            else:
                user_request, song_list = qq_music.get_qq_music_list(music_name)
                if type(song_list) == dict:
                    # 如果是字典，说明出错了，那么就把错误信息返回去
                    MAIN_MSG['error_msg'] = song_list
                    response = render(request, "music_download.html", {"InfoHandled": MAIN_MSG})
                    return response
            MAIN_MSG['song_list'] = song_list
            MAIN_MSG['user_request'] = user_request
            response = render(request, "music_download.html", {"InfoHandled": MAIN_MSG})
            return response
        if song_index:
            try:
                # 说明用户是要下载音乐
                music_name = request.POST.get("remusic_name")
                platform = request.POST.get("platform")
                if platform == "kg":
                    song_url, this_song_name = ku_gou.download(music_name, song_index)
                    # song_url是要下载音乐的下载链接，this_song_name是要下载音乐的名字
                    song_save_path = download(song_url, music_name, platform)
                    file = open(song_save_path, 'rb')
                    response = FileResponse(file)
                    response['Content-Type'] = 'application/octet-stream'
                    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(urlquote(this_song_name + ".mp3"))
                    return response
                if platform == "qq":
                    song_url = qq_music.download(music_name, song_index)
                    song_save_path = download(song_url, music_name, platform)
                    # print("QQ音乐返回了链接", song_url)
                    file = open(song_save_path, 'rb')
                    response = FileResponse(file)
                    response['Content-Type'] = 'application/octet-stream'
                    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(music_name + ".m4a")
                    # if os.path.isfile(song_save_path):
                    #     os.remove(song_save_path)
                    return response
            except:
                response = render(request, 'music_download.html')
                return response
        MAIN_MSG['error'] = "搜索内容不能为空"
        response = render(request, 'music_download.html', {"InfoHandled": MAIN_MSG})
        return response
    except:
        response = render(request, 'music_download.html')
        return response


def feedback_handle(request, feedback):
    MAIN_MSG = mark_user_type(request)
    feedback_path = os.path.join(BASE_DIR, "another/Feedback/" + request.COOKIES.get('user_type'))
    if feedback:
        try:
            with open(feedback_path + ".txt", "a", encoding="utf-8") as f:
                # f.write(time.strftime("%Y/%m/%d/ %H:%M:%S $ "))  # 时间不准？
                f.write("{} $ ".format(request.COOKIES.get("username")))
                f.write(feedback)
                f.write("\n")
            MAIN_MSG['error'] = "感谢您的反馈，管理员已经收到"
            response = render(request, "feedback.html", {"InfoHandled": MAIN_MSG})
            return response
        except:
            MAIN_MSG['error'] = "反馈失败了"
            response = render(request, "feedback.html", {"InfoHandled": MAIN_MSG})
            return response
    response = render(request, 'information.html', {"InfoHandled": MAIN_MSG})
    return response


def account_handle(request):
    """返回到前端的MAIN_MSG
            status="1":修改成功,
            status="0":当前密码不正确，
            status="-1":两次密码不一致，
            status="2":程序出错。
            """
    current_pwd = request.POST.get("current_pwd")
    new_pwd = request.POST.get("new_pwd")
    new_pwd_again = request.POST.get("new_pwd_again")
    username = request.COOKIES.get("username")
    user_type = request.COOKIES.get("user_type")
    if user_type in ["Root", "Manager"]:
        obj = models.SelfUser.objects.filter(username=username, password=current_pwd)
    else:
        obj = models.OtherUser.objects.filter(username=username, password=current_pwd)
    if obj:
        if new_pwd_again == new_pwd:
            try:
                obj.update(password=new_pwd)
                MAIN_MSG['status'] = "1"
                response = render(request, "account_manage_status.html", {"InfoHandled": MAIN_MSG})
                return response
            except:
                MAIN_MSG['status'] = "2"
                response = render(request, "account_manage_status.html", {"InfoHandled": MAIN_MSG})
                return response
        else:
            MAIN_MSG['status'] = "1"
    else:
        MAIN_MSG['status'] = "0"
    response = render(request, "account_manage_status.html", {"InfoHandled": MAIN_MSG})
    return response

