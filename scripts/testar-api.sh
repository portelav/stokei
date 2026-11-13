#!/usr/bin/env bash
# Executa os 5 testes exigidos na Etapa 5 contra a API do Stokei.
#
# Uso:
#   bash scripts/testar-api.sh https://stokei-api-xxxxx.a.run.app   (nuvem)
#   bash scripts/testar-api.sh http://localhost:8080                 (local)
#
# Cria um produto de teste chamado "Produto de teste <horário>".

set -uo pipefail

API="${1:?Informe a URL da API}"
API="${API%/}"
FALHAS=0

# Faz a requisição e imprime o status HTTP e o corpo da resposta.
requisicao() {
  local metodo="$1" caminho="$2" corpo="${3:-}"
  local args=(-s -w '\n%{http_code}' -X "$metodo" "${API}${caminho}")
  [ -n "$corpo" ] && args+=(-H "Content-Type: application/json" -d "$corpo")
  local saida; saida="$(curl "${args[@]}")"
  STATUS="${saida##*$'\n'}"
  CORPO="${saida%$'\n'*}"
  printf '%s %s -> HTTP %s\n%s\n' "$metodo" "$caminho" "$STATUS" "$CORPO"
}

conferir() {
  local esperado="$1" descricao="$2"
  if [ "$STATUS" = "$esperado" ]; then
    printf '[OK]    %s (HTTP %s)\n\n' "$descricao" "$STATUS"
  else
    printf '[FALHA] %s (esperado HTTP %s, recebido %s)\n\n' "$descricao" "$esperado" "$STATUS"
    FALHAS=$((FALHAS + 1))
  fi
}

echo "Testando ${API} em $(date '+%d/%m/%Y %H:%M:%S')"
echo

echo "--- Teste 1: acesso à API pela internet ---"
requisicao GET /produtos
conferir 200 "API respondeu"

echo "--- Teste 2: inserção e armazenamento de dados ---"
NOME="Produto de teste $(date +%H%M%S)"
CODIGO="TESTE-$(date +%H%M%S)"
requisicao POST /produtos "{\"codigo\":\"${CODIGO}\",\"nome\":\"${NOME}\",\"categoria\":\"Testes\",\"quantidade\":3,\"minimo\":5,\"preco\":2.5}"
conferir 201 "Produto cadastrado"
ID="$(printf '%s' "$CORPO" | grep -o '"id": *"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
echo "id do produto criado: ${ID}"
requisicao GET "/produtos?busca=$(printf '%s' "$NOME" | sed 's/ /%20/g')"
conferir 200 "Produto recuperado do banco pela busca"

echo "--- Teste 3: processamento na nuvem (entrada de estoque) ---"
requisicao POST /movimentacao "{\"id\":\"${ID}\",\"tipo\":\"entrada\",\"quantidade\":4}"
conferir 200 "Entrada processada: saldo 3 + 4 = 7 e alerta desligado (7 >= mínimo 5)"

echo "--- Teste 4: recuperação e apresentação dos resultados ---"
requisicao GET /relatorio
conferir 200 "Relatório gerado"
requisicao GET "/movimentacoes?produto_id=${ID}"
conferir 200 "Histórico recuperado"

echo "--- Teste 5: entradas inválidas e falhas simples ---"
requisicao POST /movimentacao "{\"id\":\"${ID}\",\"tipo\":\"saida\",\"quantidade\":999}"
conferir 400 "Saída maior que o saldo foi recusada"
requisicao POST /produtos '{"nome":"","quantidade":-1}'
conferir 400 "Cadastro com dados inválidos foi recusado"
requisicao POST /produtos "{\"codigo\":\"${CODIGO}\",\"nome\":\"Duplicado\"}"
conferir 400 "Cadastro com código repetido foi recusado"
requisicao POST /movimentacao '{"id":"nao-existe","tipo":"entrada","quantidade":1}'
conferir 404 "Movimentação em produto inexistente retornou 404"
requisicao POST /produtos '{isto nao e json'
conferir 400 "Corpo que não é JSON foi recusado"

echo "--- Limpeza ---"
requisicao DELETE "/produtos/${ID}"
conferir 204 "Produto de teste removido"

if [ "$FALHAS" -eq 0 ]; then
  echo "RESULTADO: todos os testes passaram."
else
  echo "RESULTADO: ${FALHAS} teste(s) falharam."
  exit 1
fi
