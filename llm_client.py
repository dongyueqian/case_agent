import time
import logging
from zhipuai import ZhipuAI
from config import API_KEY, MODEL_NAME, TEMPERATURE, TIMEOUT, MAX_RETRIES

client = ZhipuAI(api_key=API_KEY)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def llm_call(prompt: str, model=MODEL_NAME, temperature=TEMPERATURE) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                timeout=TIMEOUT,
                messages=[{"role": "user", "content": prompt}]
            )
            content = resp.choices[0].message.content.strip()
            content = content.replace("'", '"')
            content = content.strip().strip("```json").strip("```").strip()
            return content
        except Exception as e:
            logging.warning(f"LLM调用失败 尝试{attempt+1}/{MAX_RETRIES}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logging.error(f"LLM最终调用失败: {str(e)}")
                return None
            time.sleep(2)
    return None