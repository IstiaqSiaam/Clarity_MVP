# apps/nlp_service/nlp/worker/jobs.py
import os
import asyncio

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def analyze_text(text: str) -> dict:
    # Placeholder: later call your LLM / HF pipeline here
    return {"sentiment": "neutral", "themes": ["journal"], "summary": text[:140]}

def analyze_text_sync(text: str) -> dict:
    # RQ-friendly wrapper
    return asyncio.run(analyze_text(text))
