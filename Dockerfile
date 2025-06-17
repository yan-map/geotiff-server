FROM python:3.11-slim

RUN apt update && apt install -y \
    gdal-bin \
    poppler-utils \
    && pip install --no-cache-dir \
    fastapi uvicorn pdf2image python-multipart requests Pillow

WORKDIR /app
COPY . /app

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
