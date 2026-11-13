"""API do Stokei, sistema de estoque (Google Cloud Run functions, Python).

Rotas:
    GET    /produtos?busca=texto        lista produtos (busca por nome, código ou categoria) com flag de alerta
    POST   /produtos                    cadastra produto
    DELETE /produtos/{id}               remove produto
    POST   /movimentacao                registra entrada ou saída
    GET    /movimentacoes?produto_id=   histórico (mais recentes primeiro)
    GET    /relatorio                   resumo do estoque (dashboard)

Os dados ficam no Firestore. A autenticação com o Firestore é feita pela conta
de serviço da função (credenciais do ambiente), sem chave ou senha no código.
"""

import json
import logging
import os

import functions_framework

import estoque
from memoria import NaoEncontrado, RepositorioMemoria

PRODUTOS = "produtos"
MOVIMENTACOES = "movimentacoes"
LIMITE_HISTORICO = 50


# --------------------------------------------------------------------------
# Acesso ao Firestore
# --------------------------------------------------------------------------

class RepositorioFirestore:
    def __init__(self):
        from google.cloud import firestore

        self._fs = firestore
        self.db = firestore.Client()

    @staticmethod
    def _produto(doc):
        dados = doc.to_dict()
        return {
            "id": doc.id,
            "codigo": dados.get("codigo", ""),
            "nome": dados["nome"],
            "categoria": dados.get("categoria", ""),
            "quantidade": int(dados["quantidade"]),
            "minimo": int(dados["minimo"]),
            "preco": float(dados["preco"]),
        }

    def listar_produtos(self):
        return [self._produto(d) for d in self.db.collection(PRODUTOS).stream()]

    def criar_produto(self, dados):
        ref = self.db.collection(PRODUTOS).document()
        ref.set(dados)
        return {"id": ref.id, **dados}

    def remover_produto(self, produto_id):
        ref = self.db.collection(PRODUTOS).document(produto_id)
        if not ref.get().exists:
            raise NaoEncontrado()
        ref.delete()

    def movimentar(self, produto_id, tipo, quantidade):
        """Atualiza o saldo e grava o histórico numa única transação.

        Se duas movimentações chegarem ao mesmo tempo, o Firestore repete a
        transação, então o saldo nunca fica errado nem negativo.
        """
        fs = self._fs
        produto_ref = self.db.collection(PRODUTOS).document(produto_id)
        historico_ref = self.db.collection(MOVIMENTACOES).document()

        @fs.transactional
        def executar(transacao):
            doc = produto_ref.get(transaction=transacao)
            if not doc.exists:
                raise NaoEncontrado()
            produto = self._produto(doc)
            produto["quantidade"] = estoque.aplicar_movimentacao(produto["quantidade"], tipo, quantidade)
            transacao.update(produto_ref, {"quantidade": produto["quantidade"]})
            transacao.set(historico_ref, {
                "produto_id": produto_id,
                "produto_nome": produto["nome"],
                "tipo": tipo,
                "quantidade": quantidade,
                "saldo": produto["quantidade"],
                "data": fs.SERVER_TIMESTAMP,
            })
            return produto

        return executar(self.db.transaction())

    def listar_movimentacoes(self, produto_id=None):
        from google.cloud.firestore_v1.base_query import FieldFilter

        colecao = self.db.collection(MOVIMENTACOES)
        if produto_id:
            # Filtro + ordenação em campos diferentes exigiria índice composto;
            # com o volume do projeto, ordenar em memória é suficiente.
            docs = colecao.where(filter=FieldFilter("produto_id", "==", produto_id)).stream()
        else:
            docs = colecao.order_by("data", direction=self._fs.Query.DESCENDING).limit(LIMITE_HISTORICO).stream()

        movimentacoes = []
        for d in docs:
            m = d.to_dict()
            movimentacoes.append({
                "produto_id": m["produto_id"],
                "produto_nome": m["produto_nome"],
                "tipo": m["tipo"],
                "quantidade": int(m["quantidade"]),
                "saldo": int(m["saldo"]),
                "data": m["data"].isoformat() if m.get("data") else None,
            })
        movimentacoes.sort(key=lambda m: m["data"] or "", reverse=True)
        return movimentacoes[:LIMITE_HISTORICO]


