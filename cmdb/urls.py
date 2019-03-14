from django.conf.urls import url
from cmdb import views

urlpatterns = [
    url(r'^login', views.Login.as_view(), name="login"),
    url(r'^home', views.Home.as_view(), name="home"),
    url(r'^test_upload', views.Upload.as_view(), name="upload"),
    url(r'^test_manage', views.Manage.as_view(), name="manage"),
    url(r'^music_download', views.Download.as_view(), name="music"),
    url(r'^information', views.InforToManager.as_view(), name="information"),
    url(r'^allow_upload', views.AllowUpload.as_view(), name="allow_upload"),
    url(r'^upload_test', views.UploadTest.as_view(), name="start_upload_test"),
    url(r'^show_uploaded', views.ShowUploaded.as_view(), name="show_uploaded"),
    url(r'^test_list', views.TestList.as_view(), name="test_list"),
    url(r'^test_status', views.TestStatus.as_view(), name="test_status"),
    url(r'^account_manage', views.AccountManage.as_view(), name="account_manage")
]
