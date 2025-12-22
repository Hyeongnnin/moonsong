from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import Employee, WorkRecord
from .services import calculate_annual_leave_v2

User = get_user_model()

class AnnualLeaveSimpleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.employee = Employee.objects.create(
            user=self.user,
            workplace_name='Test Shop',
            is_workplace_over_5=True,
            start_date=date.today() - timedelta(days=400), # 1년 이상
            hourly_rate=10000,
            contract_weekly_hours=20
        )

    def test_ineligible_under_5(self):
        """5인 미만 사업장 자격 미달 확인"""
        self.employee.is_workplace_over_5 = False
        self.employee.save()
        
        res = calculate_annual_leave_v2(self.employee, date.today().year)
        self.assertFalse(res['eligible'])
        self.assertIn("5인 미만", res['reason'])

    def test_ineligible_under_15h(self):
        """주 15시간 미만 자격 미달 확인"""
        self.employee.contract_weekly_hours = 10
        self.employee.save()
        
        res = calculate_annual_leave_v2(self.employee, date.today().year)
        self.assertFalse(res['eligible'])
        self.assertIn("15시간 미만", res['reason'])

    def test_accrued_over_1y(self):
        """1년 이상자 15일 고정 발생 확인"""
        # setUp에서 400일 전 입사로 설정됨
        res = calculate_annual_leave_v2(self.employee, date.today().year)
        self.assertTrue(res['eligible'])
        self.assertEqual(res['accrued_days'], 15.0)

    def test_accrued_under_1y_no_absent(self):
        """1년 미만자 결근 없을 때 월 1회 발생 확인"""
        # 오늘 기준 4개월 전 입사
        self.employee.start_date = date.today() - timedelta(days=125)
        self.employee.save()
        
        # 125일이면 약 4개월 (0~3개월차 종료, 4개월차 진행중)
        # i=0 (30d), i=1 (60d), i=2 (90d), i=3 (120d). i=4 (150d > today)
        # 내 로직: for i in range(11): if m_start > today: break ... 
        # m_start: 0, 30, 60, 90, 120 (5번)
        res = calculate_annual_leave_v2(self.employee, date.today().year)
        self.assertTrue(res['eligible'])
        # 0~120일차까지 5번의 루프 (0, 30, 60, 90, 120) 가 오늘(125)보다 작거나 같으므로 5일
        self.assertEqual(res['accrued_days'], 5.0)

    def test_accrued_under_1y_with_absent(self):
        """1년 미만자 결근 있을 때 발생 제외 확인"""
        # 100일 전 입사 (0, 30, 60, 90 -> 4일 발생 예상)
        self.employee.start_date = date.today() - timedelta(days=100)
        self.employee.save()
        
        # 45일째(1개월차 기간 내)에 결근 기록 추가
        absent_date = self.employee.start_date + timedelta(days=45)
        # 결근이 소정근로일이어야 깎임
        # 여기서는 단순화를 위해 모든 날이 소정근로일인 상황으로 테스트하려면? 
        # calculate_annual_leave_v2 내에서 is_scheduled_workday를 체크하므로 스케줄 필요
        from .models import WorkSchedule
        WorkSchedule.objects.create(employee=self.employee, weekday=absent_date.weekday(), start_time='09:00', end_time='18:00', enabled=True)
        
        WorkRecord.objects.create(employee=self.employee, work_date=absent_date, attendance_status='ABSENT')
        
        res = calculate_annual_leave_v2(self.employee, date.today().year)
        # 0, 30, 60, 90 중 30~59 구간에 결근이 있으므로 1일 차감되어 3일 예상
        self.assertEqual(res['accrued_days'], 3.0)

    def test_used_days(self):
        """사용 연차(ANNUAL_LEAVE) 집계 확인"""
        today = date.today()
        # 올해 연차 사용 2건
        WorkRecord.objects.create(employee=self.employee, work_date=today - timedelta(days=5), attendance_status='ANNUAL_LEAVE')
        WorkRecord.objects.create(employee=self.employee, work_date=today - timedelta(days=10), attendance_status='ANNUAL_LEAVE')
        
        res = calculate_annual_leave_v2(self.employee, today.year)
        self.assertEqual(res['used_days'], 2.0)
        self.assertEqual(res['remaining_days'], 13.0) # 15 - 2
