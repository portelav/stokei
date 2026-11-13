#!/usr/bin/env bash
# Cria a infraestrutura do Stokei no Google Cloud e publica o contêiner
# (site + API) no Cloud Run.
#
# Uso (no Cloud Shell, na raiz do repositório):
#   bash scripts/deploy.sh SEU_ID_DE_PROJETO
#
# Pode ser executado de novo sem problema: o que já existe é mantido e o
# contêiner é publicado outra vez.

set -euo pipefail

PROJETO="${1:?Informe o ID do projeto: bash scripts/deploy.sh SEU_ID_DE_PROJETO}"
REGIAO="southamerica-east1"
SERVICO="stokei"
CONTA="stokei-api@${PROJETO}.iam.gserviceaccount.com"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

passo() { printf '\n==> %s\n' "$1"; }

passo "Selecionando o projeto ${PROJETO}"
gcloud config set project "$PROJETO"

passo "Ativando as APIs necessárias"
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com firestore.googleapis.com

passo "Criando o banco Firestore (modo nativo) em ${REGIAO}"
if gcloud firestore databases describe --database="(default)" >/dev/null 2>&1; then
  echo "Firestore já existe."
else
  gcloud firestore databases create --database="(default)" --location="$REGIAO" --type=firestore-native
fi

passo "Criando a conta de serviço do Stokei (somente acesso ao Firestore)"
if gcloud iam service-accounts describe "$CONTA" >/dev/null 2>&1; then
  echo "Conta de serviço já existe."
else
  gcloud iam service-accounts create stokei-api --display-name="Stokei"
fi
gcloud projects add-iam-policy-binding "$PROJETO" \
  --member="serviceAccount:${CONTA}" --role="roles/datastore.user" --condition=None >/dev/null
echo "Papel roles/datastore.user concedido."

passo "Montando a imagem (Dockerfile) e publicando no Cloud Run"
gcloud run deploy "$SERVICO" \
  --source="$RAIZ" --region="$REGIAO" \
  --allow-unauthenticated \
  --service-account="$CONTA" \
  --memory=256Mi --max-instances=2 \
  --quiet

URL="$(gcloud run services describe "$SERVICO" --region="$REGIAO" --format='value(status.url)')"

passo "Restringindo o CORS ao próprio endereço do serviço"
gcloud run services update "$SERVICO" --region="$REGIAO" \
  --update-env-vars="ALLOWED_ORIGIN=${URL}" --quiet

passo "Pronto!"
echo "Site e API: ${URL}"
echo
echo "Para rodar os testes da Etapa 5:  bash scripts/testar-api.sh ${URL}"
