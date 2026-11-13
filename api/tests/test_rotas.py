"""Testes das rotas da API com um repositório em memória no lugar do Firestore."""

import pytest

import estoque
from main import tratar
from memoria import RepositorioMemoria


@pytest.fixture
def repo():
    return RepositorioMemoria()


def chamar(repo, metodo, caminho, corpo=None, params=None):
    def ler_corpo():
        if corpo is None:
            raise estoque.ErroValidacao("Corpo da requisição não é um JSON válido")
        return corpo

    return tratar(metodo, caminho, params or {}, ler_corpo, repo)


def cadastrar(repo, **dados):
    status, produto = chamar(repo, "POST", "/produtos", {"nome": "Caneta", "quantidade": 3, "minimo": 5, "preco": 2.5, **dados})
    assert status == 201
    return produto


def test_cadastro_e_listagem_com_alerta(repo):
    produto = cadastrar(repo)
    assert produto["alerta"] is True
    status, lista = chamar(repo, "GET", "/produtos")
    assert status == 200
    assert lista == [produto]


def test_prefixo_api_e_aceito(repo):
    cadastrar(repo)
    assert chamar(repo, "GET", "/api/produtos")[0] == 200


def test_cadastro_invalido_retorna_400(repo):
    status, corpo = chamar(repo, "POST", "/produtos", {"nome": ""})
    assert status == 400
    assert "nome" in corpo["erro"]


def test_corpo_que_nao_e_json_retorna_400(repo):
    status, _ = chamar(repo, "POST", "/produtos", corpo=None)
    assert status == 400


def test_codigo_duplicado_retorna_400(repo):
    cadastrar(repo, codigo="CAN-01")
    status, corpo = chamar(repo, "POST", "/produtos", {"nome": "Outra", "codigo": "can-01"})
    assert status == 400
    assert "código" in corpo["erro"]
    assert len(repo.produtos) == 1


def test_busca_por_nome(repo):
    cadastrar(repo, nome="Caneta Azul")
    cadastrar(repo, nome="Lápis")
    status, lista = chamar(repo, "GET", "/produtos", params={"busca": "caneta"})
    assert [p["nome"] for p in lista] == ["Caneta Azul"]


def test_entrada_atualiza_saldo_e_alerta(repo):
    produto = cadastrar(repo)
    status, atualizado = chamar(repo, "POST", "/movimentacao", {"id": produto["id"], "tipo": "entrada", "quantidade": 4})
    assert status == 200
    assert atualizado["quantidade"] == 7
    assert atualizado["alerta"] is False


def test_saida_maior_que_saldo_retorna_400(repo):
    produto = cadastrar(repo)
    status, corpo = chamar(repo, "POST", "/movimentacao", {"id": produto["id"], "tipo": "saida", "quantidade": 99})
    assert status == 400
    assert "insuficiente" in corpo["erro"]
    assert repo.produtos[produto["id"]]["quantidade"] == 3


def test_movimentacao_sem_id_retorna_400(repo):
    assert chamar(repo, "POST", "/movimentacao", {"tipo": "entrada", "quantidade": 1})[0] == 400


def test_movimentacao_produto_inexistente_retorna_404(repo):
    assert chamar(repo, "POST", "/movimentacao", {"id": "nao-existe", "tipo": "entrada", "quantidade": 1})[0] == 404


def test_historico(repo):
    a = cadastrar(repo, nome="A")
    b = cadastrar(repo, nome="B")
    chamar(repo, "POST", "/movimentacao", {"id": a["id"], "tipo": "entrada", "quantidade": 1})
    chamar(repo, "POST", "/movimentacao", {"id": b["id"], "tipo": "saida", "quantidade": 1})
    _, todas = chamar(repo, "GET", "/movimentacoes")
    assert [m["produto_nome"] for m in todas] == ["B", "A"]
    _, so_a = chamar(repo, "GET", "/movimentacoes", params={"produto_id": a["id"]})
    assert [m["tipo"] for m in so_a] == ["entrada"]


def test_relatorio(repo):
    cadastrar(repo, nome="Caneta", quantidade=3, minimo=5, preco=2.5)
    cadastrar(repo, nome="Caderno", quantidade=10, minimo=2, preco=12)
    status, rel = chamar(repo, "GET", "/relatorio")
    assert status == 200
    assert rel["total_itens"] == 13
    assert rel["valor_total"] == 127.5
    assert [p["nome"] for p in rel["abaixo_do_minimo"]] == ["Caneta"]


def test_remover(repo):
    produto = cadastrar(repo)
    assert chamar(repo, "DELETE", f"/produtos/{produto['id']}") == (204, None)
    assert chamar(repo, "DELETE", f"/produtos/{produto['id']}")[0] == 404


def test_rota_inexistente(repo):
    assert chamar(repo, "GET", "/qualquer")[0] == 404
    assert chamar(repo, "PUT", "/produtos")[0] == 404
