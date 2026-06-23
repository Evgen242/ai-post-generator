## CI/CD Архитектура: Codeberg → Drone → VPS

```mermaid
graph TD
    A["Разработчик (git push)"] -->|отправляет код| B["Codeberg (репозиторий)"]
    B -->|триггер через вебхук| C["Drone CI (сервер)"]
    C -->|запускает пайплайн| D[".drone.yml (шаги: test & deploy)"]
    D -->|по SSH| E["VPS сервер (aigenerator.myvnc.com)"]
    E -->|обновляет код| F["/home/deploy/ai-post-generator"]
    F -->|перезапуск| G["Приложение (Streamlit на порту 8501)"]
    G -->|доступ| H["https://aigenerator.myvnc.com"]

# trigger pipeline
# Webhook test
# Test CI/CD pipeline Mon Jun 15 11:59:45 AM UTC 2026
