from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.db import models
from django.views import View
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.http import FileResponse
# from django.http import StreamingHttpResponse
from cmdb import models
import shutil
import re
import os
import time
from another.craw_music import KuGou, QQMusic, download
# Create your views here.

BASE_DIR = os.getcwd()
MEDIA_DIR = os.path.join(BASE_DIR, 'media/')
ANOTHER_DIR = os.path.join(BASE_DIR, 'another/')
main_msg = {"user_type": "another",
            "title": "我的主页"}


def logger(string_list):
    """将输入重定向到文件中logger.txt中,string_list: 这是要写入文件的内容,是列表"""
    try:
        with open("logger.txt", "a", encoding='utf-8') as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S $"))
            for item in string_list:
                f.write(str(item))
                f.write('\n')
            f.write('\n')
    except Exception as e:
        print("logger中出错>>", e)


def auth(func):
    """用来装饰，在每一个类之上，用于验证用户是否已经登录过"""
    def inner(request, *args, **kwargs):
        v = request.COOKIES.get('user_type')
        try:
            if not v:
                return render(request, 'login.html')
        except:
            pass
        return func(request, *args, **kwargs)
    return inner


def auth_two(func):
    def inner(request, *args, **kwargs):
        v = request.COOKIES.get("from_upload")
        try:
            if not v:
                return render("request", "test_upload.html")
        except:
            pass
        return func(request, *args, **kwargs)
    return inner


def page_main_msg(request, title="我的主页"):
    """返回用户用户类型和用户请求页面的主标题"""
    user_type = request.COOKIES.get('user_type')
    try:
        main_msg['title'] = title
        main_msg['user_type'] = user_type
    except:
        pass
    return main_msg


def kv_msg(key_info, value_info):
    """给这个字典添加信息"""
    main_msg[key_info] = value_info
    return main_msg


def get_test_menu_files():
    """获取服务器上的作业信息，然后将每个目录和对应目录下的文件作为字典返回。{'目录1':[该目录下的文件],['目录2':[该目录下的文件]}"""
    menus = os.listdir(MEDIA_DIR)  # 得到目录下的作业菜单
    files_dict = {}
    for menu in menus:
        try:
            if os.path.isdir(MEDIA_DIR+'/'+menu):
                files_dict[menu] = os.listdir(MEDIA_DIR+'/'+menu)
        except Exception as e:
            logger(["get_test_menu_files中出错>>{}".format(e)])
    return files_dict  # {'目录1':[该目录下的文件],['目录2':[该目录下的文件]}


def set_user_info(request, user_type, user, max_age=300):
    """
    设置登录用户的信息，cookie等
    :param request:
    :param user_type: 用户类型
    :param user: 用户名
    :param max_age: 最大在线时间
    :return: response
    """
    page_msg = kv_msg("user_type", user_type)
    page_msg = kv_msg("username", user)
    response = render(request, 'home.html', {'InfoHandled': page_msg})
    response.set_cookie('user_type', user_type, max_age=max_age)
    return response


