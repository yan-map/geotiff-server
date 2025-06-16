FROM python:3.11-slim

# Системные утилиты
RUN apt-get update && apt-get install -y gdal-bin poppler-utils

# Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Приложение
COPY server.py .

# Папка для результатов
RUN mkdir -p /app/output
WORKDIR /app

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
