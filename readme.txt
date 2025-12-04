LazyCat - 스터디 타이머 & 커뮤니티 플랫폼
이 프로젝트는 Django와 Node.js를 활용하여 개발된 실시간 스터디 타이머 및 커뮤니티 웹 애플리케이션입니다.

제출 파일 구성
manage.py: Django 프로젝트 실행 파일
requirements.txt: 파이썬 의존성 패키지 목록
db.sqlite3: 데이터베이스 파일 (기본 데이터 포함)
config/: 프로젝트 설정 폴더
webapp/: 메인 애플리케이션 폴더
server/: 실시간 통신을 위한 Node.js 소켓 서버 폴더
templates/, static/: HTML 및 정적 파일

---

실행 방법 (필수)**************꼭 해주셔야합니다*******************
이 애플리케이션은 Django 서버(웹)와 Node.js 서버(실시간 기능)가 동시에 실행되어야 완벽하게 작동합니다.

환경 설정 및 패키지 설치
터미널에서 프로젝트 루트 디렉토리로 이동 후 아래 명령어를 실행하여 필요한 패키지를 설치합니다.

bash
pip install -r requirements.txt


테스트 계정 정보
원활한 테스트를 위해 아래 계정을 사용할 수 있습니다.

ID: lazycat
PW: 12341234
추가 ID:박민수 (채팅기능시도를 위한 아이디입니다. 시크릿모드로 들어가 채팅기능을 시도할수있습니다.)
PW:박민수
주요 기능
실시간 타이머: Socket.IO를 이용한 실시간 공부 시간 측정 및 동기화

실시간 채팅: 같은 스터디룸에 있는 유저와 대화 가능

고양이 수집 (Gamification): 공부 시간에 따라 레벨이 오르고, 고양이 가족이 늘어나는 애니메이션

랭킹 시스템: 유저들의 공부 시간을 기반으로 한 실시간 랭킹

게시판 & 스터디 그룹: 스터디 그룹 생성 및 참여 기능
기술 스택
Backend: Python (Django), Node.js (Socket.IO)

Frontend: HTML5, CSS3, JavaScript

Database: SQLite3