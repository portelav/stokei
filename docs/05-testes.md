# Etapa 5 — Testes e validação

## Os 5 testes exigidos

O script `scripts/testar-api.sh` executa todos os testes abaixo e marca cada um como `[OK]` ou `[FALHA]`. Ele foi rodado localmente e precisa ser rodado de novo contra a nuvem depois do deploy.

| # | O que o enunciado pede | Como é testado | Resultado esperado | Local | Nuvem |
|---|---|---|---|---|---|
| 1 | Acesso à aplicação ou API pela internet | `GET /produtos`. Na nuvem, abrir também a URL pública do site | HTTP 200 | ✅ | ☐ |
| 2 | Inserção e armazenamento de dados | `POST /produtos` e depois `GET /produtos?busca=` para recuperar o que foi gravado. Na nuvem, conferir o documento no console do Firestore | 201, e o produto aparece na busca | ✅ | ☐ |
| 3 | Processamento executado na nuvem | `POST /movimentacao` com entrada de 4 num produto com saldo 3 e mínimo 5 | 200, saldo 7, alerta desligado | ✅ | ☐ |
| 4 | Recuperação e apresentação dos resultados | `GET /relatorio` e `GET /movimentacoes`; na interface, Dashboard e Histórico | 200, com totais e histórico corretos | ✅ | ☐ |
| 5 | Comportamento com entrada inválida ou falha simples | Saída de 999 unidades, cadastro com nome vazio, código repetido, produto inexistente, corpo que não é JSON | 400, 400, 400, 404, 400, sem alterar dados | ✅ | ☐ |

Saída completa da execução local: [`evidencias/testes-api-local.txt`](evidencias/testes-api-local.txt). Resultado: **12 de 12 verificações OK** (11 testes e a remoção do produto de teste).

Depois do deploy, rodem `bash scripts/testar-api.sh <URL-da-API>` no Cloud Shell, salvem o print e marquem a coluna "Nuvem".

## Testes automatizados

Além dos testes de ponta a ponta, o projeto tem **58 testes automatizados** (pytest), todos passando:

| Arquivo | Testes | O que cobre |
|---|---|---|
| `test_estoque.py` | 40 | Validação de produto (16 casos de entrada inválida), código único, entrada e saída, bloqueio de saldo negativo, busca por nome/código/categoria, alerta e relatório |
| `test_rotas.py` | 14 | Cada rota da API, inclusive os erros 400 e 404 e o código duplicado |
| `test_http.py` | 4 | Requisições HTTP reais: CORS (*preflight*), JSON válido e inválido, DELETE |

Saída completa: [`evidencias/testes-unitarios.txt`](evidencias/testes-unitarios.txt).

## Testes da interface

Cada funcionalidade é verificada pela interface, independentemente do layout. Os prints ficam em `docs/evidencias/` e serão refeitos após a reformulação visual do site.

**Dados de exemplo** (para os resultados abaixo baterem):

| Código | Nome | Categoria | Qtd. inicial | Mínimo | Preço | Movimentação |
|---|---|---|---|---|---|---|
| ARZ-05 | Arroz 5kg | Mercearia | 20 | 10 | 25,90 | entrada de 10 |
| FEJ-01 | Feijão carioca 1kg | Mercearia | 12 | 10 | 8,49 | saída de 8 |
| CAF-500 | Café 500g | Bebidas | 15 | 5 | 18,50 | saída de 3 |
| ACU-01 | Açúcar 1kg | Mercearia | 2 | 8 | 4,79 | — |
| OLE-900 | Óleo de soja 900ml | Mercearia | 12 | 6 | 7,99 | saída de 2 |

| Área | Funcionalidade | Como testar | Resultado esperado | Print |
|---|---|---|---|---|
| Dashboard | F5. Resumo | Abrir o sistema com os dados de exemplo | 5 produtos, 58 itens, R$ 1.122,44, 2 abaixo do mínimo | ☐ |
| Dashboard | F4. Alerta | Conferir os itens críticos | Açúcar (2/8) e Feijão (4/10) | ☐ |
| Produtos | F1. Cadastro | Cadastrar "LEI-01 · Leite integral 1L", quantidade 3, mínimo 6 | O produto aparece na lista, destacado como abaixo do mínimo | ☐ |
| Produtos | F1. Código repetido | Cadastrar outro produto com código "lei-01" | Mensagem de erro da API; nenhum produto novo | ☐ |
| Produtos | F2. Busca | Buscar "merc", depois "CAF" | Primeiro os 4 produtos da Mercearia, depois só o Café | ☐ |
| Movimentações | F3. Entrada | Entrada de 5 no Leite | Saldo 8; o Leite deixa de estar em alerta | ☐ |
| Movimentações | F3. Saída inválida | Saída de 100 no Leite | Mensagem "Estoque insuficiente"; saldo continua 8 | ☐ |
| Histórico | F6. Histórico | Abrir após as movimentações | Movimentações mais recentes primeiro, com o saldo após cada uma | ☐ |
| Todas | Celular | Repetir a navegação numa tela de celular | Todas as áreas utilizáveis, sem conteúdo cortado | ☐ |

Os valores esperados foram conferidos pela API com os mesmos dados (`GET /relatorio`: 5 produtos, 58 itens, R$ 1.122,44, 2 abaixo do mínimo).

## Resultados obtidos

- Todas as regras de negócio funcionam como planejado: o saldo nunca fica negativo, o alerta acende e apaga conforme o mínimo e o relatório bate com a soma manual.
- Toda entrada inválida testada foi recusada com mensagem clara, sem alterar os dados.
- A interface será validada pela tabela acima, com prints, após a reformulação visual.

## Limitações conhecidas

| Limitação | Impacto | Possível melhoria |
|---|---|---|
| Sem login | Qualquer pessoa com a URL pode alterar o estoque | Firebase Authentication ou Identity Platform |
| Testes de ponta a ponta feitos localmente, com o banco em memória | A integração real com o Firestore só é validada após o deploy | Rodar `testar-api.sh` contra a URL da nuvem (já previsto) |
| A lista de produtos e o relatório leem a coleção inteira a cada consulta | Mais leituras no Firestore, o que conta para a cota gratuita | Guardar totais pré-calculados ou reaproveitar a lista para calcular o relatório |
| A API devolve só as últimas 50 movimentações | Movimentações antigas não podem ser consultadas | Paginação |
| Primeira requisição após um tempo parado é mais lenta (*cold start*, alguns segundos) | Pequena espera no primeiro acesso | Instância mínima = 1 (custa mais) |
| Sem edição de produto (nome, código, categoria, mínimo, preço) | É preciso remover e cadastrar de novo | Rota `PUT /produtos/{id}` |
| A verificação de código único lê todos os produtos antes de cadastrar | Duas pessoas cadastrando o mesmo código no mesmo instante poderiam passar | Usar o código como ID do documento no Firestore |
| No `curl` do Windows (Prompt/Git Bash), nomes com acento são enviados em outra codificação e recusados como JSON inválido | Só afeta testes manuais no terminal do Windows; navegador e Cloud Shell enviam UTF-8 normalmente | Usar o Cloud Shell ou o próprio site para os testes |
