from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from webapp.models import StudyGroup
from django.shortcuts import get_object_or_404

# 1. 게시판 (스터디 그룹 탐색/매칭) 페이지
def group_list(request: HttpRequest) -> HttpResponse:
    return render(request, 'board.html', {})

# 2. 로그인 페이지
def user_login(request: HttpRequest) -> HttpResponse:
    # 로그인 로직을 처리하는 곳이지만, 현재는 템플릿만 렌더링
    return render(request, 'login.html', {})

# 3. 사용자 프로필 및 고양이 관리 페이지
def user_profile(request: HttpRequest) -> HttpResponse:
    # 사용자 데이터(닉네임, 고양이 레벨 등)를 템플릿에 전달할 수 있음
    return render(request, 'profile.html', {})

# 4. 랭킹 페이지 (주간/월간 경쟁 순위)
def weekly_ranking(request: HttpRequest) -> HttpResponse:
    # 랭킹 데이터를 조회하여 템플릿에 전달
    return render(request, 'ranking.html', {})

# 5. 스터디룸 타이머 페이지 (실시간 Websocket 연결 필요)
@login_required
def study_timer(request: HttpRequest, group_code: str) -> HttpResponse:
    
    # 1. group_code로 스터디 그룹 객체를 찾거나, 없으면 404 에러를 반환
    study = get_object_or_404(StudyGroup, group_code=group_code) 
    
    # 2. 현재 사용자가 그룹 멤버인지 확인 (템플릿의 is_member 조건에 사용)
    #    (사용자가 로그인되어 있고, 해당 그룹의 멤버인지 확인하는 로직)
    is_member = request.user.is_authenticated and study.members.filter(id=request.user.id).exists()

    context = {
        'study': study, # 📌 템플릿에 study 객체를 전달해야 {{ study.name }} 등을 사용할 수 있습니다.
        'group_code': group_code,
        'is_member': is_member,
    }
    
    return render(request, 'timer.html', context)

def create_study(request):
    """
    새로운 스터디를 개설하는 페이지를 렌더링합니다.
    """
    # 임시 템플릿(create_study.html)이 있다고 가정하고 렌더링
    return render(request, 'create_study.html', {})

def user_register(request):
    """
    회원가입 페이지를 렌더링합니다.
    """
    # 임시 템플릿(register.html)이 있다고 가정하고 렌더링
    return render(request, 'register.html', {})