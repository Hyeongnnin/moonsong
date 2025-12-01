# consultations/serializers.py
from rest_framework import serializers
from .models import Consultation

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = "__all__"
        read_only_fields = ["user", "consultation_date", "status", "ai_result_json"]
