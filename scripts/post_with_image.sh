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

# Убираем привязку к времени суток - просто тема
echo "$(date): 🤖 Генерируем пост с картинкой: $TOPIC"

RESPONSE=$(curl -s -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: openclaw_secret_key_2025" \
  -d "{\"topic\": \"$TOPIC\", \"generate_image\": false}")

TEXT=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('text', ''))" 2>/dev/null)

if [ -z "$TEXT" ]; then
    echo "$(date): ❌ Ошибка" >> /var/www/apps/post-generator/errors.log
    exit 1
fi

echo "$(date): ✅ Текст готов"

# Стили и художники для разнообразия
STYLES=(
    "digital art" "photorealistic" "cinematic" "abstract"
    "cyberpunk" "minimalist" "vibrant colors" "dark moody"
    "bright colorful" "sketch style" "watercolor"
)

ARTISTS=(
    "in style of studio ghibli" "in style of cyberpunk 2077"
    "in style of futuristic concept art" "in style of sci-fi movie poster"
    "in style of artstation trending" "in style of realistic"
)

RANDOM_STYLE=${STYLES[$RANDOM % ${#STYLES[@]}]}
RANDOM_ARTIST=${ARTISTS[$RANDOM % ${#ARTISTS[@]}]}
UNIQUE_SEED=$((RANDOM % 10000))

PROMPT="${TOPIC}, ${RANDOM_STYLE}, ${RANDOM_ARTIST}, high quality, 4k, detailed"
ENCODED=$(printf '%s' "$PROMPT" | python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read()))")
IMAGE_URL="https://image.pollinations.ai/prompt/${ENCODED}?width=1024&height=1024&seed=${UNIQUE_SEED}"

echo "🎨 Генерируем: ${RANDOM_STYLE} | ${RANDOM_ARTIST} | seed: ${UNIQUE_SEED}"

MAX_RETRIES=3
RETRY_DELAY=10
IMAGE_DOWNLOADED=""

for attempt in $(seq 1 $MAX_RETRIES); do
    echo "  Попытка $attempt загрузить изображение..."
    curl -s --max-time 90 "$IMAGE_URL" -o /tmp/img.jpg
    FILE_SIZE=$(stat -c%s /tmp/img.jpg 2>/dev/null || echo "0")
    
    if [ "$FILE_SIZE" -gt 10000 ]; then
        echo "  ✅ Изображение загружено ($FILE_SIZE байт)"
        IMAGE_DOWNLOADED="yes"
        break
    else
        echo "  ⚠️ Не загрузилось (размер: $FILE_SIZE), повтор через ${RETRY_DELAY} сек..."
        rm -f /tmp/img.jpg
        sleep $RETRY_DELAY
    fi
done

if [ "$IMAGE_DOWNLOADED" = "yes" ] && [ -f /tmp/img.jpg ] && [ $(stat -c%s /tmp/img.jpg 2>/dev/null || echo "0") -gt 10000 ]; then
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendPhoto" \
        -F "chat_id=$CHANNEL_ID" \
        -F "photo=@/tmp/img.jpg" \
        -F "caption=$TEXT" > /dev/null
    echo "$(date): ✅ Пост с картинкой опубликован (стиль: ${RANDOM_STYLE})" >> /var/www/apps/post-generator/posts.log
    echo "✅ Готово! Картинка в стиле: ${RANDOM_STYLE}"
else
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d "chat_id=$CHANNEL_ID" \
        -d "text=$TEXT" > /dev/null
    echo "$(date): ⚠️ Текст опубликован (картинка не загрузилась)" >> /var/www/apps/post-generator/posts.log
fi

echo "=== $(date) ===" >> /var/www/apps/post-generator/posts.log
echo "Тема: $TOPIC" >> /var/www/apps/post-generator/posts.log
echo "$TEXT" >> /var/www/apps/post-generator/posts.log
echo "---" >> /var/www/apps/post-generator/posts.log

rm -f /tmp/img.jpg
