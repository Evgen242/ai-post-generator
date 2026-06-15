#!/bin/bash

cd /var/www/apps/post-generator

echo "=== AI NEWS GENERATOR - СТАТУС ==="
echo ""
echo "📊 ПОСТЫ:"
echo "  Всего: $(grep -c "=== " posts.log 2>/dev/null || echo "0")"
echo "  С картинками: $(grep -c "✅ Пост с картинкой опубликован" posts.log 2>/dev/null || echo "0")"
echo "  За сегодня: $(grep "$(date +%Y-%m-%d)" posts.log 2>/dev/null | grep -c "✅" || echo "0")"
echo ""
echo "🖥️ СЕРВИСЫ:"
if curl -s http://localhost:8001/health > /dev/null; then
    echo "  ✅ API сервер: работает"
else
    echo "  ❌ API сервер: не работает"
fi
echo ""
echo "📝 ПОСЛЕДНИЙ ПОСТ:"
tail -5 posts.log 2>/dev/null || echo "Нет постов"
