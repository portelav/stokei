# Etapa 3 — Configuração da nuvem (Google Cloud)

O grupo executa esta etapa no console do Google Cloud e no **Cloud Shell** (o terminal do próprio console, que já vem com `gcloud`, `git` e acesso ao projeto). Há dois caminhos que chegam ao mesmo resultado:

- **Caminho A: passo a passo.** Recomendado para a avaliação, porque cada tela vira um print de evidência (entregável C).
- **Caminho B: por script.** Um comando cria tudo e publica. Serve para refazer o deploy rapidamente ou como plano B.

Nos dois casos o Stokei roda como **um único contêiner no Cloud Run**, montado a partir do `Dockerfile` da raiz do repositório. O mesmo serviço entrega o site e a API, e os dados ficam no Firestore.

O enunciado pede **"criar o grupo de recursos, provisionar os serviços, configurar armazenamento, processamento, rede e permissões"**. A tabela mostra onde cada item é feito:

| Pedido no enunciado | Onde é feito |
|---|---|
| Grupo de recursos | Passo 1 (projeto do Google Cloud) |
| Armazenamento | Passo 3 (Firestore) |
| Processamento | Passo 5 (Cloud Run) |
| Rede | Passo 5 (endereço HTTPS público e CORS restrito ao próprio endereço) |
| Permissões | Passo 1 (membros do grupo), Passo 4 (conta de serviço) e Passo 5 (acesso público só de leitura/uso do site) |
| Consumo e custos (R6) | Passo 2 (orçamento), Passo 5 (máximo de instâncias) e Passo 7 (monitoramento) |

---

## Caminho A: passo a passo

Os passos marcados com 📸 indicam onde tirar print.

### Passo 1: Conta, projeto e membros

1. Acesse console.cloud.google.com e ative o **teste gratuito**. Use o tipo de conta **Individual**. O cartão é só para verificação: nada é cobrado sem ativar a conta paga.
2. No seletor de projetos, clique em **Novo projeto**. Nome: `stokei`. Anote o **ID do projeto** (ex.: `stokei-123456`).
3. Vá em **IAM e administrador → IAM → Conceder acesso**. Adicione o e-mail de cada integrante com o papel **Editor**.

📸 **Print 1:** tela do projeto criado (painel com nome e ID).
📸 **Print 2:** IAM com os integrantes do grupo.

### Passo 2: Orçamento com alerta

1. Vá em **Faturamento → Orçamentos e alertas → Criar orçamento**.
2. Nome: `stokei`. Escopo: projeto `stokei`. Valor: **R$ 10**. Alertas em **50%, 90% e 100%**.

📸 **Print 3:** orçamento criado.

### Passo 3: Firestore (armazenamento)

1. Vá em **Firestore → Criar banco de dados**.
2. ID: **(default)**. Só o banco default tem cota gratuita.
3. Modo: **Nativo**. Local: **southamerica-east1 (São Paulo)**. Regras: modo de produção (o banco fica fechado para acesso direto; só o serviço do Stokei acessa).

As coleções `produtos` e `movimentacoes` são criadas sozinhas na primeira gravação.

📸 **Print 4:** banco criado (tela de dados, ainda vazia).

### Passo 4: Conta de serviço (permissão mínima)

1. Vá em **IAM e administrador → Contas de serviço → Criar conta de serviço**.
2. Nome: `stokei-api`.
3. Papel: **Cloud Datastore User**, que permite ler e gravar no Firestore e nada mais.

É com essa identidade que o contêiner vai rodar. Não existe senha ou chave no código.

📸 **Print 5:** conta de serviço com o papel *Cloud Datastore User*.

### Passo 5: Cloud Run (processamento e site)

Abra o **Cloud Shell** (ícone `>_` no topo do console) e rode, trocando `<ID-do-projeto>`:

```
git clone https://github.com/portelav/stokei.git
cd stokei
gcloud config set project <ID-do-projeto>
gcloud run deploy stokei --source . --region southamerica-east1 \
    --allow-unauthenticated --max-instances 2 --memory 256Mi \
    --service-account stokei-api@<ID-do-projeto>.iam.gserviceaccount.com
```

- Se perguntar se pode ativar APIs ou criar o repositório `cloud-run-source-deploy` no Artifact Registry, responda `Y`.
- O **Cloud Build** monta a imagem a partir do `Dockerfile`, o **Artifact Registry** guarda a imagem e o **Cloud Run** publica o serviço. Leva alguns minutos.
- `--allow-unauthenticated` deixa o site aberto na internet. `--max-instances 2` limita a escala e protege contra custo inesperado.

Ao final aparece a **URL do serviço** (ex.: `https://stokei-xxxxx-rj.a.run.app`). Restrinja o CORS a esse endereço:

```
gcloud run services update stokei --region southamerica-east1 \
    --update-env-vars ALLOWED_ORIGIN=<URL-do-serviço>
```

Teste: abra a URL no navegador. O Dashboard do Stokei deve aparecer com "API conectada" no menu.

