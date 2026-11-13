# API do Stokei em contêiner, para publicar como serviço do Cloud Run
# (alternativa ao "gcloud functions deploy" usado em scripts/deploy.sh).
#
# Build e teste local:
#   docker build -t stokei-api .
#   docker run --rm -p 8080:8080 -e STOKEI_MEMORIA=1 stokei-api
#
# Publicar no Cloud Run (Cloud Shell, dentro da pasta api/):
#   gcloud run deploy stokei-api --source . --region southamerica-east1 \
#       --allow-unauthenticated --max-instances 2 \
#       --service-account stokei-api@SEU_PROJETO.iam.gserviceaccount.com \
#       --set-env-vars ALLOWED_ORIGIN=https://storage.googleapis.com

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py estoque.py memoria.py ./

# Não roda como root
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8080

# O Cloud Run informa a porta na variável PORT
CMD exec functions-framework --target=api --host=0.0.0.0 --port="${PORT}"
