FROM python:3.11-slim

RUN apt-get update && apt-get install -y gdal-bin poppler-utils

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server.py .

RUN mkdir -p /app/output
WORKDIR /app

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
