import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from django.conf import settings
from labor.models import Employee, CalculationResult
from langchain_core.tools import tool

# 1. Define Tools
@tool
def fetch_my_employees_tool(user_id: int) -> str:
    """
    사용자의 모든 알바(Employee) 등록 정보(시급, 근무시간, 주휴수당 여부 등)를 조회합니다.
    급여 계산이나 근로 조건에 대한 질문이 들어왔을 때 반드시 이 도구를 먼저 사용해서 정보를 확인해야 합니다.
    """
    try:
        employees = Employee.objects.filter(user_id=user_id)
        if not employees.exists():
            return "등록된 알바(Employee) 정보가 없습니다."
        
        results = []
        for emp in employees:
            info = (
                f"[ID: {emp.id}] {emp.workplace_name}\n"
                f"- 시급: {emp.hourly_rate}원\n"
                f"- 주당 근로시간: {emp.weekly_hours}시간\n"
                f"- 일일 근로시간: {emp.daily_hours}시간\n"
                f"- 고용형태: {emp.employment_type}\n"
                f"- 주휴수당 대상: {'대상' if emp.has_paid_weekly_holiday else '비대상'}"
            )
            results.append(info)
        
        return "\n\n".join(results)
    except Exception as e:
        return f"Error fetching employees: {str(e)}"

@tool
def fetch_recent_calculations_tool(user_id: int) -> str:
    """
    사용자의 최근 급여 계산 결과(CalculationResult)를 조회합니다.
    '이번 달 월급 얼마야?', '주휴수당 왜 빠졌어?' 같은 질문 시 과거 계산 기록을 확인하기 위해 사용합니다.
    """
    try:
        # 사용자의 모든 Employee에 연결된 계산 결과를 최신순으로 가져옴
        calcs = CalculationResult.objects.filter(employee__user_id=user_id).order_by('-calculated_at')[:5]
        
        if not calcs.exists():
            return "최근 계산된 급여 내역이 없습니다."

        results = []
        for c in calcs:
            emp_name = c.employee.workplace_name if c.employee else "삭제된 알바"
            info = (
                f"[계산일: {c.calculated_at.strftime('%Y-%m-%d')}] 사업장: {emp_name}\n"
                f"- 기간: {c.period_start} ~ {c.period_end}\n"
                f"- 예상 총임금: {c.expected_total_pay}원\n"
                f"- 연차 잔여: {c.remaining_annual_leave}일"
            )
            results.append(info)
        
        return "\n\n".join(results)
    except Exception as e:
        return f"Error fetching calculations: {str(e)}"

# 2. Configure Manual Agent Executor
class ManualAgentExecutor:
    def __init__(self, model, tools, system_prompt):
        self.model = model.bind_tools(tools)
        self.tools = {t.name: t for t in tools}
        self.system_prompt = system_prompt

    def invoke(self, inputs: dict) -> dict:
        """
        Mimics AgentExecutor.invoke
        inputs: {"input": "user question..."}
        returns: {"output": "ai response..."}
        """
        user_input = inputs.get("input", "")
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_input)
        ]
        
        # Max turns to prevent infinite loops
        max_turns = 5
        final_answer = ""
        
        for _ in range(max_turns):
            # 1. Call Model
            ai_msg = self.model.invoke(messages)
            messages.append(ai_msg)
            
            # 2. Check for Tool Calls
            if not ai_msg.tool_calls:
                final_answer = ai_msg.content
                break
            
            # 3. Execute Tools
            for tool_call in ai_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_obj = self.tools.get(tool_name)
                
                if tool_obj:
                    # Execute tool
                    try:
                        tool_output = tool_obj.invoke(tool_args)
                    except Exception as e:
                        tool_output = f"Error executing tool {tool_name}: {str(e)}"
                    
                    # Create ToolMessage
                    messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
                else:
                    messages.append(ToolMessage(content=f"Tool {tool_name} not found", tool_call_id=tool_call["id"]))
        
        return {"output": final_answer}

def get_consultation_agent():
    # GMS 프록시 엔드포인트를 통한 OpenAI 호출을 지원
    # 예: https://gms.ssafy.io/gmsapi/api.openai.com/v1/responses
    gms_openai_base = os.getenv("GMS_OPENAI_BASE_URL", "").strip() or None

    # 모델 설정 (기본 gpt-4o, 필요 시 gpt-4.1로 교체 가능)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
        base_url=gms_openai_base,  # None이면 기본 OpenAI 엔드포인트 사용
    )
    
    tools = [fetch_my_employees_tool, fetch_recent_calculations_tool]
    
    # 시스템 프롬프트
    system_prompt = """
    당신은 '노동법 진단 서비스'의 숙련된 AI 노무 상담사입니다.
    
    [행동 지침]
    1. 사용자의 질문에 답하기 위해 필요한 정보가 있다면, 반드시 제공된 도구(Tools)를 사용해 데이터를 조회하세요.
       - user_id는 입력 문장에 포함되어 있습니다. (예: Current User ID is 1)
       - 도구 호출 시 user_id 인자를 올바르게 파싱해서 전달하세요.
    2. 조회된 정보를 바탕으로 **팩트에 기반한** 답변을 제공하세요.
    3. 법률적 조언은 신중하게 하되, 명확한 근로기준법 위반 소지가 있다면 이를 지적해주세요.
    4. 사용자가 구체적인 상황을 말하지 않았다면, 먼저 도구로 정보를 확인하거나 되물어보세요.
    5. 답변은 친절하고 전문적인 말투(해요체)로 작성하세요.
    """
    
    return ManualAgentExecutor(llm, tools, system_prompt)
