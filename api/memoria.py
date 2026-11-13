"""Repositório em memória, com a mesma interface do RepositorioFirestore.

Usado nos testes automatizados e para rodar a API localmente sem nuvem
(STOKEI_MEMORIA=1). Os dados se perdem quando o processo termina, então
NÃO é usado em produção.
"""

from datetime import datetime, timezone

import estoque


class NaoEncontrado(Exception):
    """Produto inexistente (vira HTTP 404)."""


class RepositorioMemoria:
    def __init__(self):
        self.produtos = {}
        self.movimentacoes = []
        self._seq = 0

    def _proximo_id(self):
        self._seq += 1
        return f"p{self._seq}"

    def listar_produtos(self):
        return [dict(p) for p in self.produtos.values()]

    def criar_produto(self, dados):
        produto = {"id": self._proximo_id(), **dados}
        self.produtos[produto["id"]] = produto
        return dict(produto)

    def remover_produto(self, produto_id):
        if produto_id not in self.produtos:
            raise NaoEncontrado()
        del self.produtos[produto_id]

    def movimentar(self, produto_id, tipo, quantidade):
        if produto_id not in self.produtos:
            raise NaoEncontrado()
        produto = self.produtos[produto_id]
        produto["quantidade"] = estoque.aplicar_movimentacao(produto["quantidade"], tipo, quantidade)
        self._seq += 1
        self.movimentacoes.insert(0, {
            "produto_id": produto_id,
            "produto_nome": produto["nome"],
            "tipo": tipo,
            "quantidade": quantidade,
            "saldo": produto["quantidade"],
            "data": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        return dict(produto)

    def listar_movimentacoes(self, produto_id=None, limite=50):
        return [m for m in self.movimentacoes if not produto_id or m["produto_id"] == produto_id][:limite]
