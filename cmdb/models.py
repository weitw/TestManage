from django.db import models

# Create your models here.


class SelfUser(models.Model):
    """管理员和超级用户的表"""
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

    class Meta:
        db_table = "selfuser"


class OtherUser(models.Model):
    """普通用户的表"""
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)

    class Meta:
        db_table = "otheruser"


class StudentInfo(models.Model):
    """学生信息情况，即学生和每次作业提交情况"""
    stu_num = models.CharField(max_length=10)
    stu_name = models.CharField(max_length=10)

    class Meta:
        db_table = "studentinfo"


class HashTest(models.Model):
    """作业和建表字段的使用，例如,test_hash=test1, test_title=微机实验一"""
    test = models.CharField(max_length=20)

    class Meta:
        db_table = "hashtest"


class StudentTestInfo(models.Model):
    """学生作业情况"""
    test = models.CharField(max_length=60)
    stu_01 = models.CharField(max_length=5, default="0", null=True)
    stu_02 = models.CharField(max_length=5, default="0", null=True)
    stu_03 = models.CharField(max_length=5, default="0", null=True)
    stu_04 = models.CharField(max_length=5, default="0", null=True)
    stu_05 = models.CharField(max_length=5, default="0", null=True)
    stu_06 = models.CharField(max_length=5, default="0", null=True)
    stu_07 = models.CharField(max_length=5, default="0", null=True)
    stu_08 = models.CharField(max_length=5, default="0", null=True)
    stu_09 = models.CharField(max_length=5, default="0", null=True)
    stu_10 = models.CharField(max_length=5, default="0", null=True)
    stu_11 = models.CharField(max_length=5, default="0", null=True)
    stu_12 = models.CharField(max_length=5, default="0", null=True)
    stu_13 = models.CharField(max_length=5, default="0", null=True)
    stu_14 = models.CharField(max_length=5, default="0", null=True)
    stu_15 = models.CharField(max_length=5, default="0", null=True)
    stu_16 = models.CharField(max_length=5, default="0", null=True)
    stu_17 = models.CharField(max_length=5, default="0", null=True)
    stu_18 = models.CharField(max_length=5, default="0", null=True)
    stu_19 = models.CharField(max_length=5, default="0", null=True)
    stu_20 = models.CharField(max_length=5, default="0", null=True)
    stu_21 = models.CharField(max_length=5, default="0", null=True)
    stu_22 = models.CharField(max_length=5, default="0", null=True)
    stu_23 = models.CharField(max_length=5, default="0", null=True)
    stu_24 = models.CharField(max_length=5, default="0", null=True)
    stu_25 = models.CharField(max_length=5, default="0", null=True)
    stu_26 = models.CharField(max_length=5, default="0", null=True)
    stu_27 = models.CharField(max_length=5, default="0", null=True)
    stu_28 = models.CharField(max_length=5, default="0", null=True)
    stu_29 = models.CharField(max_length=5, default="0", null=True)
    stu_30 = models.CharField(max_length=5, default="0", null=True)
    stu_31 = models.CharField(max_length=5, default="0", null=True)
    stu_32 = models.CharField(max_length=5, default="0", null=True)

    class Meta:
        db_table = "studenttestinfo"


class UserIP(models.Model):
    """用户的IP，当他访问时获取，在其下载音乐时调用"""
    remote_addr = models.CharField(max_length=30)

    class Meta:
        db_table = "userip"



