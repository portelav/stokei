# Etapa 3 — Configuração da nuvem (Google Cloud)

O grupo executa esta etapa no console do Google Cloud. Há dois caminhos que chegam ao mesmo resultado:

- **Caminho A: pelo console, clicando.** É o recomendado para a avaliação, porque cada tela vira um print de evidência (entregável C).
- **Caminho B: por script, no Cloud Shell.** Um comando cria tudo e publica. Serve para refazer o deploy rapidamente ou como plano B.

O enunciado pede **"criar o grupo de recursos, provisionar os serviços, configurar armazenamento, processamento, rede e permissões"**. A tabela mostra onde cada item é feito:

| Pedido no enunciado | Onde é feito |
|---|---|
| Grupo de recursos | Passo 1 (projeto do Google Cloud) |
| Armazenamento | Passo 3 (Firestore) e Passo 6 (Cloud Storage) |
| Processamento | Passo 5 (Cloud Run functions) |
| Rede | Passo 5 (acesso HTTPS público, CORS) e Passo 6 (leitura pública do site) |
| Permissões | Passo 1 (membros do grupo), Passo 4 (conta de serviço) e Passo 6 (bucket) |
| Consumo e custos (R6) | Passo 2 (orçamento) e Passo 8 (monitoramento) |

---

## Caminho A: pelo console

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
3. Modo: **Nativo**. Local: **southamerica-east1 (São Paulo)**. Regras: modo de produção (o banco fica fechado para acesso direto; só a função acessa).

As coleções `produtos` e `movimentacoes` são criadas sozinhas na primeira gravação.

📸 **Print 4:** banco criado (tela de dados, ainda vazia).

### Passo 4: Conta de serviço (permissão mínima)

1. Vá em **IAM e administrador → Contas de serviço → Criar conta de serviço**.
2. Nome: `stokei-api`.
3. Papel: **Cloud Datastore User**, que permite ler e gravar no Firestore e nada mais.

É com essa identidade que a função vai rodar. Não existe senha ou chave no código.

📸 **Print 5:** conta de serviço com o papel *Cloud Datastore User*.

### Passo 5: Cloud Run functions (processamento)

1. Vá em **Cloud Run → Escrever uma função** (ou *Implantar contêiner → Função*).
2. Configure:
   - Nome do serviço: `stokei-api`. Região: **southamerica-east1**. Ambiente de execução: **Python 3.12**.
   - Autenticação: **Permitir acesso público** (a API é chamada pelo navegador).
   - Em *Contêiner, rede e segurança*:
     - **Segurança → Conta de serviço:** `stokei-api`
     - **Variáveis:** `ALLOWED_ORIGIN = https://storage.googleapis.com`
     - **Escalonamento → Máximo de instâncias:** `2`. Isso limita custos.
3. Criar. No editor que abre:
   - Ponto de entrada da função: **`api`**
   - Copie o conteúdo de `api/main.py`, `api/estoque.py`, `api/memoria.py` e `api/requirements.txt`. Crie os arquivos que não existirem.
4. **Salvar e implantar.** Ao final, copie a **URL** do serviço (ex.: `https://stokei-api-xxxxx-rj.a.run.app`).
5. Teste: abra `<URL>/produtos` no navegador. A resposta deve ser `[]`.

📸 **Print 6:** serviço `stokei-api` implantado, com a URL visível.
📸 **Print 7:** aba de segurança mostrando a conta de serviço `stokei-api`.
📸 **Print 8:** `<URL>/produtos` aberto no navegador.

### Passo 6: Cloud Storage (site)

1. Vá em **Cloud Storage → Buckets → Criar**.
2. Nome: `<ID-do-projeto>-stokei-web`. Local: **Region, southamerica-east1**. Classe: **Standard**.
3. **Desmarque** "Aplicar a prevenção do acesso público" e mantenha o **controle de acesso uniforme**.
4. No bucket, vá em **Permissões → Conceder acesso**. Principal: `allUsers`. Papel: **Leitor de objetos do Storage**. Isso deixa o site público só para leitura.
5. Em `web/config.js`, troque a linha `const API_URL = "http://localhost:8080";` pela URL do Passo 5, sem barra no final.
6. Faça **upload** de todos os arquivos da pasta `web/` para o bucket: as páginas `.html`, o `style.css` e os scripts `.js`.
7. Abra `https://storage.googleapis.com/<ID-do-projeto>-stokei-web/index.html`.

📸 **Print 9:** bucket com os 3 arquivos do site e a permissão `allUsers` como leitor.
📸 **Print 10:** o sistema aberto pela URL pública, com dados cadastrados.

### Passo 7: Conferir que os dados estão na nuvem

1. Cadastre produtos e faça movimentações pelo site.
2. Vá em **Firestore → Dados** e confira os documentos nas coleções `produtos` e `movimentacoes`.

📸 **Print 11:** Firestore com documentos nas duas coleções. **Este é o print mais importante: prova a gravação na nuvem (R2).**

### Passo 8: Monitoramento e consumo

1. Vá em **Cloud Run → stokei-api → Métricas**: contagem de requisições, latência e erros.
2. Vá em **Cloud Run → stokei-api → Registros**: logs de cada chamada, incluindo "Produto cadastrado" e "Movimentação…".
3. Vá em **Faturamento → Relatórios**: custo do período.

📸 **Print 12:** métricas da função, com requisições processadas (R3).
📸 **Print 13:** logs da função.
📸 **Print 14:** relatório de faturamento.

---

## Caminho B: por script (Cloud Shell)

No console, clique no ícone **Ativar Cloud Shell** (`>_`, no topo) e rode:

```
git clone <url-do-repositorio> stokei
cd stokei
bash scripts/deploy.sh <ID-do-projeto>
```

O script faz os passos 3 a 6 e mostra no final a URL do site e a da API. O orçamento (Passo 2) e os membros (Passo 1) continuam sendo feitos pelo console.

Depois, rode os testes da Etapa 5 contra a nuvem:

```
bash scripts/testar-api.sh <URL-da-API>
```

📸 Tire print da saída do script de testes. Ele mostra os 5 testes exigidos com `[OK]`.

---

## Checklist de evidências (entregável C)

- [ ] 1. Projeto criado
- [ ] 2. IAM com os integrantes
- [ ] 3. Orçamento com alertas
- [ ] 4. Firestore criado
- [ ] 5. Conta de serviço com papel mínimo
- [ ] 6. Função implantada com URL
- [ ] 7. Função usando a conta de serviço
- [ ] 8. API respondendo no navegador
- [ ] 9. Bucket com os arquivos do site e leitura pública
- [ ] 10. Sistema aberto pela URL pública
- [ ] 11. **Documentos no Firestore**
- [ ] 12. Métricas da função
- [ ] 13. Logs da função
- [ ] 14. Faturamento
- [ ] 15. Saída do `testar-api.sh` contra a nuvem

Salvem os prints em `docs/evidencias/` com o número no nome (ex.: `11-firestore.png`).

## Ao final do semestre

Para não haver cobrança depois da avaliação, vá em **IAM e administrador → Configurações → Encerrar** (excluir o projeto). Isso apaga todos os recursos de uma vez.
