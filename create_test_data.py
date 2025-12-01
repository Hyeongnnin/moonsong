#!/usr/bin/env python
"""
테스트 데이터 생성 스크립트
python manage.py shell < create_test_data.py
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from labor.models import Employee, WorkRecord

User = get_user_model()

# 테스트 사용자 생성 (첫 번째 슈퍼유저 또는 테스트 유저)
try:
    user = User.objects.first()
except:
    user = User.objects.create_user(username='testuser', password='testpass')

print(f"User: {user.username}")

# 기존 Employee 삭제 (테스트용)
Employee.objects.filter(user=user).delete()

# Job 1: 카페 알바
job1 = Employee.objects.create(
    user=user,
    workplace_name="Starbucks 강남점",
    workplace_address="서울시 강남구",
    industry="음식료",
    employment_type="알바",
    start_date=date(2025, 1, 1),
    hourly_rate=Decimal('11500'),
    weekly_hours=Decimal('30'),
    is_current=True
)
print(f"Created Job: {job1.workplace_name}")

# Job 2: 편의점 야간
job2 = Employee.objects.create(
    user=user,
    workplace_name="GS25 역삼점",
    workplace_address="서울시 강남구",
    industry="소매",
    employment_type="알바",
    start_date=date(2025, 3, 1),
    hourly_rate=Decimal('12000'),
    weekly_hours=Decimal('25'),
    is_current=True
)
print(f"Created Job: {job2.workplace_name}")

# Job 3: 과외
job3 = Employee.objects.create(
    user=user,
    workplace_name="개인 과외",
    workplace_address="온라인",
    industry="교육",
    employment_type="프리랜서",
    start_date=date(2025, 5, 1),
    hourly_rate=Decimal('30000'),
    weekly_hours=Decimal('10'),
    is_current=True
)
print(f"Created Job: {job3.workplace_name}")

# Job 1: 카페의 근로 기록 생성 (현재 달 11월)
today = date.today()
year, month = today.year, today.month

# 11월 1일부터 오늘까지
for day in range(1, today.day + 1):
    work_date = date(year, month, day)
    
    # 주말(토,일)은 건너뜀 (1=월, 6=토, 0=일)
    if work_date.weekday() in [5, 6]:
        continue
    
    # 09:00 ~ 18:00 (점심시간 1시간)
    time_in = datetime.combine(work_date, datetime.min.time()).replace(hour=9)
    time_out = datetime.combine(work_date, datetime.min.time()).replace(hour=18)
    
    WorkRecord.objects.create(
        employee=job1,
        work_date=work_date,
        time_in=time_in,
        time_out=time_out,
        break_minutes=60,
        is_overtime=False,
        is_night=False,
        is_holiday=False
    )
    print(f"Created WorkRecord for {job1.workplace_name}: {work_date}")

# Job 2: 편의점의 근로 기록 생성
for day in range(1, today.day + 1):
    work_date = date(year, month, day)
    
    # 주말(토,일)만 근무
    if work_date.weekday() not in [5, 6]:
        continue
    
    # 20:00 ~ 02:00 (야간 근무)
    time_in = datetime.combine(work_date, datetime.min.time()).replace(hour=20)
    time_out = datetime.combine(work_date + timedelta(days=1), datetime.min.time()).replace(hour=2)
    
    WorkRecord.objects.create(
        employee=job2,
        work_date=work_date,
        time_in=time_in,
        time_out=time_out,
        break_minutes=30,
        is_overtime=False,
        is_night=True,
        is_holiday=False
    )
    print(f"Created WorkRecord for {job2.workplace_name}: {work_date}")

# Job 3: 과외의 근로 기록 생성
for day in range(5, today.day + 1, 7):  # 주 1회, 금요일
    work_date = date(year, month, day)
    if work_date > today:
        break
    
    time_in = datetime.combine(work_date, datetime.min.time()).replace(hour=19)
    time_out = datetime.combine(work_date, datetime.min.time()).replace(hour=21)
    
    WorkRecord.objects.create(
        employee=job3,
        work_date=work_date,
        time_in=time_in,
        time_out=time_out,
        break_minutes=0,
        is_overtime=False,
        is_night=False,
        is_holiday=False
    )
    print(f"Created WorkRecord for {job3.workplace_name}: {work_date}")

print("\n✓ 테스트 데이터 생성 완료!")
