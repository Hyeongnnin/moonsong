from openai import AsyncOpenAI
import os
import getpass
import asyncio

# GMS KEY를 입력하는 단계입니다. 실제 서비스에서는 환경변수나 KMS를 활용하세요!
if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("GMS KEY를 입력하세요: S14P02BB04-1ec57b82-502d-4b2c-9a98-a6927a9b7b00")

# 중요! OpenAI의 BASE_URL을 GMS로 설정합니다. 
client = AsyncOpenAI(base_url="https://gms.ssafy.io/gmsapi/api.openai.com/v1")

async def main():
    res_text = ""
    stream = await client.chat.completions.create(
        model='gpt-4.1',
        messages=[{"role": "system", "content": "당신은 Friday라는 이름의 긍정 에너지 가득한 AI입니다."}, {"role": "user", "content": "안녕! 오늘 기분 어때?"}],
        max_tokens=1024,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            res_text += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n\n---------\n전체 응답:\n", res_text)

if __name__ == "__main__":
    asyncio.run(main())
