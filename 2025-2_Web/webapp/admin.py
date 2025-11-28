from django.contrib import admin
from .models import UserProfile, StudyGroup, StudyLog

# 관리자 페이지에서 보일 모델 등록
admin.site.register(UserProfile)
admin.site.register(StudyGroup)
admin.site.register(StudyLog)