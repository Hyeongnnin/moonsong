# 🚀 프로젝트 설치 및 실행 가이드 (Setup Guide)

이 프로젝트를 로컬 환경에서 실행하기 위한 단계별 가이드입니다.

## 📋 사전 요구사항 (Prerequisites)
- **Python**: 3.10 이상
- **Node.js**: 18.0 이상
- **Git**

---

## 1. 프로젝트 클론 (Clone)
```bash
git clone <repository-url>
cd labor-law-diagnosis
```

## 2. 백엔드 설정 (Backend Setup)

### 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 환경변수 설정 (.env)
루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 입력하세요:
```ini
SECRET_KEY=your-secret-key-here
DEBUG=True
OPENAI_API_KEY=your-openai-api-key
```

### 데이터베이스 및 관리자 계정 설정
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 서버 실행
```bash
python manage.py runserver
```

---

## 3. 프론트엔드 설정 (Frontend Setup)

### 디렉토리 이동
```bash
cd frontend
```

### 의존성 설치
```bash
npm install
```

### 개발 서버 실행
```bash
npm run dev
```

---

## 4. 접속
브라우저를 열고 다음 주소로 접속하세요:
- **Frontend**: http://localhost:5173
- **Backend Admin**: http://localhost:8000/admin
