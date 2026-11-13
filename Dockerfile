# Stokei: site e API no mesmo contêiner, publicado no Cloud Run.
#
# Build e teste local (dados em memória):
#   docker build -t stokei .
#   docker run --rm -p 8080:8080 -e STOKEI_MEMORIA=1 stokei
#   abrir http://localhost:8080
#
# Publicar: bash scripts/deploy.sh <ID-do-projeto>   (no Cloud Shell)

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    STOKEI_WEB=/app/web

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/main.py api/estoque.py api/memoria.py ./
COPY web/ ./web/

# Não roda como root
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8080

# O Cloud Run informa a porta na variável PORT
CMD exec functions-framework --target=api --host=0.0.0.0 --port="${PORT}"
