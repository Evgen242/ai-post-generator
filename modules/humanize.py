"""
Модуль для "очеловечивания" AI-текста
Убирает шаблонные фразы и делает текст более естественным
"""
import openai
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/var/www/apps/post-generator/.env")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")

def humanize_text(text, style="natural"):
    """
    Преобразует AI-текст в более естественный, человеческий
    
    style:
    - "natural" - естественный разговорный
    - "professional" - профессиональный, но не шаблонный
    - "emotional" - более эмоциональный, живой
    """
    if not OPENROUTER_KEY:
        return text
    
    client = openai.OpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    
    style_prompts = {
        "natural": "Сделай текст более естественным, разговорным, убери шаблонные фразы. Добавь живые обороты, убери 'во-первых', 'кроме того', 'таким образом'. Сделай так, будто текст написал человек, а не нейросеть.",
        "professional": "Сохрани профессиональный тон, но убери шаблонные AI-фразы. Сделай текст более живым и естественным, сохраняя экспертность.",
        "emotional": "Сделай текст более эмоциональным, добавь восклицания, живые примеры. Убери сухие формулировки."
    }
    
    prompt = f"""{style_prompts.get(style, style_prompts["natural"])}

Оригинальный текст:
{text}

Перепиши текст, сделай его более человеческим, но сохрани смысл и ключевую информацию. Не добавляй новые факты. Просто перепиши более естественно:"""
    
    try:
        response = client.chat.completions.create(
            model="openrouter/google/gemini-2.0-flash-lite-preview-02-05:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,  # Чуть выше для разнообразия
            max_tokens=1200
        )
        humanized = response.choices[0].message.content
        if humanized and len(humanized.strip()) > 50:
            return humanized
        return text
    except Exception as e:
        print(f"Человезация не удалась: {e}")
        return text

def detect_ai_artifacts(text):
    """Определяет признаки AI-текста"""
    artifacts = []
    
    # Список шаблонных AI-фраз
    ai_phrases = [
        "во-первых", "во-вторых", "в-третьих",
        "кроме того", "более того", "следует отметить",
        "таким образом", "подводя итог", "в заключение",
        "несомненно", "безусловно", "очевидно",
        "стоит отметить", "важно подчеркнуть", "обратите внимание"
    ]
    
    for phrase in ai_phrases:
        if phrase.lower() in text.lower():
            artifacts.append(phrase)
    
    return artifacts
