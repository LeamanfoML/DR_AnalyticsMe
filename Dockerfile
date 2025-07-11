FROM python:3.11-slim-bullseye  # Более стабильная база

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Кэширование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Оптимизация для SQLAlchemy 2.x
ENV SQLALCHEMY_WARN_20=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot/main.py"]