class Login(View):
    def get(self, request):
        ip = request.META['HTTP_HOST']
        logger([ip])
        return render(request, 'login.html')

    def post(self, request):

        user = request.POST.get('username')
        pwd = request.POST.get('password')
        try:
            result = models.SelfUser.objects.filter(username=user, password=pwd).first()  # 得到的是一个对象
            if result:
                if user == 'root':
                    response = set_user_info(request, "Root", user, max_age=10000)
                    return response
                else:
                    response = set_user_info(request, "Manager", user, max_age=1800)
                    return response
            else:
                """说明用户不是管理员或者超级管理员"""
                result = models.OtherUser.objects.filter(username=user, password=pwd).first()
                if result:
                    """说明用户是普通用户"""
                    response = set_user_info(request, "Ordinary", user, max_age=300)
                    return response
                else:
                    """用户不是也普通用户或者密码错误"""
                    error_msg = "用户名或密码错误！"
                    page_msg = kv_msg("error_msg", error_msg)
                    return render(request, 'login.html', {"InfoHandled": page_msg})
        except Exception as e:
            logger(["Login登录异常>>{}".format(e)])
            return HttpResponse("<h2>404!<h2>")


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
                # 说明test没有在hash_test中，说明该作业被管理员删了,则student_test_info表中的作业也要被删除
                try:
                    drop_test = {"test": test}
                    models.StudentTestInfo.objects.filter(**drop_test).delete()
                    logger(["student_test_info表中删除了作业>>>{}".format(test)])
                except Exception as er:
                    logger(["auto_update_mysql函数中出错1>>{}".format(er)])
        for test in hash_test_list:
            if test not in student_test_info_list:
                # 说明该test是管理员新增的,则student_test_info表中的作业也要增加
                try:
                    add_test = {"test": test}
                    models.StudentTestInfo.objects.create(**add_test)
                    logger(["student_test_info表中增加了作业>>>{}".format(test)])
                except Exception as err:
                    logger(["auto_update_mysql函数中出错2>>{}".format(err)])
    except Exception as err:
        logger(["auto_update_mysql函数中出错3>>{}".format(err)])


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
                    logger(["删除了MEDIA_DIR中的作业>>{}".format(test)])
                    reports["END"].append(test)
                except Exception as er:
                    logger(["update_MEDIA_DIR1中出错>>{}".format(er)])
                    break
        for test in new_tests:
            """如果数据库中的作业MEDIA_DIR中没有，说明是管理员新增的，所以MEDIA_DIR中也要新增相应的目录"""
            if test not in old_tests:
                try:
                    path = os.path.join(MEDIA_DIR, test)
                    os.mkdir(path)
                    logger(["在MEDIA_DIR中增加了作业>>{}".format(test)])
                except Exception as e:
                    logger(["update_media2中出错>>{}".format(e)])
                    break
        # logger(["MEDIA_DIR中的作业已经更新"])
        return reports
    except Exception as e:
        logger(["update_media中出错>>{}".format(e)])
        return None


@method_decorator(auth, name='dispatch')
class Home(View):
    def get(self, request):
        auto_update_mysql()  # 管理员每次到home页面就刷新一下，将数据库作业信息修改
        reports = update_media()  # 上面是根据hash_test表中的作业修改student_test_info表中的作业， 这儿是修改MEDIA_DIR中的作业
        menus_files = get_test_menu_files()
        reports["START"] = list()
        for menu in menus_files.keys():
            reports["START"].append(menu)
        page_msg = page_main_msg(request, '我的主页')
        page_msg = kv_msg("REPORTS", reports)
        return render(request, 'home.html', {'InfoHandled': page_msg})

    def post(self, request):
        """post还未添加功能"""
        page_msg = page_main_msg(request, '我的主页')
        return render(request, 'home.html', {'InfoHandled': page_msg})


def update_mysql(file):
    """作业提交之后，就将数据库的信息改为1，表示用户已经提交了"""
    cmdb_hashtest_list = models.HashTest.objects.all().values('test')
    for item in cmdb_hashtest_list:
        # item类似{'test': '微机实验一'}
        try:
            if item.get('test') in file.name:
                dic = {"stu_" + file.name[7:9]: "1"}
                models.StudentTestInfo.objects.filter(**item).update(**dic)
        except Exception as e:
            logger(["update_mysql中出错>>{}".format(e)])


def get_all_files():
    """得到服务器中所有的作业列表，并返回"""
    files_dict = get_test_menu_files()  # {'目录1':[该目录下的文件],['目录2':[该目录下的文件]}
    file_list = []
    for files in files_dict.values():
        for file in files:
            file_list.append(file)
    return file_list


