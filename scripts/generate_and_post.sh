#!/bin/bash

cd /var/www/apps/post-generator

BOT_TOKEN="8505446866:AAEhIzNad0WiME1rmgpBvNnA_w8EVnd_dbo"
CHANNEL_ID="-1003957026845"

THEMES=(
    "Нейросети: новые архитектуры и модели 2026"
    "Искусственный интеллект в медицине: прорывы года"
    "AI в бизнесе: автоматизация и оптимизация"
    "Генеративные нейросети: как они работают"
    "Этика искусственного интеллекта: вызовы и решения"
    "Нейроинтерфейсы: будущее взаимодействия человека и AI"
    "Робототехника и машинное обучение: тренды"
    "ИИ в образовании: персонализация обучения"
)

HOURS_SINCE_EPOCH=$(($(date +%s) / 3600))
INDEX=$((HOURS_SINCE_EPOCH % ${#THEMES[@]}))
TOPIC="${THEMES[$INDEX]}"

# Убираем привязку к времени суток - просто тема без утреннего/дневного/вечернего
echo "$(date): 🤖 Генерируем пост на тему: $TOPIC"

RESPONSE=$(curl -s -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: openclaw_secret_key_2025" \
  -d "{\"topic\": \"$TOPIC\", \"generate_image\": false}")

TEXT=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('text', ''))" 2>/dev/null)

if [ -n "$TEXT" ]; then
    echo "$(date): ✅ Пост сгенерирован"

    echo "=== $(date) ===" >> /var/www/apps/post-generator/posts.log
    echo "Тема: $TOPIC" >> /var/www/apps/post-generator/posts.log
    echo "$TEXT" >> /var/www/apps/post-generator/posts.log
    echo "---" >> /var/www/apps/post-generator/posts.log

    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d "chat_id=$CHANNEL_ID" \
        -d "text=$TEXT" > /dev/null

    echo "$(date): ✅ Пост опубликован" >> /var/www/apps/post-generator/posts.log
    echo "✅ Готово!"
else
    echo "$(date): ❌ Ошибка генерации" >> /var/www/apps/post-generator/errors.log
fi
