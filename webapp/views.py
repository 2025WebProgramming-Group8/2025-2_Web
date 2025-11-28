import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt # API 호출을 위해 필요
from django.db.models import Q

from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from webapp.models import StudyGroup, UserProfile, StudyGroupMember

# 1. 게시판 (스터디 그룹 탐색/매칭) 페이지
def group_list(request: HttpRequest) -> HttpResponse:
    # 모든 스터디 그룹 조회
    groups = StudyGroup.objects.all()
    # 검색 기능 구현 (URL 쿼리 파라미터 'q'를 받음)
    query = request.GET.get('q')
    if query:
        # 그룹 이름(name), 과목(subject), 그룹 코드(group_code)에서 검색
        groups = groups.filter(
            Q(name__icontains=query) |
            Q(subject__icontains=query) |
            Q(group_code__icontains=query)
        ).distinct()
    context = {
        'groups': groups,  # 조회된 스터디 목록을 'groups' 키로 전달
        'query': query,    # 검색창에 입력된 내용을 다시 보여주기 위해 전달
    }
    # 템플릿 렌더링
    return render(request, 'board.html', context)

# 2. 로그인/로그아웃 페이지
def user_login(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        # 폼에서 사용자 이름과 비밀번호를 가져옵니다.
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 사용자 인증 시도
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 인증 성공 시 세션에 로그인 정보 저장
            login(request, user)
            
            # 로그인 성공 후 게시판 페이지로 리디렉션
            return redirect('board') # URL 이름이 'board'라고 가정
        else:
            # 인증 실패 시
            context = {
                'error_message': '아이디 또는 비밀번호가 올바르지 않습니다.',
                # 입력값을 유지하고 싶다면 'username': username을 컨텍스트에 추가
            }
            return render(request, 'login.html', context)
            
    # GET 요청 시 (최초 로그인 페이지 접속 시)
    return render(request, 'login.html', {})

def user_logout(request):
    logout(request)
    return redirect('board')
 
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
    
    study = get_object_or_404(StudyGroup, group_code=group_code) 
    initial_time = 0
    is_member = False # 기본값: 멤버 아님
    member_data = StudyGroupMember.objects.filter(study_group=study).select_related('user', 'user__profile')
    
    if request.user.is_authenticated:
        try:
            member_profile = StudyGroupMember.objects.get(user=request.user, study_group=study)
            duration_obj = member_profile.group_study_time
            
            if duration_obj and hasattr(duration_obj, 'total_seconds'):
                # DurationField 객체를 초 단위 정수로 변환
                initial_time = int(duration_obj.total_seconds())
            else:
                # None, 빈 문자열, 또는 유효하지 않은 객체인 경우 0으로 강제 설정
                initial_time = 0 
            
            is_member = True
            
        except StudyGroupMember.DoesNotExist:
            # 멤버가 아니면 is_member = False 유지 (가입 버튼 표시)
            is_member = False
            
    context = {
        'study': study,
        'group_code': group_code,
        'is_member': is_member,      # True/False에 따라 타이머/가입 버튼 표시
        'initial_time': str(initial_time), 
        'groups': member_data,
    }
    return render(request, 'timer.html', context)

# Node.js 서버로부터 공부 시간을 받아 DB에 저장하는 API 뷰
@csrf_exempt
def save_study_time(request: HttpRequest):
    if request.method == 'POST':
        try:
            # 데이터 파싱
            data = json.loads(request.body)
            user_id = data.get('userId')
            final_time = data.get('currentTime') # 초 단위 정수 (클라이언트에서 전송)
            room_id = data.get('room') # Node.js 서버에서 room ID도 보내줘야 함

            user = User.objects.get(id=user_id)
            study = StudyGroup.objects.get(id=room_id)
            
            # StudyGroupMember 객체를 가져와서 저장
            member_profile = StudyGroupMember.objects.get(user=user, study_group=study)
            
            # DurationField에 맞게 저장
            duration_to_save = timedelta(seconds=int(final_time))
            member_profile.group_study_time = duration_to_save
            member_profile.save()
            
            return JsonResponse({'status': 'success', 'saved_time': final_time})        
        # 예외 처리
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except StudyGroup.DoesNotExist: # StudyGroup 조회 실패 시 처리
            return JsonResponse({'status': 'error', 'message': 'StudyGroup not found'}, status=404)
        except StudyGroupMember.DoesNotExist: # 멤버 관계가 없는 경우 처리
            return JsonResponse({'status': 'error', 'message': 'User is not a member of this study group'}, status=403)
        except Exception as e:
            # 500 오류 처리 (디버깅에 유용)
            print(f"DB 저장 중 심각한 오류 발생: {e}") 
            return JsonResponse({'status': 'error', 'message': f"Internal Server Error: {e}"}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

def create_study(request):
    """
    새로운 스터디를 개설하는 페이지를 렌더링합니다.
    """
    # 임시 템플릿(create_study.html)이 있다고 가정하고 렌더링
    return render(request, 'create_study.html', {})

def join_study(request: HttpRequest, group_code: str) -> HttpResponse:
    study = get_object_or_404(StudyGroup, group_code=group_code)
    
    # POST 요청 및 로그인 상태 확인
    if request.method == 'POST' and request.user.is_authenticated:
        
        # StudyGroupMember 객체를 생성하거나 이미 존재하면 가져옵니다.
        StudyGroupMember.objects.get_or_create(
            user=request.user, 
            study_group=study, 
            defaults={'group_study_time': timedelta(seconds=0)}
        )
        study.members.add(request.user)
        
        # 성공 후 타이머 페이지로 리디렉션
        return redirect('timer', group_code=group_code) 
    
    return redirect('timer', group_code=group_code)

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 회원가입 성공 후 로그인 페이지 또는 게시판으로 리디렉션
            return redirect('login') 
    else:
        # GET 요청 시 빈 폼 객체를 생성합니다.
        form = UserCreationForm()
        
    context = {'form': form}
    return render(request, 'register.html', context)