# --------------------------------------------------------------------------
# Rotas (independentes do Firestore, para poderem ser testadas)
# --------------------------------------------------------------------------

def com_alerta(produto):
    return {**produto, "alerta": estoque.em_alerta(produto)}


def produtos_ordenados(repo):
    return sorted(repo.listar_produtos(), key=lambda p: p["nome"].lower())


def tratar(metodo, caminho, params, ler_corpo, repo):
    """Executa a rota e devolve (status, corpo)."""
    partes = [p for p in caminho.strip("/").split("/") if p]
    if partes and partes[0] == "api":
        partes = partes[1:]

    try:
        if partes == ["produtos"] and metodo == "GET":
            produtos = estoque.filtrar_produtos(produtos_ordenados(repo), params.get("busca"))
            return 200, [com_alerta(p) for p in produtos]

        if partes == ["produtos"] and metodo == "POST":
            dados = estoque.validar_produto(ler_corpo())
            estoque.verificar_codigo_unico(repo.listar_produtos(), dados["codigo"])
            produto = repo.criar_produto(dados)
            logging.info("Produto cadastrado: %s", produto["id"])
            return 201, com_alerta(produto)

        if len(partes) == 2 and partes[0] == "produtos" and metodo == "DELETE":
            repo.remover_produto(partes[1])
            return 204, None

        if partes == ["movimentacao"] and metodo == "POST":
            dados = ler_corpo()
            if not isinstance(dados, dict) or not isinstance(dados.get("id"), str) or not dados["id"]:
                raise estoque.ErroValidacao("'id' do produto é obrigatório")
            produto = repo.movimentar(dados["id"], dados.get("tipo"), dados.get("quantidade"))
            logging.info("Movimentação %s de %s no produto %s", dados["tipo"], dados["quantidade"], dados["id"])
            return 200, com_alerta(produto)

        if partes == ["movimentacoes"] and metodo == "GET":
            return 200, repo.listar_movimentacoes(params.get("produto_id"))

        if partes == ["relatorio"] and metodo == "GET":
            return 200, estoque.gerar_relatorio(produtos_ordenados(repo))

    except estoque.ErroValidacao as e:
        return 400, {"erro": str(e)}
    except NaoEncontrado:
        return 404, {"erro": "Produto não encontrado"}

    return 404, {"erro": "Rota não encontrada"}


# --------------------------------------------------------------------------
# Ponto de entrada HTTP
# --------------------------------------------------------------------------

_repo = None


def repositorio():
    """Firestore em produção; memória quando STOKEI_MEMORIA=1 (só para desenvolvimento local)."""
    global _repo
    if _repo is None:
        if os.environ.get("STOKEI_MEMORIA") == "1":
            logging.warning("STOKEI_MEMORIA=1: usando repositório em memória (dados não persistem)")
            _repo = RepositorioMemoria()
        else:
            _repo = RepositorioFirestore()
    return _repo


def cabecalhos_cors():
    return {
        "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "*"),
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
    }


@functions_framework.http
def api(request):
    if request.method == "OPTIONS":
        return "", 204, cabecalhos_cors()

    def ler_corpo():
        dados = request.get_json(silent=True)
        if dados is None:
            raise estoque.ErroValidacao("Corpo da requisição não é um JSON válido")
        return dados

    status, corpo = tratar(request.method, request.path, request.args, ler_corpo, repositorio())
    if corpo is None:
        return "", status, cabecalhos_cors()
    cabecalhos = {**cabecalhos_cors(), "Content-Type": "application/json; charset=utf-8"}
    return json.dumps(corpo, ensure_ascii=False), status, cabecalhos
