from django.views import View
from django.utils.decorators import method_decorator
from .helper import *


class Login(View):
    def get(self, request):
        ip = request.META['HTTP_HOST']
        logger(ip)
        return render(request, 'login.html')

    def post(self, request):
        user = request.POST.get('username')
        pwd = request.POST.get('password')
        response = login_handle(request, user, pwd)  # 处理用户登录，并返回相应的页面给用户
        return response


@method_decorator(auth, name='dispatch')
class Home(View):
    def get(self, request):
        auto_update_mysql()  # 管理员每次到home页面就刷新一下，将数据库作业信息修改
        reports = update_media()  # 上面是根据hash_test表中的作业修改student_test_info表中的作业， 这儿是修改MEDIA_DIR中的作业
        menus_files = get_test_menu_files()
        reports["START"] = list()
        for menu in menus_files.keys():
            reports["START"].append(menu)
        MAIN_MSG = mark_user_type(request)
        MAIN_MSG['REPORTS'] = reports
        return render(request, 'home.html', {'InfoHandled': MAIN_MSG})

    def post(self, request):
        """post还未添加功能"""
        MAIN_MSG['user_type'] = request.COOKIES.get('user_type')
        return render(request, 'home.html', {'InfoHandled': MAIN_MSG})


# 作业提交主页
@method_decorator(auth, name='dispatch')
class Upload(View):
    def get(self, request):
        return render(request, 'test_upload.html', {'InfoHandled': mark_user_type(request)})

    def post(self, request):
        return render(request, 'test_upload.html', {'InfoHandled': mark_user_type(request)})


@method_decorator(auth, name='dispatch')
class AllowUpload(View):
    """允许提交的作业"""
    def get(self, request):
        MAIN_MSG = mark_user_type(request)
        file_dict = get_test_menu_files()
        MAIN_MSG["file_dict"] = file_dict
        return render(request, "allow_upload.html", {"InfoHandled": MAIN_MSG})


@method_decorator(auth, name='dispatch')
class UploadTest(View):
    """提交作业页"""
    def get(self, request):
        return render(request, 'start_upload_test.html', {"InfoHandled": mark_user_type(request)})

    def post(self, request):
        file = request.FILES.get('upload')  # upload使用户选择文件的那个input的name
        file_dict = get_test_menu_files()
        response = upload_test_handle(request, file, file_dict)  # 逻辑处理，并返回相应的页面
        return response


@method_decorator(auth, name='dispatch')
class ShowUploaded(View):
    """显示已经提交过的作业"""
    def get(self, request):
        file_list = get_all_files()
        response = uploaded_handle(request, file_list)  # 逻辑处理，并返回相应的页面
        return response

    def post(self, request):
        return render(request, 'show_uploaded_test.html', {"InfoHandled": mark_user_type(request)})


# 管理主页
@method_decorator(auth, name='dispatch')
class Manage(View):

    def get(self, request):
        return render(request, 'test_manage.html', {"InfoHandled": mark_user_type(request)})

    def post(self, request):
        return render(request, 'test_manage.html', {"InfoHandled": mark_user_type(request)})


# 作业清单，管理员可在该页面下载文件
@method_decorator(auth, name='dispatch')
@method_decorator(access_permissiom, name='dispatch')
class TestList(View):
    def get(self, request):
        MAIN_MSG = mark_user_type(request)
        test_dict = get_test_menu_files()
        MAIN_MSG['menus_files'] = test_dict
        return render(request, 'test_list.html', {"InfoHandled": MAIN_MSG})

    def post(self, request):
        download_menu = request.POST.get('test_name')  # 获取管理员选择要下载的作业题目
        # print("要下载的题目:", download_menu)
        response = download_test_handle(request, download_menu)  # 逻辑处理，并返回相应的页面
        return response


# 作业提交状态（已提交，未提交）
@method_decorator(auth, name='dispatch')
class TestStatus(View):
    def get(self, request):
        MAIN_MSG = mark_user_type(request)
        stu_info_list = get_stu_info_in_sql()  # 包含所有学生所有作业提交的信息
        MAIN_MSG['stu_info'] = stu_info_list
        return render(request, 'test_status.html', {"InfoHandled": MAIN_MSG})

    def post(self, request):
        MAIN_MSG = mark_user_type(request)
        return render(request, 'test_status.html', {"InfoHandled": MAIN_MSG})


# 音乐下载主页
@method_decorator(auth, name='dispatch')
@method_decorator(access_permissiom, name='dispatch')
class Download(View):
    """下载音乐"""
    def get(self, request):
        # user_ip = request.META.get("REMOTE_ADDR")
        # print(user_ip)
        MAIN_MSG = mark_user_type(request)
        return render(request, 'music_download.html', {"InfoHandled": MAIN_MSG})

    def post(self, request):
        response = download_music_handle(request)  # 处理逻辑，并返回相应的页面
        return response


# 信息反馈主页
@method_decorator(auth, name='dispatch')
class InforToManager(View):
    def get(self, request):
        MAIN_MSG = mark_user_type(request)
        return render(request, 'information.html', {"InfoHandled": MAIN_MSG})

    def post(self, request):
        feedback = request.POST.get("reworkmes")
        response = feedback_handle(request, feedback)
        return response


@method_decorator(auth, name='dispatch')
class AccountManage(View):
    def get(self, request):
        MAIN_MSG = mark_user_type(request)
        return render(request, "account_manage.html", {"InfoHandled": MAIN_MSG})

    def post(self, request):
        response = account_handle(request)  # 处理逻辑，并返回相应的页面
        return response



