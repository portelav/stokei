# Etapa 4 — Desenvolvimento da aplicação

## Tecnologias

| Camada | Tecnologia | Por quê |
|---|---|---|
| Linguagem do back-end | **Python 3.12** | Linguagem que o grupo domina, com suporte nativo no Cloud Run functions |
| Framework HTTP | **Functions Framework** (Google), sobre Flask | É o padrão do Google para funções em Python. O mesmo código roda local e na nuvem |
| Banco | **google-cloud-firestore** (biblioteca oficial) | Acesso ao Firestore com transações e autenticação automática pela conta de serviço |
| Front-end | **HTML + CSS + JavaScript puro** | Sem build nem framework. Basta enviar os arquivos ao bucket |
| Testes | **pytest** | Testes automatizados das regras, das rotas e do HTTP |
| Implantação | **gcloud CLI** (Cloud Shell) ou console | Ferramentas oficiais do Google Cloud |

## Organização do código

```
api/
  main.py         Ponto de entrada HTTP (função "api"), rotas e acesso ao Firestore
  estoque.py      Regras de negócio, sem nenhuma dependência de nuvem
  memoria.py      Repositório em memória (testes e execução local)
  requirements.txt
  tests/
    test_estoque.py   regras de negócio
    test_rotas.py     cada rota da API
    test_http.py      requisições HTTP reais (CORS, JSON inválido)
web/              site estático (HTML, CSS e JavaScript puros)
scripts/
  deploy.sh       cria a infraestrutura e publica (Cloud Shell)
  testar-api.sh   executa os 5 testes da Etapa 5
```

O código está separado em três camadas:

```
HTTP (main.api)  ──>  rotas (main.tratar)  ──>  regras (estoque.py)
                                    │
                                    └──>  repositório: Firestore (produção) ou memória (testes)
```

- **`estoque.py`** concentra as regras: validação dos dados, código único, cálculo do saldo, alerta de mínimo, busca e relatório. São funções puras, fáceis de testar.
- **`main.tratar`** recebe método, caminho e corpo e devolve status e resposta. Não sabe se os dados estão no Firestore ou na memória.
- **`RepositorioFirestore`** é a única parte que conversa com a nuvem.

Essa separação permitiu testar toda a lógica sem conta na nuvem e deixa claro, na apresentação, onde está cada responsabilidade.

## Integração com os serviços

**Firestore (armazenamento):**
- A função cria o cliente com `firestore.Client()`, sem passar senha ou chave. O Google injeta as credenciais da conta de serviço `stokei-api` no ambiente da função.
- A movimentação usa uma **transação**: lê o produto, calcula o novo saldo, atualiza o produto e grava o histórico. Ou tudo é gravado, ou nada é.
- A data da movimentação é gerada pelo servidor (`SERVER_TIMESTAMP`), não pelo navegador do usuário.

**Cloud Run functions (processamento):**
- Uma única função HTTP (`api`) atende todas as rotas.
- Responde OPTIONS para o *preflight* de CORS e adiciona os cabeçalhos CORS em toda resposta, liberando só a origem configurada em `ALLOWED_ORIGIN`.
- Os logs (`logging.info`) vão automaticamente para o Cloud Logging.

**Cloud Storage (interface):**
- O JavaScript do site chama a API com `fetch`. A URL da API fica numa constante (`API_URL`), que o `deploy.sh` preenche automaticamente.

## Interface

O site é dividido em quatro áreas: **Dashboard**, **Produtos**, **Movimentações** e **Histórico**. Ele só exibe dados e envia o que o usuário digita. Todas as regras ficam na API, então o navegador nunca decide sozinho se uma operação é válida.

| Área | Funcionalidade | O que o usuário faz | Rota da API | O que a interface mostra |
|---|---|---|---|---|
| Dashboard | F5. Resumo do estoque | Abre o sistema | `GET /relatorio` | Total de produtos, itens em estoque, valor do estoque e quantidade de itens abaixo do mínimo |
| Dashboard | F4. Alerta de estoque baixo | — | `GET /relatorio` (lista `abaixo_do_minimo`) | Quais produtos estão abaixo do mínimo |
| Produtos | F1. Cadastro | Informa código, nome, categoria, quantidade, mínimo e preço | `POST /produtos` | O produto novo na lista ou a mensagem de erro da API (ex.: código repetido) |
| Produtos | F2. Busca | Digita parte do nome, código ou categoria | `GET /produtos?busca=` | Só os produtos que combinam com o termo |
| Produtos | F4. Alerta de estoque baixo | — | `GET /produtos` (campo `alerta`) | Produtos abaixo do mínimo destacados dos demais |
| Produtos | Remoção | Escolhe um produto para remover | `DELETE /produtos/{id}` | A lista sem o produto |
| Movimentações | F3. Entrada e saída | Escolhe o produto, o tipo e a quantidade | `POST /movimentacao` | O saldo novo, ou a mensagem "Estoque insuficiente" quando a saída é maior que o saldo |
| Histórico | F6. Histórico | Consulta as movimentações | `GET /movimentacoes` | Data, produto, tipo, quantidade e saldo após cada operação (últimas 50) |

Regras que valem para a interface inteira:
- **Erros:** toda mensagem de erro exibida é a mensagem devolvida pela API (`{"erro": "..."}`). A interface não cria regras próprias.
- **Dados atualizados:** depois de cadastrar, remover ou movimentar, a interface consulta a API de novo, para refletir o estado salvo no Firestore.
- **Segurança:** textos digitados pelo usuário são exibidos com `textContent`, nunca como HTML (evita XSS).
- **Telas pequenas:** a interface deve funcionar também no celular.

## Pontos de atenção tratados no código

| Situação | Tratamento |
|---|---|
| Dados inválidos (nome vazio, quantidade negativa, texto no lugar de número) | Validados no servidor. Retorna **400** com mensagem clara |
| Saída maior que o saldo | Recusada com **400** ("Estoque insuficiente"). O saldo não muda |
| Código de produto repetido | Recusado com **400** (sem diferenciar maiúsculas de minúsculas) |
| Produto inexistente | **404** |
| Corpo da requisição que não é JSON | **400** |
| Duas movimentações simultâneas | Transação do Firestore, então o saldo continua correto |
| Nome de produto com HTML/script (XSS) | A interface usa `textContent`, que nunca interpreta o texto como HTML |
| Credenciais | Nenhuma no código: a autenticação vem da conta de serviço |
| Custo descontrolado | Máximo de 2 instâncias e orçamento com alertas |

## Como rodar localmente (sem nuvem)

```
cd api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
```

Para subir a API com dados em memória e usar a interface:

```
set STOKEI_MEMORIA=1
functions-framework --target=api --port=8080
```

Abra a página inicial do site (pasta `web/`) no navegador. O modo memória serve só para desenvolvimento: os dados somem ao parar o servidor. Em produção a função usa o Firestore.
