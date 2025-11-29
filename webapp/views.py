import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt # API 호출을 위해 필요
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum

from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from webapp.models import StudyGroup, UserProfile, StudyGroupMember
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .forms import RegisterForm, StudyGroupForm
from django.db.models import Sum

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
@login_required
def user_profile(request: HttpRequest) -> HttpResponse:
    # 사용자 데이터(닉네임, 고양이 레벨 등)를 템플릿에 전달할 수 있음
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"nickname": request.user.username, "level": 1},
    )
    
    if request.method == "POST":
        nickname = request.POST.get("nickname", "").strip()
        email = request.POST.get("email", "").strip()
        avatar_index = request.POST.get("avatar_index")

        # 닉네임 변경
        if nickname:
            profile.nickname = nickname

        # 이메일 변경
        if email:
            request.user.email = email

        # 아바타 변경 (1~10 사이만 허용)
        if avatar_index:
            try:
                idx = int(avatar_index)
                if 1 <= idx <= 10:
                    profile.avatar_index = idx
            except ValueError:
                pass  # 숫자 아닌 값 들어오면 무시

        request.user.save()
        profile.save()

        return redirect("profile")  # 저장 후 프로필 페이지 다시 로딩
    
    total_time_display = "0시간 0분 0초"
    
    if request.user.is_authenticated:
        member_links = StudyGroupMember.objects.filter(user=request.user)
        total_time_result = member_links.aggregate(
            total_seconds=Sum('group_study_time')
        )['total_seconds']
        
        if total_time_result:
            
            # 총 초 단위로 변환
            if hasattr(total_time_result, 'total_seconds'):
                total_seconds = total_time_result.total_seconds()
            else:
                total_seconds = total_time_result 
                
            # 시, 분, 초 계산 
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60) # 👈 초 계산 추가
            
            parts = []
            if hours > 0:
                parts.append(f"{hours}시간")
            if minutes > 0 or hours > 0: # 시가 있거나 분이 0 이상일 때 분 표시
                 parts.append(f"{minutes}분")
            
            # 초는 항상 표시 (총 시간이 0일 때 0초를 표시하기 위함)
            parts.append(f"{seconds}초")

            total_time_display = " ".join(parts)
        else:
            total_time_display = "0분 0초" # 총 시간이 없을 때 기본값
    
    user_study_memberships = StudyGroupMember.objects.filter(user=request.user).select_related(
        'study_group', 
        'user__profile' # UserProfile 정보를 가져오기 위함
    )
    
    # avatar_index 필드가 있다고 가정 (없으면 기본값 1)
    avatar_index = getattr(profile, "avatar_index", 1)

    context = {
        "profile": profile,
        "avatar_index": avatar_index,
        "total_study_time_sum": total_time_display,
        "memberships": user_study_memberships,
    }

    return render(request, 'profile.html', context)
# 4. 랭킹 페이지 (공부 시간 순으로 정렬)
def weekly_ranking(request: HttpRequest) -> HttpResponse:
    # 1. 공부 기록이 있는 모든 유저를 가져옵니다.
    # 2. total_study_time이 높은 순서대로 정렬합니다.
    # 3. 상위 8명만 자릅니다 (포디움 3명 + 리스트 5명)
    rankers = UserProfile.objects.exclude(total_study_time=None).order_by('-total_study_time')[:8]
    
    return render(request, 'ranking.html', {'rankers': rankers})

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
            
            total_time = StudyGroupMember.objects.filter(user=user).aggregate(
                total=Sum('group_study_time')
            )['total']
            
            user.profile.total_study_time = total_time
            
            if total_time is not None:
                total_seconds = int(total_time.total_seconds())
                user.profile.level = total_seconds // 300 + 1
            else:
                user.profile.level = 1
            
            user.profile.save()
            # ---------------------------------------------------------

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

@login_required
def create_study(request):
    
    # 임시 그룹 코드 생성 함수는 그대로 유지
    def generate_random_code(length=6):
        import string, random
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for i in range(length))

    if request.method == 'POST':
        form = StudyGroupForm(request.POST) # POST 데이터로 폼 객체 생성
        if form.is_valid():
            try:
                new_study = form.save(commit=False)

                # 고유 그룹 코드 생성 및 할당 (충돌 방지)
                while True:
                    group_code = generate_random_code()
                    if not StudyGroup.objects.filter(group_code=group_code).exists():
                        break
                new_study.group_code = group_code
                new_study.save() # 1차 저장
                # 멤버십 객체 생성 및 M2M 관계 동기화
                StudyGroupMember.objects.create(
                    user=request.user,
                    study_group=new_study,
                    group_study_time=timedelta(seconds=0)
                )
                # M2M 관계 동기화 (StudyGroupMember를 through로 지정했더라도 안전하게 연결)
                new_study.members.add(request.user) 

                return redirect('timer', group_code=group_code)

            except Exception as e:
                # DB 저장 중 오류 발생 (예: IntegrityError)
                print(f"DB 저장 중 심각한 오류 발생: {e}")
                form.add_error(None, f"스터디 그룹 생성 중 오류가 발생했습니다: {e}")
                
    else: # GET 요청
        form = StudyGroupForm() # 빈 폼 객체 생성

    # 최종 렌더링: 오류 메시지를 포함한 폼 객체를 전달
    return render(request, 'create_study.html', {'form': form})

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
        
    # 다시 타이머 페이지로 돌아갑니다 (이제 멤버로 인식됨)
    return redirect('timer', group_code=group_code)

#프로필 이미지 저장
@login_required
def update_avatar(request):
    profile = request.user.profile

    try:
        data = json.loads(request.body)
        avatar_index = int(data.get("avatar_index"))
    except Exception:
        return HttpResponseBadRequest("Invalid data")

    if 1 <= avatar_index <= 10:
        profile.avatar_index = avatar_index
        profile.save()
        return JsonResponse({"status": "ok"})
    else:
        return HttpResponseBadRequest("Avatar index out of range")
        # 성공 후 타이머 페이지로 리디렉션
        return redirect('timer', group_code=group_code) 
    
    return redirect('timer', group_code=group_code)

def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = request.POST.get('email', '').strip()
            user.save()
            return redirect('login') 
    else:
        # GET 요청 시 빈 폼 객체를 생성합니다.
        form = UserCreationForm()
        
    context = {'form': form}
    return render(request, 'register.html', context)

# 비밀번호 변경 뷰 함수
@login_required
def change_password(request):
    if request.method == 'POST':
        # PasswordChangeForm을 사용하여 기존 비밀번호와 새 비밀번호를 검증합니다.
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user, request.POST)
        
        if form.is_valid():
            user = form.save()
            # 비밀번호 변경 후 세션을 업데이트합니다. (필수)
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            return redirect('profile')
        else:
            # 폼에 오류가 있을 경우, 오류 메시지를 포함한 폼을 다시 렌더링합니다.
            pass
    else:
        # GET 요청 시 빈 폼을 생성합니다.
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user)
        
    context = {
        'form': form,
    }
    return render(request, 'change_password.html', context) # 템플릿 이름은 'change_password.html'로 가정