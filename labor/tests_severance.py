from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta, time, datetime
from decimal import Decimal
from .models import Employee, WorkRecord, WorkSchedule
from .services import calculate_severance_v2

User = get_user_model()

class SeveranceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.get_or_create(username='testuser')[0]
        self.employee = Employee.objects.create(
            user=self.user,
            workplace_name='Test Shop',
            hourly_rate=Decimal('10000'),
            start_date=date.today() - timedelta(days=400), # 1년 이상
            contract_weekly_hours=20,
            is_workplace_over_5=True
        )

    def test_ineligible_under_1y(self):
        """재직 1년 미만 시 부적격 및 금액 0원 확인"""
        self.employee.start_date = date.today() - timedelta(days=300)
        self.employee.save()
        
        res = calculate_severance_v2(self.employee)
        self.assertFalse(res['eligible'])
        self.assertEqual(res['reason'], 'service_period_under_1y')
        self.assertEqual(res['severance_pay'], 0)

    def test_ineligible_under_15h(self):
        """주 15시간 미만 시 부적격 및 금액 0원 확인"""
        self.employee.contract_weekly_hours = 12
        self.employee.save()
        
        res = calculate_severance_v2(self.employee)
        self.assertFalse(res['eligible'])
        self.assertEqual(res['reason'], 'hours_under_15')
        self.assertEqual(res['severance_pay'], 0)

    def test_fallback_contract_estimate(self):
        """근로기록 없을 때 계약시간 기반 추정(CONTRACT_ESTIMATE) 확인"""
        res = calculate_severance_v2(self.employee)
        self.assertTrue(res['eligible'])
        self.assertEqual(res['method'], 'CONTRACT_ESTIMATE')
        
        # 평균임금(일급) = (20 / 7) * 10000 = 28571.4... -> 28571
        self.assertEqual(res['avg_daily_wage'], 28571)
        
        # 퇴직금 = 28571 * 30 * (400 / 365) = 939320.5... -> 939320
        # (서비스 일수에 따라 달라질 수 있음)
        self.assertGreater(res['severance_pay'], 900000)

    def test_rolling_90d_actual(self):
        """최근 90일 근로기록 있을 때 실제 임금 기반 산정 확인"""
        # 최근 90일간 매일 4시간씩 근무 (주말 제외 등 단순화 위해 매일 생성)
        today = date.today()
        for i in range(1, 91):
            d = today - timedelta(days=i)
            WorkRecord.objects.create(
                employee=self.employee,
                work_date=d,
                attendance_status='REGULAR_WORK',
                time_in=datetime.combine(d, time(9, 0)),
                time_out=datetime.combine(d, time(13, 0)) # 4시간
            )
            
        res = calculate_weekly_holiday_pay_v2 = None # mock check unnecessary here as it's imported in service
        
        res = calculate_severance_v2(self.employee)
        self.assertTrue(res['eligible'])
        self.assertEqual(res['method'], 'ROLLING_90D_ACTUAL')
        
        # 90일간 매일 4시간 = 360시간 * 10000 = 3,600,000원
        # 여기에 주휴수당도 포함됨 (90일은 약 12.8주)
        # 대략적인 금액 확인
        self.assertGreater(res['total_wage_last_90d'], 3600000)
        self.assertGreater(res['avg_daily_wage'], 40000)
