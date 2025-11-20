"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.group_list, name='board'), 
    
    # 2. 로그인 페이지 (http://localhost:8000/login/)
    path('login/', views.user_login, name='login'),
    
    # 3. 프로필 페이지 (http://localhost:8000/profile/)
    path('profile/', views.user_profile, name='profile'),
    
    # 4. 랭킹 페이지 (http://localhost:8000/ranking/)
    path('ranking/', views.weekly_ranking, name='ranking'),
    
    # 5. 스터디룸/타이머 페이지 (그룹 코드가 URL에 포함됨, 예: http://localhost:8000/study/A1B2C3/)
    path('study/<str:group_code>/', views.study_timer, name='timer'),
    
    path('create/', views.create_study, name='create_study'),
    
    path('register/', views.user_register, name='register'),
]
