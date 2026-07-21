"""
Модуль генерации постов - OpenRouter (только рабочие бесплатные модели)
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/app/.env")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")

# Только проверенные рабочие бесплатные модели
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-2.5-pro-exp-03-25:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.2-3b-instruct:free"
]

def generate_post(topic, tone, length, language_code, include_hashtags):
    if not OPENROUTER_KEY:
        return "❌ API ключ не настроен"

    length_map = {
        "short": "300-500",
        "medium": "500-800",
        "long": "800-1200"
    }

    lang_names = {
        "ru": "Русский",
        "en": "English",
        "kk": "Қазақша",
        "uk": "Українська"
    }

    prompt = f"""Напиши пост для Telegram-канала на тему: "{topic}"

Тональность: {tone}
Длина: {length_map.get(length, '500-800')} символов
Язык: {lang_names.get(language_code, 'Русский')}

Требования:
- Используй эмодзи (2-4 штуки)
- Разбей на 2-3 абзаца
- В конце задай вопрос аудитории
{"- Добавь 3-5 хештегов в конце" if include_hashtags else ""}

Сразу пиши готовый пост, без пояснений:"""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    
    last_error = None
    for model in FREE_MODELS:
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты профессиональный копирайтер для Telegram-каналов."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 800
        }

        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            result = response.json()
            
            if response.status_code == 200:
                return result['choices'][0]['message']['content'].strip()
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                last_error = f"{model}: {error_msg}"
                continue
                
        except Exception as e:
            last_error = f"{model}: {str(e)}"
            continue
    
    return f"❌ Все модели недоступны. Последняя ошибка: {last_error}"

def generate_image(prompt, style="Реалистичный", detail="Средняя", extra_details=""):
    return None

def factcheck_post(post_text):
    return {"has_errors": False, "errors": [], "corrections": []}

def humanize_text(post_text, style="natural"):
    return post_text

def detect_ai_artifacts(post_text):
    return []
