# consultations/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

# 모델
from labor.models import Employee, CalculationResult
from .models import Consultation
from .serializers import ConsultationSerializer

# AI Agent
from .ai_agent import get_consultation_agent

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
          "title": "급여 문의",
          "content": "이번 달 제 월급 계산이 맞는 건가요?", 
          "category": "급여"
        }
        """
        user = request.user
        title = request.data.get("title") or "AI 노동 상담"
        content = request.data.get("content")
        category = request.data.get("category", "")

        if not content:
            return Response({"detail": "content는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.OPENAI_API_KEY:
             return Response({"detail": "OPENAI_API_KEY가 설정되지 않았습니다."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 1. Agent 생성
        try:
            agent_executor = get_consultation_agent()
        except Exception as e:
            return Response({"detail": f"Agent 생성 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Agent 실행
        # input에 user_id를 힌트로 같이 주어 Tool이 사용할 수 있게 유도하거나, 
        # Tool 함수 호출 시 user_id를 주입하는 방법이 있음.
        # 여기서는 질문 텍스트(input) 내에 메타데이터를 포함시키기보다, 
        # Agent가 Tool을 호출할 때 user_id를 인자로 넘기도록 유도하기 위해 
        # 시스템 프롬프트나 input에 명시적으로 user_id 정보를 주입함.
        
        # 더 나은 방법: 도구 실행 시 user_id를 바인딩하는 것이지만, 
        # 간단 구현을 위해 "Current User ID is {user.id}"를 질문 앞에 붙여줌.
        augmented_input = f"Current User ID is {user.id}.\nUser Question: {content}"
        
        try:
            result = agent_executor.invoke({"input": augmented_input})
            ai_text = result["output"]
        except Exception as e:
             return Response({"detail": f"AI 응답 생성 실패: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. 결과 저장
        consultation = Consultation.objects.create(
            user=user,
            title=title,
            content=content,
            category=category,
            status="AI분석완료",
            ai_result_json={"answer": ai_text},
            # related_result는 필요하다면 Agent가 찾은 정보를 바탕으로 연결할 수도 있으나 지금은 생략
        )

        return Response(
            {
                "consultation_id": consultation.id,
                "answer": ai_text,
            },
            status=status.HTTP_201_CREATED,
        )
