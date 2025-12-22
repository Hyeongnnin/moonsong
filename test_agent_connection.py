import os
import django
import dotenv
from langchain_core.messages import HumanMessage

dotenv.load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from consultations.ai_agent import get_consultation_agent

try:
    print("Initializing Agent...")
    agent = get_consultation_agent()
    print("Agent Initialized.")
    
    print(f"OPENAI_API_KEY Set: {bool(os.environ.get('OPENAI_API_KEY'))}")
    print(f"GMS_OPENAI_BASE_URL: {os.environ.get('GMS_OPENAI_BASE_URL')}")

    print("Invoking Agent with test query...")
    # Using a simple query that typically doesn't require tools to test basic LLM connectivity
    result = agent.invoke({"input": "Hello, are you ready?"})
    print(f"Result: {result}")

except Exception as e:
    print(f"Error: {e}")
