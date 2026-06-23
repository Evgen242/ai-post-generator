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
```

### Описание

- **Триггер:** push в Codeberg → Webhook → Drone CI
- **Пайплайн:** `.drone.yml` (test → deploy)
- **Деплой:** SSH → VPS → git pull → restart сервиса