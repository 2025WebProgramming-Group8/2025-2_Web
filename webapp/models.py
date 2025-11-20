from django.db import models
from django.contrib.auth.models import User

# 1. 사용자 프로필 (기본 User 모델 + 추가 정보)
class UserProfile(models.Model):
    # Django 기본 User와 1:1 연결
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 추가 필드 (profile.html에 있는 정보들)
    nickname = models.CharField(max_length=20, blank=True)
    level = models.IntegerField(default=1)  # Lv. 1
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) # 프로필 사진
    total_study_time = models.DurationField(null=True, blank=True) # 총 공부 시간
    
    def __str__(self):
        return self.user.username

# 2. 스터디 그룹 (board.html에 표시될 내용)
class StudyGroup(models.Model):
    name = models.CharField(max_length=100)  # 스터디 이름
    subject = models.CharField(max_length=50) # 과목명 (예: 웹프로그래밍)
    
    # 그룹 코드 (URL에 사용: /study/A1B2C/)
    group_code = models.CharField(max_length=20, unique=True) 
    
    description = models.TextField(blank=True) # 소개글
    created_at = models.DateTimeField(auto_now_add=True) # 생성일
    
    # 참여 멤버 (User와 다대다 관계)
    members = models.ManyToManyField(User, related_name='study_groups', blank=True)

    def __str__(self):
        return self.name

# 3. 공부 기록 (ranking.html 및 timer.html용)
class StudyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(StudyGroup, on_delete=models.SET_NULL, null=True)
    
    start_time = models.DateTimeField(auto_now_add=True) # 시작 시간
    end_time = models.DateTimeField(null=True, blank=True) # 종료 시간
    study_duration = models.DurationField(null=True, blank=True) # 공부한 시간 (종료 - 시작)

    def __str__(self):
        return f"{self.user} - {self.study_duration}"