#!/bin/bash

cd /var/www/apps/post-generator

BOT_TOKEN="8505446866:AAEhIzNad0WiME1rmgpBvNnA_w8EVnd_dbo"
CHANNEL_ID="-1003957026845"

# === ТИПЫ КОНТЕНТА ===
CONTENT_TYPES=("quote" "meme" "comparison" "review" "case")
RANDOM_TYPE=${CONTENT_TYPES[$RANDOM % ${#CONTENT_TYPES[@]}]}

# === ЦИТАТЫ ДНЯ ===
generate_quote() {
    local TOPICS=(
        "искусственный интеллект и будущее"
        "нейросети и творчество"
        "AI и этика"
        "технологии и человек"
        "машинное обучение"
    )
    local RANDOM_TOPIC=${TOPICS[$RANDOM % ${#TOPICS[@]}]}
    
    RESPONSE=$(curl -s -X POST http://localhost:8001/api/generate \
        -H "Content-Type: application/json" \
        -H "X-API-Key: openclaw_secret_key_2025" \
        -d "{\"topic\": \"Сгенерируй короткую вдохновляющую цитату об $RANDOM_TOPIC (1-2 предложения)\", \"generate_image\": false}")
    
    QUOTE=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('text', ''))" 2>/dev/null)
    
    if [ -n "$QUOTE" ]; then
        TEXT="🌟 **Цитата дня об ИИ** 🌟\n\n$QUOTE\n\n---\n_Делитесь в комментариях своей любимой цитатой!_"
        generate_image "quote" "$QUOTE"
    fi
}

# === AI-МЕМЫ ===
generate_meme() {
    local MEME_TOPICS=(
        "нейросети ошибка мем"
        "AI заменит программиста мем"
        "чат гпт прикол"
        "искусственный интеллект юмор"
    )
    local RANDOM_MEME=${MEME_TOPICS[$RANDOM % ${#MEME_TOPICS[@]}]}
    
    TEXT="😂 **AI-Мем дня** 😂\n\n_Смеёмся вместе с нейросетями!_\n\n#AIмем #ИИюмор"
    generate_image "$RANDOM_MEME" "$TEXT"
}

# === СРАВНЕНИЯ ChatGPT vs Claude vs Gemini ===
generate_comparison() {
    local COMPARE_TOPICS=(
        "ChatGPT и Claude"
        "ChatGPT и Gemini"
        "Claude и Gemini"
        "ChatGPT, Claude и Gemini"
    )
    local RANDOM_COMPARE=${COMPARE_TOPICS[$RANDOM % ${#COMPARE_TOPICS[@]}]}
    
    RESPONSE=$(curl -s -X POST http://localhost:8001/api/generate \
        -H "Content-Type: application/json" \
        -H "X-API-Key: openclaw_secret_key_2025" \
        -d "{\"topic\": \"Сравни $RANDOM_COMPARE: сильные и слабые стороны, когда что лучше использовать\", \"generate_image\": false}")
    
    COMPARISON=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('text', ''))" 2>/dev/null)
    
    if [ -n "$COMPARISON" ]; then
        TEXT="⚖️ **Сравнение AI моделей** ⚖️\n\n$COMPARISON\n\n---\n_А какую модель используете вы?_"
        generate_image "comparison $RANDOM_COMPARE" "$TEXT"
    fi
}

# === ОБЗОРЫ НОВЫХ ИНСТРУМЕНТОВ ===
generate_review() {
    local TOOLS=(
        "новый AI инструмент для видео"
        "нейросеть для генерации музыки"
        "AI помощник для кода"
        "инструмент для дизайна на ИИ"
    )
    local RANDOM_TOOL=${TOOLS[$RANDOM % ${#TOOLS[@]}]}
    
    RESPONSE=$(curl -s -X POST http://localhost:8001/api/generate \
        -H "Content-Type: application/json" \
        -H "X-API-Key: openclaw_secret_key_2025" \
        -d "{\"topic\": \"Обзор $RANDOM_TOOL: возможности, плюсы, минусы, цена\", \"generate_image\": false}")
    
    REVIEW=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('text', ''))" 2>/dev/null)
    
    if [ -n "$REVIEW" ]; then
        TEXT="🔍 **Обзор AI инструмента** 🔍\n\n$REVIEW\n\n---\n_Пользовались таким? Делитесь опытом!_"
        generate_image "review $RANDOM_TOOL" "$TEXT"
    fi
}

# === КЕЙСЫ ИСПОЛЬЗОВАНИЯ AI ===
generate_case() {
    local CASES=(
        "AI в маркетинге кейс"
        "нейросети в логистике пример"
        "ИИ в ресторанном бизнесе"
        "автоматизация склада с AI"
        "чат-бот для клиентской поддержки"
    )
    local RANDOM_CASE=${CASES[$RANDOM % ${#CASES[@]}]}
    
    RESPONSE=$(curl -s -X POST http://localhost:8001/api/generate \
        -H "Content-Type: application/json" \
        -H "X-API-Key: openclaw_secret_key_2025" \
        -d "{\"topic\": \"Реальный кейс: $RANDOM_CASE. Описание проблемы, решение, результат\", \"generate_image\": false}")
    
    CASE=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('text', ''))" 2>/dev/null)
    
    if [ -n "$CASE" ]; then
        TEXT="📈 **Кейс использования AI** 📈\n\n$CASE\n\n---\n_Как вы используете ИИ в своей работе?_"
        generate_image "case $RANDOM_CASE" "$TEXT"
    fi
}

# === ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ ===
generate_image() {
    local PROMPT_TEXT="$1"
    local CAPTION="$2"
    
    local STYLES=("digital art" "illustration" "concept art" "creative")
    local RANDOM_STYLE=${STYLES[$RANDOM % ${#STYLES[@]}]}
    local UNIQUE_SEED=$((RANDOM % 10000))
    
    local FULL_PROMPT="${PROMPT_TEXT}, ${RANDOM_STYLE}, high quality, 4k"
    local ENCODED=$(printf '%s' "$FULL_PROMPT" | python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.stdin.read()))")
    local IMAGE_URL="https://image.pollinations.ai/prompt/${ENCODED}?width=1024&height=1024&seed=${UNIQUE_SEED}"
    
    echo "🎨 Генерируем изображение для: $RANDOM_TYPE"
    
    curl -s --max-time 60 "$IMAGE_URL" -o /tmp/special_img.jpg
    local FILE_SIZE=$(stat -c%s /tmp/special_img.jpg 2>/dev/null || echo "0")
    
    if [ "$FILE_SIZE" -gt 10000 ]; then
        curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendPhoto" \
            -F "chat_id=$CHANNEL_ID" \
            -F "photo=@/tmp/special_img.jpg" \
            -F "caption=$CAPTION" > /dev/null
        echo "$(date): ✅ Спецконтент ($RANDOM_TYPE) опубликован" >> /var/www/apps/post-generator/special.log
    else
        curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
            -d "chat_id=$CHANNEL_ID" \
            -d "text=$CAPTION" > /dev/null
        echo "$(date): ⚠️ Текст ($RANDOM_TYPE) опубликован без картинки" >> /var/www/apps/post-generator/special.log
    fi
    
    rm -f /tmp/special_img.jpg
}

echo "$(date): 🎲 Генерируем спецконтент: $RANDOM_TYPE"

case $RANDOM_TYPE in
    "quote") generate_quote ;;
    "meme") generate_meme ;;
    "comparison") generate_comparison ;;
    "review") generate_review ;;
    "case") generate_case ;;
esac

echo "✅ Спецконтент '$RANDOM_TYPE' обработан!"
