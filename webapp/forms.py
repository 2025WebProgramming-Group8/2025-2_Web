from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudyGroup

# 회원가입 폼
class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email'] # ID와 이메일 입력받기

class StudyGroupForm(forms.ModelForm):
    class Meta:
        model = StudyGroup
        fields = ['name', 'subject', 'description'] # 입력받을 필드만 지정
        labels = {
            'name': '스터디 이름',
            'subject': '과목',
            'description': '소개글',
        }