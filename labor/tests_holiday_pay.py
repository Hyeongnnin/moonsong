from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from .models import Employee, WorkRecord, WorkSchedule
from .services import calculate_weekly_holiday_pay_v2, get_monthly_holiday_pay_info

User = get_user_model()

class HolidayPayTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.employee = Employee.objects.create(
            user=self.user,
            workplace_name='Test Workplace',
            hourly_rate=Decimal('10000'),
            start_date=date(2025, 1, 1),
            contract_weekly_hours=20
        )
        # 월~금 4시간씩 (총 20시간)
        for i in range(5):
            WorkSchedule.objects.create(
                employee=self.employee,
                weekday=i,
                start_time=time(9, 0),
                end_time=time(13, 0),
                enabled=True
            )

    def test_eligible_holiday_pay(self):
        """20시간 계약 + 개근 시 주휴수당 발생 확인"""
        target_date = date(2025, 1, 6) # 월요일
        # 월~금 근무 기록 생성
        for i in range(5):
            d = target_date + timedelta(days=i)
            WorkRecord.objects.create(
                employee=self.employee,
                work_date=d,
                attendance_status='REGULAR_WORK',
                time_in=datetime.combine(d, time(9, 0)),
                time_out=datetime.combine(d, time(13, 0))
            )
        
        res = calculate_weekly_holiday_pay_v2(self.employee, target_date)
        self.assertTrue(res['is_eligible'])
        # 주휴시간 = 20 / 5 = 4시간
        # 금액 = 4 * 10000 = 40000
        self.assertEqual(res['amount'], 40000)
        self.assertEqual(res['hours'], 4.0)

    def test_not_eligible_due_to_absence(self):
        """결근 시 주휴수당 0원 확인"""
        target_date = date(2025, 1, 13) # 월요일
        # 수요일(15일) 결근 처리 (기록 미생성 시 결근으로 간주)
        for i in [0, 1, 3, 4]: # 2(수) 제외
            d = target_date + timedelta(days=i)
            WorkRecord.objects.create(
                employee=self.employee,
                work_date=d,
                attendance_status='REGULAR_WORK',
                time_in=datetime.combine(d, time(9, 0)),
                time_out=datetime.combine(d, time(13, 0))
            )
        
        res = calculate_weekly_holiday_pay_v2(self.employee, target_date)
        self.assertFalse(res['is_eligible'])
        self.assertEqual(res['amount'], 0)
        self.assertEqual(res['reason'], 'not_perfect_attendance')

    def test_eligible_with_annual_leave(self):
        """연차 사용 시 개근으로 인정되어 주휴수당 발생 확인"""
        target_date = date(2025, 1, 20) # 월요일
        # 수요일 연차
        for i in range(5):
            d = target_date + timedelta(days=i)
            status = 'ANNUAL_LEAVE' if i == 2 else 'REGULAR_WORK'
            WorkRecord.objects.create(
                employee=self.employee,
                work_date=d,
                attendance_status=status,
                time_in=datetime.combine(d, time(9, 0)) if status == 'REGULAR_WORK' else None,
                time_out=datetime.combine(d, time(13, 0)) if status == 'REGULAR_WORK' else None
            )
        
        res = calculate_weekly_holiday_pay_v2(self.employee, target_date)
        self.assertTrue(res['is_eligible'])
        self.assertEqual(res['amount'], 40000)

    def test_not_eligible_less_than_15h(self):
        """주 15시간 미만 시 0원 확인"""
        self.employee.contract_weekly_hours = 12
        self.employee.save()
        
        target_date = date(2025, 2, 3) # 월요일
        res = calculate_weekly_holiday_pay_v2(self.employee, target_date)
        self.assertFalse(res['is_eligible'])
        self.assertEqual(res['amount'], 0)
        self.assertEqual(res['reason'], 'less_than_threshold')

    def test_monthly_accumulation(self):
        """월 누적 금액 확인"""
        # 1월 3주간 개근 기록 생성
        # 1주: 1/6~1/12
        # 2주: 1/13~1/19
        for week in range(2):
            monday = date(2025, 1, 6) + timedelta(days=week*7)
            for day in range(5):
                d = monday + timedelta(days=day)
                WorkRecord.objects.create(
                    employee=self.employee,
                    work_date=d,
                    attendance_status='REGULAR_WORK',
                    time_in=datetime.combine(d, time(9, 0)),
                    time_out=datetime.combine(d, time(13, 0))
                )
        
        # 오늘이 2025-12-22이므로 2025-01은 모두 확정분
        info = get_monthly_holiday_pay_info(self.employee, 2025, 1)
        # 1월은 1일(수)부터 시작. 
        # 주의 시작일 기준이면 12/30(월)~1/5(일) 포함될 수 있음.
        # 내 로직은 주의 시작일 또는 종료일이 해당 월에 포함되면 리스트에 넣음.
        
        # 주휴수당 발생한 주가 2개 이상이어야 함
        eligible_weeks = [w for w in info['weeks'] if w['is_eligible']]
        self.assertGreaterEqual(len(eligible_weeks), 2)
        self.assertEqual(info['confirmed_total'], len(eligible_weeks) * 40000)
