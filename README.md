##  CI/CD Архитектура: GitHub → GitHub Actions → VPS

```mermaid
graph TD
    A["Разработчик (git push)"] -->|отправляет код| B["GitHub (репозиторий)"]
    B -->|триггер через push| C["GitHub Actions"]
    C -->|запускает пайплайн| D[".github/workflows/deploy.yml"]
    C -->|сборка образа| E["Docker Hub (evgen1771/ai-post-generator)"]
    E -->|скачивание образа| F["VPS сервер (103.125.216.112)"]
    F -->|запуск контейнера| G["Приложение (Streamlit на порту 8501)"]
    G -->|доступ через nginx| H["https://autolot25.ddns.net:8082"]

    C -->|уведомление| I["Telegram бот (@SeRveDog_bot)"]
    I -->|успех/ошибка| A
```
Описание
Триггер: push в main → GitHub Actions

Пайплайн: .github/workflows/deploy.yml (build → push → deploy)

Сборка: Docker образ → Docker Hub

Деплой: SSH → VPS → docker pull → docker compose up -d

Уведомления: Telegram бот @SeRveDog_bot

📦 Приложение
Название: Telegram Post Generator

Доступ: https://autolot25.ddns.net:8082

Логин: admin / Bash_2026

Технологии: Streamlit, Python, PostgreSQL, Docker

AI: OpenRouter (текст) + Pollinations (изображения)

Языки: 4

