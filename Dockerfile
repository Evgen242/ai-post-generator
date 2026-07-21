FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем пользователя для приложения
RUN useradd -m -u 1000 deploy && chown -R deploy:deploy /app
USER deploy

# Открываем порт Streamlit
EXPOSE 8501

# Запускаем приложение
CMD ["streamlit", "run", "🏠_Главная.py", "--server.port=8501", "--server.address=0.0.0.0"]
