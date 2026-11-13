#!/usr/bin/env bash
# Cria a infraestrutura do Stokei no Google Cloud e publica a API e o site.
#
# Uso (no Cloud Shell, na raiz do repositório):
#   bash scripts/deploy.sh SEU_ID_DE_PROJETO
#
# Pode ser executado de novo sem problema: o que já existe é mantido e a
# API e o site são publicados outra vez.

set -euo pipefail

PROJETO="${1:?Informe o ID do projeto: bash scripts/deploy.sh SEU_ID_DE_PROJETO}"
REGIAO="southamerica-east1"
FUNCAO="stokei-api"
CONTA="stokei-api@${PROJETO}.iam.gserviceaccount.com"
BUCKET="gs://${PROJETO}-stokei-web"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

passo() { printf '\n==> %s\n' "$1"; }

passo "Selecionando o projeto ${PROJETO}"
gcloud config set project "$PROJETO"

passo "Ativando as APIs necessárias"
gcloud services enable \
  cloudfunctions.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com firestore.googleapis.com storage.googleapis.com

passo "Criando o banco Firestore (modo nativo) em ${REGIAO}"
if gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
  echo "Firestore já existe."
else
  gcloud firestore databases create --database="(default)" --location="$REGIAO" --type=firestore-native
fi

passo "Criando a conta de serviço da API (somente acesso ao Firestore)"
if gcloud iam service-accounts describe "$CONTA" >/dev/null 2>&1; then
  echo "Conta de serviço já existe."
else
  gcloud iam service-accounts create "$FUNCAO" --display-name="Stokei API"
fi
gcloud projects add-iam-policy-binding "$PROJETO" \
  --member="serviceAccount:${CONTA}" --role="roles/datastore.user" --condition=None >/dev/null
echo "Papel roles/datastore.user concedido."

passo "Criando o bucket do site"
if gcloud storage buckets describe "$BUCKET" >/dev/null 2>&1; then
  echo "Bucket já existe."
else
  gcloud storage buckets create "$BUCKET" --location="$REGIAO" --uniform-bucket-level-access
fi
gcloud storage buckets add-iam-policy-binding "$BUCKET" \
  --member=allUsers --role=roles/storage.objectViewer >/dev/null
echo "Leitura pública liberada (somente leitura)."

passo "Publicando a API (Cloud Run functions)"
gcloud functions deploy "$FUNCAO" --gen2 \
  --runtime=python312 --region="$REGIAO" \
  --source="${RAIZ}/api" --entry-point=api \
  --trigger-http --allow-unauthenticated \
  --service-account="$CONTA" \
  --set-env-vars=ALLOWED_ORIGIN=https://storage.googleapis.com \
  --memory=256Mi --max-instances=2

URL_API="$(gcloud functions describe "$FUNCAO" --gen2 --region="$REGIAO" --format='value(serviceConfig.uri)')"
echo "API publicada em: ${URL_API}"

passo "Publicando o site com o endereço da API"
TMP="$(mktemp -d)"
cp "${RAIZ}/web/index.html" "${RAIZ}/web/style.css" "$TMP/"
sed "s#const API_URL = \".*\";#const API_URL = \"${URL_API}\";#" "${RAIZ}/web/app.js" > "${TMP}/app.js"
gcloud storage cp "${TMP}/index.html" "${BUCKET}/index.html" \
  --cache-control="no-cache" --content-type="text/html; charset=utf-8"
gcloud storage cp "${TMP}/style.css" "${BUCKET}/style.css" \
  --cache-control="no-cache" --content-type="text/css; charset=utf-8"
gcloud storage cp "${TMP}/app.js" "${BUCKET}/app.js" \
  --cache-control="no-cache" --content-type="text/javascript; charset=utf-8"
rm -rf "$TMP"

passo "Pronto!"
echo "Site: https://storage.googleapis.com/${PROJETO}-stokei-web/index.html"
echo "API:  ${URL_API}"
echo
echo "Para rodar os testes da Etapa 5:  bash scripts/testar-api.sh ${URL_API}"
