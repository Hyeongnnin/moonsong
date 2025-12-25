import json
import os
from datetime import date
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from django.conf import settings
from labor.models import Employee, CalculationResult
from labor.services import (
    compute_payroll_summary, 
    calculate_severance_v2, 
    evaluate_labor, 
    job_to_inputs
)

# 1. Define Tools
@tool
def fetch_my_employees_tool(user_id: int) -> str:
    """
    [내 정보 조회] 사용자의 모든 알바(Employee) 등록 정보(시급, 근무시간 등)를 조회합니다.
    사용자가 본인의 근로 조건에 대해 물어보거나, 급여 계산 전 기준 정보를 확인할 때 사용하세요.
    """
    try:
        employees = Employee.objects.filter(user_id=user_id)
        if not employees.exists():
            return "등록된 알바(Employee) 정보가 없습니다."
        
        results = []
        for emp in employees:
            hours = emp.contract_weekly_hours or 0
            is_eligible = "대상 (주 15시간 이상)" if hours >= 15 else "비대상 (주 15시간 미만)"
            
            info = (
                f"[ID: {emp.id}] {emp.workplace_name}\n"
                f"- 시급: {emp.hourly_rate}원\n"
                f"- 계약상 주 근로시간: {hours}시간\n"
                f"- 고용형태: {emp.employment_type}\n"
                f"- 주휴수당: {is_eligible}"
            )
            results.append(info)
        
        return "\n\n".join(results)
    except Exception as e:
        return f"Error fetching employees: {str(e)}"

@tool
def fetch_recent_calculations_tool(user_id: int) -> str:
    """
    [과거 내역 조회] 사용자의 최근 급여 계산 및 명세서 내역을 조회합니다.
    '저번 달 월급 얼마였어?', '과거 급여 내역 보여줘' 등의 질문에 사용하세요.
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
def calculate_monthly_salary_tool(user_id: int, target_month: int = 0) -> str:
    """
    [월급 계산] 사용자의 월별 예상 급여를 실시간으로 계산합니다.
    '이번 달 얼마 벌었어?' -> target_month=0
    '6월 급여 계산해줘' -> target_month=6
    """
    try:
        employees = Employee.objects.filter(user_id=user_id)
        if not employees.exists():
            return "등록된 알바(Employee) 정보가 없습니다."

        today = date.today()
        year = today.year
        month = today.month
        
        if target_month and 1 <= target_month <= 12:
            month = target_month
        
        results = []
        
        for emp in employees:
            # 급여 계산
            payroll = compute_payroll_summary(emp, year, month)
            
            # 예상 수령액 (세후 우선, 없으면 세전)
            net_pay = payroll.get('net_pay', 0)
            if not net_pay:
                net_pay = payroll.get('estimated_monthly_pay', 0)
                
            info = (
                f"[{emp.workplace_name}] {month}월 급여 상세\n"
                f"- 예상 수령액: {int(net_pay):,}원\n"
                f"- 총 근무시간: {payroll['total_hours']}시간\n"
                f"- 주휴수당: {int(payroll['monthly_weekly_holiday_pay']):,}원\n"
                f"- 야간수당: {int(payroll['night_bonus']):,}원\n"
                f"- 휴일수당: {int(payroll['holiday_bonus']):,}원"
            )
            results.append(info)
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error calculating monthly salary: {str(e)}"

@tool
def calculate_severance_pay_tool(user_id: int) -> str:
    """
    [퇴직금 계산] 사용자의 '퇴직금 예상액'을 실시간으로 계산합니다.
    '지금 그만두면 퇴직금 나와?', '퇴직금 얼마야?' 등의 질문에 사용하세요.
    """
    try:
        employees = Employee.objects.filter(user_id=user_id)
        if not employees.exists():
            return "등록된 알바(Employee) 정보가 없습니다."

        results = []
        for emp in employees:
            # 퇴직금 예상액
            severance = calculate_severance_v2(emp)
            
            severance_msg = "해당 없음 (1년 미만 또는 시간 부족)"
            if severance['eligible']:
                severance_msg = f"{severance['severance_pay']:,}원 (예상)"
            elif severance['reason'] == 'service_period_under_1y':
                severance_msg = "해당 없음 (재직 1년 미만)"
            elif severance['reason'] == 'hours_under_15':
                severance_msg = "해당 없음 (주 15시간 미만)"
            
            info = (
                f"[{emp.workplace_name}] 퇴직금 분석\n"
                f"- 예상액: {severance_msg}\n"
                f"- 산정 기준: 평균임금 {severance.get('avg_daily_wage', 0):,}원"
            )
            results.append(info)
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error calculating severance pay: {str(e)}"

@tool
def diagnose_labor_law_tool(user_id: int) -> str:
    """
    [법률 진단] 사용자의 근로 조건이 근로기준법을 준수하는지 진단합니다.
    '최저임금 위반이야?', '주휴수당 받을 수 있어?', '사장님이 법을 어기나요?' 등의 질문에 사용하세요.
    """
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
        if "deus ex machina" in inputs.get("input", ""):
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
    gms_openai_base = os.getenv("GMS_OPENAI_BASE_URL", "").strip() or None

    # 모델 설정 (기본 gpt-4o, 필요 시 gpt-4.1로 교체 가능)
    llm = ChatOpenAI(
        model="gpt-4.1-nano",
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
        base_url=gms_openai_base,
    )
    
    # [Updated] Tools list with split calculation tools
    tools = [
        fetch_my_employees_tool, 
        fetch_recent_calculations_tool, 
        calculate_monthly_salary_tool, 
        calculate_severance_pay_tool,
        diagnose_labor_law_tool
    ]
    
    # [Updated] System Prompt with split tools mapping
    system_prompt = """
    당신은 '노동법 진단 서비스'의 전문 AI 노무 상담사입니다.
    사용자의 질문을 분석하여 정확한 근로 데이터에 기반한 법률/급여 상담을 제공하세요.

    [핵심 원칙]
    1. **데이터 기반**: 추측하지 말고 반드시 도구(Tool)를 사용해 DB 데이터를 조회한 후 답변하세요.
    2. **법률 준수**: 2025년 최저임금(10,030원) 및 근로기준법을 기준으로 진단하세요.
    3. **명확성**: 핵심 결론을 먼저 말하고, 상세 근거를 설명하세요.
    4. **친절함**: 전문적이지만 이해하기 쉬운 '해요체'를 사용하세요.

    [도구 사용 가이드]
    - 유저 ID 파싱: 질문 시작 부분의 "Current User ID is {id}"에서 ID를 추출하여 도구 인자에 사용하세요.
    - **내 정보 조회**: 시급, 근로시간 등 계약 정보 확인 -> `fetch_my_employees_tool`
    - **월급(급여) 계산**: 
        - "이번 달 얼마 벌었어?" -> `calculate_monthly_salary_tool(user_id)`
        - "6월 급여 계산해줘" -> `calculate_monthly_salary_tool(user_id, target_month=6)`
    - **퇴직금 계산**: "퇴직금 받을 수 있어?", "그만두면 얼마 받아?" (월급 제외) -> `calculate_severance_pay_tool`
    - **법률 진단**: "최저임금 위반이야?", "주휴수당 받을 수 있어?", "근로계약서 안썼는데?" -> `diagnose_labor_law_tool`
    - **과거 내역**: "저번 달 월급 명세서 줘", "옛날 급여 내역" -> `fetch_recent_calculations_tool`

    [답변 형식]
    (결론) 
    (상세 설명)
    (필요한 경우 법적 근거 또는 조언)
    """
    
    return ManualAgentExecutor(llm, tools, system_prompt)
