# Servidor de teste em contêiner.
#
# Build e teste local:
#   docker build -t stokei-teste .
#   docker run --rm -p 8080:8080 stokei-teste
#
# Publicar no Cloud Run (Cloud Shell, dentro da pasta servidor-teste/):
#   gcloud run deploy stokei-teste --source . --region southamerica-east1 \
#       --allow-unauthenticated --max-instances 1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8080

CMD exec gunicorn --bind ":${PORT}" --workers 1 --threads 4 app:app
