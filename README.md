# 2025-2 웹프로그래밍 8조 개발 Repository

> 2025학년도 2학기 웹프로그래밍 수업의 8조 프로젝트 개발을 위한 저장소입니다.

## 🎯 프로젝트 개요 (Project Overview)

본 프로젝트는 2025학년도 2학기 웹프로그래밍 과목에서 요구하는 기능을 구현하며, **사용자 친화적인 인터페이스**와 **견고한 백엔드 로직** 구축을 목표로 합니다.

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 | 설명 |
| :--- | :--- | :--- |
| **Backend** | **Python Django Framework** | 빠르고 안정적인 서버 로직 및 데이터베이스 연동을 담당합니다. |
| **Frontend** | **HTML + CSS** | 사용자에게 보여지는 화면 구조 및 스타일링을 담당합니다. (필요 시 JavaScript 추가) |
| **Version Control** | Git / GitHub (or GitLab) | 형상 관리 및 팀 협업을 위한 도구입니다. |

## 📂 프로젝트 구조 (Project Structure)

본 프로젝트는 팀 규정 및 Django 초기 생성 구조에 따라, `config` 폴더가 프로젝트 설정과 메인 앱 역할을 모두 담당하는 형태로 구성되어 있습니다.
```
2025-2_Web/
├── manage.py                  # 서버 실행, 마이그레이션 등 Django 관리 명령어
├── db.sqlite3                 # SQLite 데이터베이스 파일
├── config/                    # 프로젝트 설정 + 메인 앱
│   ├── __pycache__/           # Python 바이트코드 캐시 디렉토리
│   ├── __init__.py            # Python 모듈 초기화 파일
│   ├── settings.py            # Django 환경 설정 (DB, INSTALLED_APPS, STATIC 등)
│   ├── urls.py                # 메인 URL 라우팅
│   ├── asgi.py                # ASGI(비동기) 서버 설정
│   └── wsgi.py                # WSGI(배포용) 서버 설정
├── webapp                     # 
│   ├── views.py               # 페이지 렌더링 뷰 함수
├── templates/                 # HTML 템플릿
│   ├── base.html              # 기본 레이아웃 템플릿
│   ├── board.html             # 게시판 페이지
│   ├── footer.html            # 공통 footer 영역
│   ├── gnb.html               # 네비게이션(Global Navigation Bar)
│   ├── login.html             # 로그인 페이지
│   ├── profile.html           # 프로필 페이지
│   ├── ranking.html           # 랭킹 페이지
│   └── timer.html             # 타이머 페이지
└── static/                    # 정적 파일
    └── style.css              # 프로젝트 공통 스타일시트

```
## 👥 팀원 (Team Members)

| 역할 | 이름 | GitHub ID | 연락처/비고 |
| :--- | :--- | :--- | :--- |
| 조장 | [김재민] | [@Jaem1nKim] | [jmkim0212@yonsei.ac.kr] |
| 조원 | [박정우] | [@qwfmok] | [pdnrdl2@yonsei.ac.kr] |
| 조원 | [장현빈] | [@github-id] | [] |
| 조원 | [박성준] | [@github-id] | [parkstarj@yonsei.ac.kr] |
| 조원 | [이준홍] | [@github-id] | [] |

## 🚀 시작 방법 (Getting Started)

프로젝트를 로컬 환경에서 실행하기 위한 최소한의 단계입니다.

### 1. 저장소 클론 (Clone Repository)

```bash
git clone https://github.com/2025WebProgramming-Group8/2025-2_Web.git
cd 2025-2_Web

