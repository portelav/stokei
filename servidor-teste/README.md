# Servidor de teste (Flask)

Servidor mínimo para confirmar que a configuração do Google Cloud funciona antes de publicar a API do Stokei. Não faz parte do sistema.

Rotas:

- `/`: página que mostra "Servidor funcionando" e as informações do servidor
- `/saude`: as mesmas informações em JSON

Quando o servidor roda no Cloud Run, os campos `servico` e `revisao` vêm preenchidos. Localmente aparecem como `local`.

## Rodar no computador

```
cd servidor-teste
python -m venv .venv
.venv\Scripts\activate          # Windows (no Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python app.py
```

Abra http://localhost:8080.

Com Docker: `docker build -t stokei-teste .` e `docker run --rm -p 8080:8080 stokei-teste`.

## Publicar no Cloud Run (pelo Cloud Shell)

Troque `SEU_PROJETO` pelo ID do projeto:

```
gcloud config set project SEU_PROJETO
cd servidor-teste
gcloud run deploy stokei-teste --source . --region southamerica-east1 \
    --allow-unauthenticated --max-instances 1
```

- Como a pasta tem um `Dockerfile`, o Cloud Build usa ele para montar a imagem.
- Se o comando perguntar se pode ativar APIs ou criar um repositório no Artifact Registry, responda `Y`.
- No fim, ele mostra a URL do serviço (`https://stokei-teste-....run.app`). Abra essa URL: a página deve mostrar "Servidor funcionando" e o campo `servico` igual a `stokei-teste`.
- Os logs ficam em *Cloud Run → stokei-teste → Logs*. Cada acesso à página gera a linha "Acesso à página inicial".

## Apagar depois do teste

```
gcloud run services delete stokei-teste --region southamerica-east1
```
