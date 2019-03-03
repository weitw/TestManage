from django.conf.urls import url
from cmdb import views

urlpatterns = [
    url(r'^login', views.Login.as_view(), name="login"),
    url(r'^home', views.Home.as_view(), name="home"),
    url(r'^test_upload', views.Upload.as_view(), name="upload"),
    url(r'^test_manage', views.Manage.as_view(), name="manage"),
    url(r'^music_download', views.Download.as_view(), name="music"),
    url(r'^information', views.InforToManager.as_view(), name="information"),
]
