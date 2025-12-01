# consultations/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from openai import OpenAI

from labor.models import Employee, CalculationResult
from .models import Consultation
from .serializers import ConsultationSerializer

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def build_context_summary(employee, calc_result):
    # Employee + CalculationResult를 요약해서 한글 문자열로 만드는 간단 버전
    if not employee:
        return "근로정보(알바 정보)가 선택되지 않았습니다."

    lines = [
        f"- 사업장 이름: {employee.workplace_name}",
        f"- 고용형태: {employee.employment_type}",
        f"- 시급: {employee.hourly_rate}원",
        f"- 주당 소정근로시간: {employee.weekly_hours}시간",
        f"- 1일 소정근로시간: {employee.daily_hours}시간",
        f"- 주휴수당 지급 여부: {'예' if employee.has_paid_weekly_holiday else '아니오'}",
    ]

    if calc_result:
        lines.append(f"- 대상 기간: {calc_result.period_start} ~ {calc_result.period_end}")
        if calc_result.expected_total_pay is not None:
            lines.append(f"- 해당 기간 예상 총임금: {calc_result.expected_total_pay}원")
        if calc_result.remaining_annual_leave is not None:
            lines.append(f"- 남은 연차: {calc_result.remaining_annual_leave}일")

    return "\n".join(lines)


class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], url_path="ai-consult")
    def ai_consult(self, request):
        """
        POST /api/consultations/ai-consult/
        {
          "employee_id": 1,   // 선택사항
          "title": "주휴수당 관련 문의",
          "content": "저는 주 20시간 일하는데...",
          "category": "임금체불"
        }
        """
        user = request.user
        employee_id = request.data.get("employee_id")
        title = request.data.get("title") or "AI 노동 상담"
        content = request.data.get("content")
        category = request.data.get("category", "")

        if not content:
            return Response({"detail": "content는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        employee = None
        if employee_id:
            try:
                employee = Employee.objects.get(id=employee_id, user=user)
            except Employee.DoesNotExist:
                return Response({"detail": "해당 employee를 찾을 수 없습니다."},
                                status=status.HTTP_400_BAD_REQUEST)

        # 해당 알바의 최신 CalculationResult 하나 (있다면)
        calc_result = None
        if employee:
            calc_result = (
                CalculationResult.objects.filter(employee=employee)
                .order_by("-calculated_at")
                .first()
            )

        context_summary = build_context_summary(employee, calc_result)

        system_prompt = """
너는 대한민국 노동법, 특히 아르바이트·단시간근로자 권리 보호에 초점을 둔
AI 상담 도우미야.

규칙:
- 사용자의 상황과 아래 제공되는 근로 정보, 계산 결과를 바탕으로
  '이론상 인정될 수 있는 권리'와 '확인해야 할 포인트'를 설명해줘.
- 모호한 부분은 '이럴 가능성이 크다' 수준으로만 표현하고,
  최종 판단은 공인노무사·변호사 상담이 필요하다고 알려줘.
- 복잡한 법조문을 그대로 나열하기보다는, 쉬운 한국어로 요약해서 설명해줘.
- 대한민국 법 기준으로만 답변해.
"""

        user_prompt = f"""
[근로자 및 근로조건 정보]
{context_summary}

[사용자 질문]
{content}

위 정보를 바탕으로:

1) 사용자가 놓치고 있을 수 있는 권리 (연차, 주휴수당, 최저임금, 수습, 해고 등)
2) 지금 상황에서 확인해야 할 핵심 포인트 (근로계약서, 급여명세서, 출퇴근기록 등)
3) 노동청이나 공인노무사에게 상담할 때 가져가면 좋은 자료
4) 조심해야 할 점 (감정적 대응, 증거 삭제 등)

을 단계별로, 쉬운 말로 정리해줘.
"""

        if not settings.OPENAI_API_KEY:
            return Response({"detail": "OPENAI_API_KEY가 설정되지 않았습니다."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # GPT-5-nano 호출
        resp = client.responses.create(
            model="gpt-5-nano",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        # 출력에서 텍스트만 추출 (responses API 포맷 기준)
        ai_text = resp.output[0].content[0].text

        consultation = Consultation.objects.create(
            user=user,
            employee=employee,
            title=title,
            content=content,
            category=category,
            status="AI분석완료",
            ai_result_json={"answer": ai_text},
            related_result=calc_result,
        )

        return Response(
            {
                "consultation_id": consultation.id,
                "answer": ai_text,
            },
            status=status.HTTP_201_CREATED,
        )
