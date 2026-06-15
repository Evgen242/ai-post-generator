"""
Модуль генерации постов
"""
import openai
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="/var/www/apps/post-generator/.env")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")

def generate_post(topic, tone, length, language_code, include_hashtags):
    if not OPENROUTER_KEY:
        raise Exception("API ключ не настроен. Проверьте .env файл")
    
    client = openai.OpenAI(
        api_key=OPENROUTER_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    
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
    
    # Используем openrouter/free - динамический выбор модели
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=800
        )
        post_text = response.choices[0].message.content
        if post_text and len(post_text.strip()) > 50:
            return post_text
        else:
            raise Exception("Пустой ответ")
    except Exception as e:
        raise Exception(f"Ошибка генерации: {e}. Попробуйте позже или пополните баланс OpenRouter")