@method_decorator(auth, name='dispatch')  # 增加这句，说明所有用户都必须登录才能提交作业
class Upload(View):
    def get(self, request):
        test_status = ""
        page_msg = kv_msg('test_status', test_status)
        page_msg = page_main_msg(request, "作业提交平台")
        menus_tests = get_test_menu_files()
        page_msg = kv_msg('menus_tests', menus_tests)
        try:
            stu_cookie = request.COOKIES.get('user_cookies')
            file_list = get_all_files()
            the_stu_files = []
            for file in file_list:
                if stu_cookie in file:
                    the_stu_files.append(file)
            page_msg = kv_msg('uploaded_files', the_stu_files)
            response = render(request, 'test_upload.html', {'InfoHandled': page_msg})
            response.set_cookie('from_upload', "yes", max_age=300)
            return response
        except:
            response = render(request, 'test_upload.html', {'InfoHandled': page_msg})
            response.set_cookie('from_upload', "yes", max_age=300)
            return response

    def post(self, request):
        page_msg = page_main_msg(request, "作业提交平台")
        return render(request, 'test_upload.html', {'InfoHandled': page_msg})


@method_decorator(auth, name='dispatch')
@method_decorator(auth_two, name='dispatch')
class AllowUpload(View):
    # 显示允许提交的作业列表
    def get(self, request):
        page_msg = page_main_msg(request, '作业查看')
        file_dict = get_test_menu_files()
        page_msg = kv_msg("file_dict", file_dict)
        return render(request, "allow_upload.html", {"InfoHandled": page_msg})


@method_decorator(auth, name='dispatch')
@method_decorator(auth_two, name='dispatch')
class UploadTest(View):
    # 上传作业
    def get(self, request):
        page_msg = page_main_msg(request, '上传作业')
        return render(request, 'start_upload_test.html', {"InfoHandled": page_msg})

    def post(self, request):
        page_msg = page_main_msg(request, '上传作业')
        file = request.FILES.get('upload')  # upload使用户选择文件的那个input的name
        try:
            file_dict = get_test_menu_files()
            stu_test_save_menu = ""  # 学生作业保存目录
            for menu, files in file_dict.items():
                if menu in file.name:  # 如果服务器中目录名（也就是作业名）包含在学生上传的作业题目中，那就把学生的作业保存到改目录下
                    stu_test_save_menu = menu
                    break
            if "B160905" not in file.name or stu_test_save_menu == "":
                upload_msg = "文件'{}'丢失，原因是作业命名不规范".format(file.name)
                page_msg = kv_msg('upload_msg', upload_msg)
                return render(request, 'TestUploadStatus.html', {"InfoHandled": page_msg})
            path = os.path.join(MEDIA_DIR + stu_test_save_menu + "/" + file.name)
            # logger(["upload的post：学生作业保存目录", path])
            # *****************************将提交的作业保存至相应的目录***********************************
            try:
                with open(path, 'wb') as f:
                    for item in file.chunks():
                        f.write(item)
            except Exception as err:
                logger(["Upload中出错>1>>{}".format(err)])
            # **********这儿写一个作业提交成功，将数据库中相应的信息改为1,默认为0，所以只要没有提交成功，就不需要改****************
            # print('准备更新数据库')
            try:
                update_mysql(file)
            except Exception as e:
                logger(["update_mysql函数中出错>>数据更新失败,原因是{}".format(e)])
            # print('数据库更新')
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
            # print(upload_msg)
            stu_num = file.name[0:9]
            page_msg = kv_msg('upload_msg', upload_msg)
            response = render(request, 'TestUploadStatus.html', {"InfoHandled": page_msg})
            response.set_cookie('user_cookies', stu_num, max_age=240)  # 用户学号的cookie只有四分钟时间
            return response
        except AttributeError:
            upload_msg = "上传作业不能为空！"
            page_msg = kv_msg('upload_msg', upload_msg)
            return render(request, 'TestUploadStatus.html', {"InfoHandled": page_msg})
        except:
            upload_msg = "作业提交失败，请重新上传"
            page_msg = kv_msg('upload_msg', upload_msg)
            return render(request, 'TestUploadStatus.html', {"InfoHandled": page_msg})


