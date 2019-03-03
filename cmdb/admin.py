from django.contrib import admin
from cmdb import models
# Register your models here.

admin.site.register(models.SelfUser)
admin.site.register(models.StudentInfo)
admin.site.register(models.HashTest)
admin.site.register(models.StudentTestInfo)
admin.site.register(models.OtherUser)
