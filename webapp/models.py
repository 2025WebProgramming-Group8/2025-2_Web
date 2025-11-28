from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta

# 1. 사용자 프로필 (기본 User 모델 + 추가 정보)
class UserProfile(models.Model):
    # Django 기본 User와 1:1 연결
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 추가 필드 (profile.html에 있는 정보들)
    nickname = models.CharField(max_length=20, blank=True)
    level = models.IntegerField(default=1)  # Lv. 1
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) # 프로필 사진

    def __str__(self):
        return self.user.username

# 2. 스터디 그룹 (board.html에 표시될 내용)
class StudyGroup(models.Model):
    name = models.CharField(max_length=100)  # 스터디 이름
    subject = models.CharField(max_length=50) # 과목명 (예: 웹프로그래밍)
    group_code = models.CharField(max_length=20, unique=True) # 그룹 코드 (URL에 사용: /study/A1B2C/)
    description = models.TextField(blank=True) # 소개글
    created_at = models.DateTimeField(auto_now_add=True) # 생성일
    # ManyToMany 필드를 StudyGroupMember를 통해 관리하도록 명시
    members = models.ManyToManyField(
        User, 
        through='StudyGroupMember', # 중간 모델 지정
        related_name='study_groups', 
        blank=True
    )
    def __str__(self):
        return self.name
# 3. 그룹별 누적 시간을 저장할 중간 모델 추가 (핵심)
class StudyGroupMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    
    # 이 필드에 각 스터디별 누적 시간을 저장합니다.
    group_study_time = models.DurationField(default=timedelta(seconds=0))
    
    class Meta:
        # 한 사용자는 한 스터디에 한 번만 등록되도록 고유성 보장
        unique_together = ('user', 'study_group')
        
    def __str__(self):
        return f"{self.user.username} in {self.study_group.name}"
    
# 4. 공부 기록 (ranking.html 및 timer.html용)
class StudyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(StudyGroup, on_delete=models.SET_NULL, null=True)
    
    start_time = models.DateTimeField(auto_now_add=True) # 시작 시간
    end_time = models.DateTimeField(null=True, blank=True) # 종료 시간
    study_duration = models.DurationField(null=True, blank=True) # 공부한 시간 (종료 - 시작)

    def __str__(self):
        return f"{self.user} - {self.study_duration}"