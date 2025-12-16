import json
import os
from django.conf import settings

class PolicyManager:
    _policy_cache = None
    POLICY_PATH = os.path.join(settings.BASE_DIR, 'labor', 'policy', 'holiday_pay_policy.json')

    @classmethod
    def get_holiday_pay_rules(cls):
        """
        Loads and returns the holiday pay rules from the JSON policy file.
        """
        if cls._policy_cache is None:
            try:
                with open(cls.POLICY_PATH, 'r', encoding='utf-8') as f:
                    cls._policy_cache = json.load(f)
            except FileNotFoundError:
                # Fallback default if file is missing (failsafe)
                cls._policy_cache = {
                    "rules": {
                        "min_weekly_hours": 15,
                        "require_perfect_attendance": True,
                        "calculation_method": "daily_average",
                        "description_ko": "주 15시간 이상 근무 (기본값)"
                    }
                }
        return cls._policy_cache['rules']

    @classmethod
    def reload_policy(cls):
        """Force reload of the policy file (useful for hot-updates)"""
        cls._policy_cache = None
        return cls.get_holiday_pay_rules()