@method_decorator(auth, name='dispatch')
@method_decorator(auth_two, name='dispatch')
class ShowUploaded(View):
    def get(self, request):
        page_msg = page_main_msg(request, '已上传的作业')
        return render(request, 'show_uploaded_test.html', {"InfoHandled": page_msg})

    def post(self, request):
        page_msg = page_main_msg(request, '已上传的作业')
        return render(request, 'show_uploaded_test.html', {"InfoHandled": page_msg})


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
        # logger(["stu_list 的结果为(这就是表头的信息)>>{}".format(stu_list)])
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
        # logger(["get_stu_info_in_sql函数调用成功!得到完整的学生信息"])
        return stu_info_list
    except Exception as er:
        logger(["get_stu_info_in_sql函数中出错>>{}".format(er)])
        return None


def download_tests(download_test):
    """ download_test管理员选择的要打包下载的作业题目，比如'微机实验二' """
    try:
        tests_dict = get_test_menu_files()
        download_menu = ''
        for menu, files in tests_dict.items():
            if menu in download_test:
                download_menu = menu
                break
        zip_test_path = os.path.join(BASE_DIR, '/another/ZIP_TEST')
        try:
            if not os.path.isdir(zip_test_path):
                os.mkdir(zip_test_path)
            logger(["创建了目录>>{}".format(zip_test_path)])
        except:
            pass
        path = os.path.join(MEDIA_DIR, download_menu)
        # print('要打包的文件所在目录', path)
        try:
            zip_files_dir = shutil.make_archive(zip_test_path+'/' + download_test, 'zip', path)  # 返回打包文件的完整路径
            # logger(["文件打包的路径是>>", zip_files_dir])
            return zip_files_dir
        except Exception as e:
            logger(["download_tests打包过程出错1>>{}".format(e)])
            return None
    except Exception as e:
        logger(["download_tests打包过程出错2>>".format(e)])
        return None


@method_decorator(auth, name='dispatch')
class Manage(View):

    def get(self, request):
        page_msg = page_main_msg(request, "作业管理平台")
        return render(request, 'test_manage.html', {"InfoHandled": page_msg})

    def post(self, request):
        page_msg = page_main_msg(request, "作业管理平台")
        return render(request, 'test_manage.html', {"InfoHandled": page_msg})


@method_decorator(auth, name='dispatch')
class TestList(View):
    def get(self, request):
        page_msg = page_main_msg(request, "作业清单")
        test_dict = get_test_menu_files()
        page_msg = kv_msg('menus_files', test_dict)
        return render(request, 'test_list.html', {"InfoHandled": page_msg})

    def post(self, request):
        page_msg = page_main_msg(request, "作业清单")
        download_menu = request.POST.get('test_name')  # 获取管理员选择要下载的作业题目
        # print("要下载的题目:", download_menu)
        if download_menu:
            zip_pack_path = download_tests(download_menu)
            if zip_pack_path:
                try:
                    # 若存在，说明返回的是已经打包好的文件路径
                    zip_file_name = re.findall(r'ZIP_TEST\\(.*)', zip_pack_path)[0]
                    # print('zip_file_name的值（打包的文件名）：>>>', zip_file_name)
                    file = open(zip_pack_path, 'rb')
                    response = FileResponse(file)
                    response['Content-Type'] = 'application/octet-stream'
                    response['Content-Disposition'] = 'attachment;filename={0}'.format(urlquote(zip_file_name))
                    # response['Content-Disposition'] = 'attachment;filename={0}'.format(zip_file_name.encode('utf-8'))
                    # response['Content-Disposition'] = 'attachment;filename="{}"'.format(zip_file_name)
                    logger(["管理员下载了作业>>>{}".format(zip_pack_path)])
                    return response
                except Exception as err:
                    logger(["test_list中的post中出错1>>>{}".format(err)])
                    return render(request, 'test_list.html')
            else:
                return render(request, 'test_list.html')
        return render(request, 'test_list.html', {"InfoHandled": page_msg})


