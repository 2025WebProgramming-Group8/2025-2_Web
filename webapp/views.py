import uuid
from django.contrib.auth.decorators import login_required
from .forms import StudyGroupForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from .models import UserProfile, StudyGroup


# 1. 게시판 (스터디 그룹 탐색/매칭) 페이지
def group_list(request):
    # DB에 있는 모든 스터디 그룹을 가져옵니다.
    groups = StudyGroup.objects.all().order_by('-created_at') 
    
    # 'groups'라는 이름으로 HTML에 데이터를 보냅니다.
    return render(request, 'board.html', {'groups': groups})

# 2. 로그인 페이지 이거 만들기 굉장히 엄
def user_login(request):
    if request.method == 'POST':
        # 데이터 받아서 검증
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # 검증 통과시 로그인 처리
            user = form.get_user()
            login(request, user)
            return redirect('board') # 로그인 후 게시판으로 이동
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})
# 로그아웃 없어서 만들었습니다
def user_logout(request):
    logout(request)
    return redirect('login') # 로그아웃 후 로그인 페이지로 이동
# 세상에 회원가입도 없었네 대충 만들겠습니다
def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 회원가입 시 UserProfile도 같이 만들어줘야 에러가 안 납니다.
            UserProfile.objects.create(user=user, nickname=user.username, level=1)
            
            login(request, user) # 가입 후 바로 로그인
            return redirect('board') #리다이렉트 이렇게 쓰는거 맞는지는 잘 모르겠습니다.
    else:
        form = RegisterForm()
        
    return render(request, 'register.html', {'form': form})

# 3. 사용자 프로필 및 고양이 관리 페이지
def user_profile(request: HttpRequest) -> HttpResponse:
    # 사용자 데이터(닉네임, 고양이 레벨 등)를 템플릿에 전달할 수 있음
    return render(request, 'profile.html', {})

# 4. 랭킹 페이지 (주간/월간 경쟁 순위)
def weekly_ranking(request: HttpRequest) -> HttpResponse:
    # 랭킹 데이터를 조회하여 템플릿에 전달
    return render(request, 'ranking.html', {})

# 5. 스터디룸 타이머 페이지 (실시간 Websocket 연결 필요)
def study_timer(request: HttpRequest, group_code: str) -> HttpResponse:
    # 그룹 코드(group_code)를 인수로 받아 해당 스터디룸을 렌더링
    return render(request, 'timer.html', {'group_code': group_code})

def create_study(request):
    """
    새로운 스터디를 개설하는 페이지를 렌더링합니다.
    """
    # 임시 템플릿(create_study.html)이 있다고 가정하고 렌더링
    return render(request, 'create_study.html', {})

# 그룹 만들기 로직 구현 코드는 자동생성으로 하고 방장을 멤버로 추가함
@login_required # 로그인이 필수인 기능입니다
def create_study(request):
    if request.method == 'POST':
        form = StudyGroupForm(request.POST)
        if form.is_valid():
            study = form.save(commit=False) # DB에 저장하기 전 잠시 멈춤
            
            # 1. 랜덤 그룹 코드 생성 (예: 8자리 문자열)
            study.group_code = str(uuid.uuid4())[:8]
            
            # 2. 먼저 스터디 저장 (ID 생성)
            study.save()
            
            # 3. 만든 사람(방장)을 멤버에 추가 (Many-to-Many 관계는 저장 후 처리해야 함)
            study.members.add(request.user)
            
            # 4. 만들어진 스터디 방(타이머)으로 바로 이동
            return redirect('timer', group_code=study.group_code)
    else:
        form = StudyGroupForm()
        
    return render(request, 'create_study.html', {'form': form})

# 5. 스터디룸 타이머 페이지
def study_timer(request, group_code):
    # 1. URL에 있는 group_code로 DB에서 스터디 방을 찾습니다.
    # 만약 없는 코드라면 404 에러 페이지를 보여줍니다.
    study = get_object_or_404(StudyGroup, group_code=group_code)
    
    # 2. 현재 로그인한 유저가 이 방의 멤버인지 확인합니다.
    is_member = False
    if request.user.is_authenticated:
        if study.members.filter(id=request.user.id).exists():
            is_member = True

    context = {
        'study': study,
        'is_member': is_member,
    }
    return render(request, 'timer.html', context)

@login_required
def join_study(request, group_code):
    # 1. 해당 스터디 그룹을 찾습니다.
    study = get_object_or_404(StudyGroup, group_code=group_code)
    
    # 2. 이미 멤버가 아니라면 추가합니다.
    if request.user not in study.members.all():
        study.members.add(request.user)
        
    # 3. 다시 타이머 페이지로 돌아갑니다 (이제 멤버로 인식됨)
    return redirect('timer', group_code=group_code)