📸 **Print 6:** **Cloud Run → stokei**, com a URL visível.
📸 **Print 7:** aba **Segurança** (ou *Revisões → Detalhes*) mostrando a conta de serviço `stokei-api`.
📸 **Print 8:** **Artifact Registry → cloud-run-source-deploy**, com a imagem do Stokei.
📸 **Print 9:** o sistema aberto pela URL pública, com dados cadastrados.

### Passo 6: Conferir que os dados estão na nuvem

1. Cadastre produtos e faça movimentações pelo site.
2. Vá em **Firestore → Dados** e confira os documentos nas coleções `produtos` e `movimentacoes`.

📸 **Print 10:** Firestore com documentos nas duas coleções. **Este é o print mais importante: prova a gravação na nuvem (R2).**

### Passo 7: Monitoramento e consumo

1. Vá em **Cloud Run → stokei → Métricas**: contagem de requisições, latência e erros.
2. Vá em **Cloud Run → stokei → Registros**: logs de cada chamada, incluindo "Produto cadastrado" e "Movimentação…".
3. Vá em **Faturamento → Relatórios**: custo do período.

📸 **Print 11:** métricas do serviço, com requisições processadas (R3).
📸 **Print 12:** logs do serviço.
📸 **Print 13:** relatório de faturamento.

---

## Caminho B: por script (Cloud Shell)

No Cloud Shell:

```
git clone https://github.com/portelav/stokei.git
cd stokei
bash scripts/deploy.sh <ID-do-projeto>
```

O script faz os passos 3 a 5: ativa as APIs, cria o Firestore e a conta de serviço, publica o contêiner no Cloud Run e restringe o CORS. No final mostra a URL do site. O orçamento (Passo 2) e os membros (Passo 1) continuam sendo feitos pelo console. Quem roda o script precisa ser **Proprietário** do projeto.

Depois, rode os testes da Etapa 5 contra a nuvem:

```
bash scripts/testar-api.sh <URL-do-serviço>
```

📸 **Print 14:** saída do script de testes. Ele mostra os 5 testes exigidos com `[OK]`.

Para publicar uma nova versão depois de mudar o código: `git pull` e rodar o `deploy.sh` de novo.

---

## Testar o contêiner no computador (opcional)

Com Docker instalado, na raiz do repositório:

```
docker build -t stokei .
docker run --rm -p 8080:8080 -e STOKEI_MEMORIA=1 stokei
```

Abra http://localhost:8080. Com `STOKEI_MEMORIA=1` os dados ficam só na memória, sem Firestore.

---

## Se der erro no deploy

| Mensagem (ou parecida) | Causa provável | O que fazer |
|---|---|---|
| `Billing account for project ... is not found` ou `billing is not enabled` | Projeto sem conta de faturamento vinculada | *Faturamento → Vincular uma conta de faturamento* ao projeto e rodar de novo |
| `PERMISSION_DENIED ... setIamPolicy` | Quem está rodando não é Proprietário (*Owner*) do projeto | Rodar com a conta que criou o projeto, ou pedir o papel Proprietário |
| `API ... has not been used in project ... or it is disabled` logo depois de ativar as APIs | As APIs levam um ou dois minutos para ficar ativas | Esperar e rodar de novo; o script aproveita o que já foi criado |
| Build falha com `missing permission on the build service account` | A conta usada pelo Cloud Build não tem o papel de build | Conceder o papel e rodar de novo (comandos abaixo) |
| `Permission 'iam.serviceaccounts.actAs' denied` | Quem publica não pode usar a conta de serviço `stokei-api` | Dar a quem publica o papel *Usuário da conta de serviço* nessa conta, ou rodar como Proprietário |
| Site abre, mas mostra "API fora do ar" | Serviço reiniciando ou cache do navegador | Esperar alguns segundos e recarregar com Ctrl+F5; ver os erros em *Cloud Run → stokei → Registros* |

Comandos para o erro de build:

```
NUM=$(gcloud projects describe <ID-do-projeto> --format='value(projectNumber)')
gcloud projects add-iam-policy-binding <ID-do-projeto> \
    --member="serviceAccount:${NUM}-compute@developer.gserviceaccount.com" \
    --role=roles/cloudbuild.builds.builder
```

---

## Checklist de evidências (entregável C)

- [ ] 1. Projeto criado
- [ ] 2. IAM com os integrantes
- [ ] 3. Orçamento com alertas
- [ ] 4. Firestore criado
- [ ] 5. Conta de serviço com papel mínimo
- [ ] 6. Serviço `stokei` no Cloud Run, com URL
- [ ] 7. Serviço usando a conta de serviço
- [ ] 8. Imagem no Artifact Registry
- [ ] 9. Sistema aberto pela URL pública
- [ ] 10. **Documentos no Firestore**
- [ ] 11. Métricas do serviço
- [ ] 12. Logs do serviço
- [ ] 13. Faturamento
- [ ] 14. Saída do `testar-api.sh` contra a nuvem

Salvem os prints em `docs/evidencias/` com o número no nome (ex.: `10-firestore.png`).

## Ao final do semestre

Para não haver cobrança depois da avaliação, vá em **IAM e administrador → Configurações → Encerrar** (excluir o projeto). Isso apaga todos os recursos de uma vez.
