FROM python:3.11-slim

# Устанавливаем необходимые системные пакеты
RUN apt-get update && apt-get install -y gdal-bin poppler-utils

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY server.py .  # <= убедись, что файл есть в корне

# Создаём папку для вывода
RUN mkdir -p /app/output
WORKDIR /app

# Запуск сервера
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
