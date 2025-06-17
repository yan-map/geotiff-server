# GeoPDF Renderer for Railway

## Установка локально
```bash
pip install -r requirements.txt
sudo apt install poppler-utils gdal-bin
uvicorn server:app --reload
```

## Пример curl-запроса
```bash
curl -X POST https://your-app.up.railway.app/render \
  -F "pdf=@plan.pdf" \
  -F "tl=76.9500,43.2700" \
  -F "tr=76.9700,43.2700" \
  -F "br=76.9700,43.2500" \
  -F "bl=76.9500,43.2500" \
  -F "zoom=20"
```
