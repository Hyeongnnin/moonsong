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

@tool
def calculate_expected_pay_tool(user_id: int) -> str:
    """
    사용자의 '현재 시점까지의 예상 급여'와 '퇴직금 예상액'을 실시간으로 계산합니다.
    '오늘까지 일하면 얼마 받아?', '지금 그만두면 퇴직금 나와?' 같은 질문에 사용합니다.
    """
    from datetime import date
    from labor.services import compute_monthly_payroll, calculate_severance_v2
    
    try:
        employees = Employee.objects.filter(user_id=user_id)
        if not employees.exists():
            return "등록된 알바(Employee) 정보가 없습니다."

        today = date.today()
        results = []
        
        for emp in employees:
            # 1. 이번 달 급여 (이달 1일 ~ 오늘)
            # compute_monthly_payroll은 해당 월 전체 기록을 가져오므로, 오늘까지의 기록만 있으면 오늘까지로 계산됨
            payroll = compute_monthly_payroll(emp, today.year, today.month)
            
            # 2. 퇴직금 예상액
            severance = calculate_severance_v2(emp)
            
            severance_msg = "해당 없음 (1년 미만 또는 시간 부족)"
            if severance['eligible']:
                severance_msg = f"{severance['severance_pay']:,}원 (예상)"
            elif severance['reason'] == 'service_period_under_1y':
                severance_msg = "해당 없음 (재직 1년 미만)"
            
            info = (
                f"[{emp.workplace_name}]\n"
                f"- 이번 달 예상 급여 ({today.month}월): {payroll['estimated_salary']:,}원\n"
                f"  (총 {payroll['total_hours']}시간, {payroll['total_work_days']}일 근무)\n"
                f"- 퇴직금 예상액: {severance_msg}"
            )
            results.append(info)
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error calculating pay: {str(e)}"

@tool
def diagnose_labor_law_tool(user_id: int) -> str:
    """
    사용자의 근로 조건이 노동법을 위반하고 있는지 종합적으로 진단합니다.
    '최저임금 위반인가요?', '주휴수당 받을 수 있나요?', '사장님이 법을 어기고 있나요?' 같은 질문에 사용합니다.
    """
    from labor.services import evaluate_labor, job_to_inputs
    
    try:
        employees = Employee.objects.filter(user_id=user_id)
        if not employees.exists():
            return "진단할 알바(Employee) 정보가 없습니다."

        results = []
        for emp in employees:
            # 1. Employee -> JobInputs 변환
            inputs = job_to_inputs(emp)
            
            # 2. 노동법 위반 여부 진단
            eval_result = evaluate_labor(inputs)
            
            # 3. 결과 포맷팅
            warnings = eval_result.get('warnings', [])
            status_msg = "✅ 위반 사항 없음 (정상)"
            if warnings:
                 status_msg = "⚠️ " + ", ".join(warnings)
            
            min_wage_ok = "준수" if eval_result['min_wage']['min_wage_ok'] else "위반 (최저임금 미달)"
            weekly_holiday = "대상 아님"
            if inputs.weekly_hours and inputs.weekly_hours >= 15:
                weekly_holiday = "지급 대상 (주 15시간 이상)"
            
            info = (
                f"[{emp.workplace_name}] 진단 결과\n"
                f"- 최저임금: {min_wage_ok}\n"
                f"- 주휴수당: {weekly_holiday}\n"
                f"- 종합 판정: {status_msg}"
            )
            results.append(info)
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error diagnosing labor law: {str(e)}"

# Global Memory Storage
# {user_id: [message1, message2, ...]}
GLOBAL_MEMORY = {}

# 2. Configure Manual Agent Executor
class ManualAgentExecutor:
    def __init__(self, model, tools, system_prompt):
        self.model = model.bind_tools(tools)
        self.tools = {t.name: t for t in tools}
        self.system_prompt = system_prompt

    def invoke(self, inputs: dict) -> dict:
        """
        Mimics AgentExecutor.invoke
        inputs: {"input": "user question...", "user_id": 1}
        returns: {"output": "ai response..."}
        """
        user_input = inputs.get("input", "")
        user_id = inputs.get("user_id", None)
        
        current_system_prompt = self.system_prompt
        # [Developer Mode]
        if "deus ex machina" in user_input:
            current_system_prompt = "You are a helpful AI assistant. Answer the user's request freely."
            user_input = user_input.replace("deus ex machina", "").strip()

        # Load history or initialize
        messages = []
        if user_id is not None:
             if user_id in GLOBAL_MEMORY:
                 messages = GLOBAL_MEMORY[user_id]
             else:
                 messages = [SystemMessage(content=current_system_prompt)]
                 GLOBAL_MEMORY[user_id] = messages
        else:
             # Fallback for no user_id (stateless)
             messages = [SystemMessage(content=current_system_prompt)]

        # [Developer Mode] System Prompt Override in History
        # 만약 개발자 모드가 감지되면, 히스토리의 첫 번째 메시지(SystemMessage)를 강제로 업데이트
        if "deus ex machina" in inputs.get("input", ""): # 원본 입력 다시 체크
             if messages and isinstance(messages[0], SystemMessage):
                 messages[0] = SystemMessage(content=current_system_prompt)

        # Add User Message
        messages.append(HumanMessage(content=user_input))
        
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
        model="gpt-4.1-nano",
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
        base_url=gms_openai_base,  # None이면 기본 OpenAI 엔드포인트 사용
    )
    
    tools = [fetch_my_employees_tool, fetch_recent_calculations_tool, calculate_expected_pay_tool, diagnose_labor_law_tool]
    
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