@method_decorator(auth, name='dispatch')
class TestStatus(View):
    def get(self, request):
        page_msg = page_main_msg(request, "作业情况")
        stu_info_list = get_stu_info_in_sql()  # 包含所有学生所有作业提交的信息
        page_msg = kv_msg('stu_info', stu_info_list)
        return render(request, 'test_status.html', {"InfoHandled": page_msg})

    def post(self, request):
        page_msg = page_main_msg(request, "作业情况")
        return render(request, 'test_status.html', {"InfoHandled": page_msg})


@method_decorator(auth, name='dispatch')
class Download(View):
    """下载音乐"""
    def get(self, request):
        user_ip = request.META.get("REMOTE_ADDR")
        print(user_ip)
        page_msg = page_main_msg(request, 'VIP音乐下载')
        return render(request, 'music_download.html', {"InfoHandled": page_msg})

    def post(self, request):
        # user_ip = request.META.get("REMOTE_ADDR")
        # print(user_ip)
        try:
            page_msg = page_main_msg(request, 'VIP音乐下载')
            music_name = request.POST.get("music_name")
            search_type = request.POST.get("search_type")
            song_index = request.POST.get('index')  # 用户选择要下载音乐的序号,是一个字符串
            ku_gou = KuGou()  # 实例化
            qq_music = QQMusic()
            print(music_name, search_type, song_index)
            if music_name:
                if search_type == "kg":
                    user_request, song_list = ku_gou.get_kg_music_list(music_name)
                    if type(song_list) == dict:
                        # 如果是字典，说明出错了，那么就把错误信息返回去
                        page_msg = kv_msg("error_msg", song_list)
                        return render(request, "music_download.html", {"InfoHandled": page_msg})
                else:
                    user_request, song_list = qq_music.get_qq_music_list(music_name)
                    if type(song_list) == dict:
                        # 如果是字典，说明出错了，那么就把错误信息返回去
                        page_msg = kv_msg("error_msg", song_list)
                        return render(request, "music_download.html", {"InfoHandled": page_msg})
                page_msg = kv_msg("song_list", song_list)
                page_msg = kv_msg("user_request", user_request)
                return render(request, "music_download.html", {"InfoHandled": page_msg})
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
                        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(urlquote(this_song_name+".mp3"))
                        return response
                    if platform == "qq":
                        song_url = qq_music.download(music_name, song_index)
                        song_save_path = download(song_url, music_name, platform)
                        # print("QQ音乐返回了链接", song_url)
                        file = open(song_save_path, 'rb')
                        response = FileResponse(file)
                        response['Content-Type'] = 'application/octet-stream'
                        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(music_name+".m4a")
                        # if os.path.isfile(song_save_path):
                        #     os.remove(song_save_path)
                        return response
                except:
                    return render(request, 'music_download.html')
            page_msg = kv_msg("error", "搜索内容不能为空")
            return render(request, 'music_download.html', {"InfoHandled": page_msg})
        except:
            return render(request, 'music_download.html')


@method_decorator(auth, name='dispatch')
class InforToManager(View):
    def get(self, request):
        print(request)
        page_msg = page_main_msg(request, '信息反馈')
        return render(request, 'information.html', {"InfoHandled": page_msg})

    def post(self, request):
        page_msg = page_main_msg(request, '信息反馈')
        feedback = request.POST.get("reworkmes")
        feedback_path = os.path.join(BASE_DIR, "another/Feedback/" + request.COOKIES.get('user_type'))
        if feedback:
            try:
                with open(feedback_path+".txt", "a", encoding="utf-8") as f:
                    f.write(time.strftime("%Y/%m/%d/ %H:%M:%S $ "))
                    f.write(feedback)
                    f.write("\n")
                page_msg = kv_msg("error", "感谢您的反馈，管理员已经收到")
                return render(request, "feedback.html", {"InfoHandled": page_msg})
            except:
                page_msg = kv_msg("error", "反馈失败了")
                return render(request, "feedback.html", {"InfoHandled": page_msg})
        return render(request, 'information.html', {"InfoHandled": page_msg})


