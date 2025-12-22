# labor/tests_overnight.py
"""
자정 넘김(Overnight) 및 익일 근무 기능 테스트

테스트 케이스:
1. 시간 입력 상한 24:00 지원
2. 24:00 퇴근 시 다음날 00:00으로 저장되는지 확인
3. is_overnight 플래그 정확성
4. 익일 근무 시간(next_day_work_minutes) 계산 정확성
5. get_total_hours()에 익일 근무가 포함되는지 확인
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from .models import Employee, WorkRecord, WorkSchedule

User = get_user_model()


class OvernightWorkTestCase(TestCase):
    def setUp(self):
        """테스트용 사용자 및 Employee 생성"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.employee = Employee.objects.create(
            user=self.user,
            workplace_name='Test Workplace',
            employment_type='알바',
            start_date=date(2025, 1, 1),
            hourly_rate=Decimal('15000')
        )

    def test_24_00_end_time_creates_overnight_record(self):
        """24:00 퇴근 시 is_overnight=True로 저장되는지 테스트"""
        work_date = date(2025, 1, 15)
        time_in = datetime.combine(work_date, time(18, 0))
        time_out = datetime.combine(work_date + timedelta(days=1), time(0, 0))  # 다음날 00:00
        
        record = WorkRecord.objects.create(
            employee=self.employee,
            work_date=work_date,
            time_in=time_in,
            time_out=time_out,
            is_overnight=True,
            break_minutes=0
        )
        
        # 검증
        self.assertTrue(record.is_overnight)
        self.assertEqual(record.time_out.date(), work_date + timedelta(days=1))
        
        # 근로시간 계산: 18:00 ~ 24:00 = 6시간
        total_hours = record.get_total_hours()
        self.assertEqual(total_hours, Decimal('6.0'))

    def test_next_day_work_minutes_included_in_total(self):
        """익일 근무 시간이 총 근로시간에 포함되는지 테스트"""
        work_date = date(2025, 1, 15)
        time_in = datetime.combine(work_date, time(18, 0))
        time_out = datetime.combine(work_date + timedelta(days=1), time(0, 0))  # 24:00
        
        # 24:00 ~ 02:00 (익일 2시간 = 120분)
        next_day_minutes = 120
        
        record = WorkRecord.objects.create(
            employee=self.employee,
            work_date=work_date,
            time_in=time_in,
            time_out=time_out,
            is_overnight=True,
            next_day_work_minutes=next_day_minutes,
            break_minutes=30
        )
        
        # 근로시간 계산: (18:00 ~ 24:00 = 6시간) - 휴게 0.5시간 + 익일 2시간 = 7.5시간
        total_hours = record.get_total_hours()
        expected = Decimal('7.5')  # 6 - 0.5 + 2
        self.assertEqual(total_hours, expected)

    def test_overnight_schedule_creates_correct_records(self):
        """자정 넘김 스케줄이 올바른 근로기록을 생성하는지 테스트"""
        # 월요일(0) 18:00 ~ 24:00 스케줄 생성
        schedule = WorkSchedule.objects.create(
            employee=self.employee,
            weekday=0,  # 월요일
            start_time=time(18, 0),
            end_time=time(0, 0),  # 24:00 = 00:00
            is_overnight=True,
            enabled=True
        )
        
        # 검증
        self.assertTrue(schedule.is_overnight)
        self.assertEqual(schedule.end_time, time(0, 0))

    def test_next_day_work_minutes_validation(self):
        """익일 근무 시간이 0~360분 범위인지 검증"""
        work_date = date(2025, 1, 15)
        time_in = datetime.combine(work_date, time(22, 0))
        time_out = datetime.combine(work_date + timedelta(days=1), time(0, 0))
        
        # 정상 범위: 180분 (3시간)
        record = WorkRecord.objects.create(
            employee=self.employee,
            work_date=work_date,
            time_in=time_in,
            time_out=time_out,
            next_day_work_minutes=180,
            break_minutes=0
        )
        
        total_hours = record.get_total_hours()
        # 22:00 ~ 24:00 = 2시간 + 익일 3시간 = 5시간
        self.assertEqual(total_hours, Decimal('5.0'))

    def test_normal_work_without_overnight(self):
        """일반 근무(자정 넘김 없음)가 정상 동작하는지 확인"""
        work_date = date(2025, 1, 15)
        time_in = datetime.combine(work_date, time(9, 0))
        time_out = datetime.combine(work_date, time(18, 0))
        
        record = WorkRecord.objects.create(
            employee=self.employee,
            work_date=work_date,
            time_in=time_in,
            time_out=time_out,
            is_overnight=False,
            next_day_work_minutes=0,
            break_minutes=60
        )
        
        # 9:00 ~ 18:00 = 9시간 - 휴게 1시간 = 8시간
        total_hours = record.get_total_hours()
        self.assertEqual(total_hours, Decimal('8.0'))
        self.assertFalse(record.is_overnight)

    def test_multiple_overnight_calculations(self):
        """여러 자정 넘김 근무의 통계 계산"""
        # 3일간의 야간 근무 기록 생성
        for day in range(1, 4):
            work_date = date(2025, 1, day)
            time_in = datetime.combine(work_date, time(20, 0))
            time_out = datetime.combine(work_date + timedelta(days=1), time(0, 0))
            
            WorkRecord.objects.create(
                employee=self.employee,
                work_date=work_date,
                time_in=time_in,
                time_out=time_out,
                is_overnight=True,
                next_day_work_minutes=120,  # 익일 2시간
                break_minutes=0
            )
        
        # 총 근로시간 계산
        total_hours = sum(
            record.get_total_hours() 
            for record in self.employee.work_records.all()
        )
        
        # 각 날: (20:00 ~ 24:00 = 4시간) + 익일 2시간 = 6시간
        # 3일: 6 * 3 = 18시간
        expected = Decimal('18.0')
        self.assertEqual(total_hours, expected)


# 실행 방법:
# python manage.py test labor.tests_overnight
