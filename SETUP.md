# 프로젝트 초기 실행 가이드

## 🚀 처음 프로젝트를 열 때 (초기 1회)

### 1단계: 백엔드 환경 설정

```bash
# 프로젝트 루트 디렉토리에서 실행
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2단계: 프론트엔드 환경 설정

```bash
# 새로운 터미널 창 열기 (Ctrl+Shift+`)
cd frontend
npm install
```

---

## ⚡ 매번 프로젝트를 실행할 때 (초기화 이후)

### 터미널 1: 백엔드 서버 실행

```bash
# 프로젝트 루트에서
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

python manage.py runserver 127.0.0.1:8000
```

### 터미널 2: 프론트엔드 서버 실행

```bash
# 새로운 터미널 창 열기
cd frontend
npm run dev
```

---

## 🌐 접속 주소

| 항목 | 주소 |
|------|------|
| **프론트엔드** | http://localhost:5174 |
| **백엔드 API** | http://127.0.0.1:8000 |
| **관리자 패널** | http://127.0.0.1:8000/admin |

---

## 💡 빠른 참고사항

### .venv 폴더는 Git에 포함되지 않음
- 새로운 환경에서 프로젝트를 받을 때는 항상 `pip install -r requirements.txt` 실행 필요

### node_modules 폴더도 Git에 포함되지 않음
- 새로운 환경에서는 `cd frontend && npm install` 실행 필요

### 포트 충돌이 발생하면
- Django: `python manage.py runserver 127.0.0.1:8080` (포트 변경)
- Vite: `npm run dev -- --port 5175` (포트 변경)

### 기존 데이터베이스 초기화 (필요시)
```bash
# db.sqlite3 파일 삭제
rm db.sqlite3

# 마이그레이션 다시 실행
python manage.py migrate
```

---

## 📋 완전 초기화 (문제 해결)

```bash
# 1. 모든 가상 환경 및 패키지 제거
rmdir /s .venv

# 2. node_modules 제거
cd frontend
rmdir /s node_modules

# 3. 처음부터 다시 시작 (위의 "처음 프로젝트를 열 때" 섹션 참조)
```

---

## ✅ 체크리스트

**프로젝트 실행 전 확인:**
- [ ] 터미널 1: Django 서버 실행 중 (http://127.0.0.1:8000 접속 가능)
- [ ] 터미널 2: Vite 서버 실행 중 (http://localhost:5174 접속 가능)
- [ ] 브라우저에서 프론트엔드 접속 가능

**문제 해결:**
- [ ] CORS 에러 → Django 서버가 실행 중인지 확인
- [ ] 포트 충돌 → 기존 프로세스 종료 후 재실행
- [ ] 패키지 에러 → pip install -r requirements.txt 또는 npm install 재실행
