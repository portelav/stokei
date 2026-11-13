import pytest

import estoque
from estoque import ErroValidacao


def produto(nome="Caneta", quantidade=10, minimo=5, preco=2.0, id="1", codigo="", categoria=""):
    return {"id": id, "codigo": codigo, "nome": nome, "categoria": categoria,
            "quantidade": quantidade, "minimo": minimo, "preco": preco}


class TestValidarProduto:
    def test_normaliza_campos(self):
        dados = {"codigo": " CAN-01 ", "nome": "  Caneta ", "categoria": " Papelaria ",
                 "quantidade": 3, "minimo": 1, "preco": 2}
        assert estoque.validar_produto(dados) == {
            "codigo": "CAN-01",
            "nome": "Caneta",
            "categoria": "Papelaria",
            "quantidade": 3,
            "minimo": 1,
            "preco": 2.0,
        }

    def test_valores_padrao(self):
        assert estoque.validar_produto({"nome": "Caneta"}) == {
            "codigo": "",
            "nome": "Caneta",
            "categoria": "",
            "quantidade": 0,
            "minimo": 0,
            "preco": 0.0,
        }

    @pytest.mark.parametrize(
        "dados",
        [
            None,
            [],
            {},
            {"nome": "   "},
            {"nome": "x" * 101},
            {"nome": "Caneta", "quantidade": -1},
            {"nome": "Caneta", "quantidade": 1.5},
            {"nome": "Caneta", "quantidade": "3"},
            {"nome": "Caneta", "quantidade": True},
            {"nome": "Caneta", "minimo": -2},
            {"nome": "Caneta", "preco": -0.01},
            {"nome": "Caneta", "preco": "10"},
            {"nome": "Caneta", "codigo": 123},
            {"nome": "Caneta", "codigo": "x" * 31},
            {"nome": "Caneta", "categoria": ["a"]},
            {"nome": "Caneta", "categoria": "x" * 51},
        ],
    )
    def test_rejeita_entrada_invalida(self, dados):
        with pytest.raises(ErroValidacao):
            estoque.validar_produto(dados)


class TestCodigoUnico:
    def test_codigo_repetido_e_recusado_sem_diferenciar_maiusculas(self):
        with pytest.raises(ErroValidacao, match="código"):
            estoque.verificar_codigo_unico([produto(codigo="CAN-01")], "can-01")

    def test_codigo_novo_e_aceito(self):
        estoque.verificar_codigo_unico([produto(codigo="CAN-01")], "CAN-02")

    def test_codigo_vazio_pode_repetir(self):
        estoque.verificar_codigo_unico([produto(codigo="")], "")


class TestAplicarMovimentacao:
    def test_entrada_soma(self):
        assert estoque.aplicar_movimentacao(5, "entrada", 3) == 8

    def test_saida_subtrai(self):
        assert estoque.aplicar_movimentacao(5, "saida", 5) == 0

    def test_saida_maior_que_saldo_e_bloqueada(self):
        with pytest.raises(ErroValidacao, match="insuficiente"):
            estoque.aplicar_movimentacao(5, "saida", 6)

    @pytest.mark.parametrize("quantidade", [0, -1, 1.5, "2", True, None])
    def test_quantidade_invalida(self, quantidade):
        with pytest.raises(ErroValidacao):
            estoque.aplicar_movimentacao(5, "entrada", quantidade)

    def test_tipo_invalido(self):
        with pytest.raises(ErroValidacao):
            estoque.aplicar_movimentacao(5, "transferencia", 1)


class TestFiltrarProdutos:
    def test_busca_parcial_sem_diferenciar_maiusculas(self):
        produtos = [produto("Caneta Azul", id="a"), produto("Caderno", id="b"), produto("Lápis", id="c")]
        assert [p["id"] for p in estoque.filtrar_produtos(produtos, "  CA ")] == ["a", "b"]

    @pytest.mark.parametrize("termo", [None, "", "   "])
    def test_termo_vazio_devolve_tudo(self, termo):
        produtos = [produto(id="a"), produto(id="b")]
        assert estoque.filtrar_produtos(produtos, termo) == produtos

    def test_busca_por_codigo_e_categoria(self):
        produtos = [produto("Caneta", id="a", codigo="CAN-01", categoria="Papelaria"),
                    produto("Arroz", id="b", codigo="ARZ-05", categoria="Mercearia")]
        assert [p["id"] for p in estoque.filtrar_produtos(produtos, "arz")] == ["b"]
        assert [p["id"] for p in estoque.filtrar_produtos(produtos, "papel")] == ["a"]

    def test_sem_resultado(self):
        assert estoque.filtrar_produtos([produto()], "xyz") == []


class TestRelatorio:
    def test_alerta_quando_abaixo_do_minimo(self):
        assert estoque.em_alerta(produto(quantidade=4, minimo=5))
        assert not estoque.em_alerta(produto(quantidade=5, minimo=5))

    def test_relatorio(self):
        produtos = [
            produto("Lápis", quantidade=2, minimo=5, preco=1.5, id="a"),
            produto("Caderno", quantidade=10, minimo=3, preco=12.0, id="b"),
            produto("Borracha", quantidade=0, minimo=1, preco=0.5, id="c"),
        ]
        rel = estoque.gerar_relatorio(produtos)
        assert rel["total_produtos"] == 3
        assert rel["total_itens"] == 12
        assert rel["valor_total"] == 123.0
        assert [p["nome"] for p in rel["abaixo_do_minimo"]] == ["Borracha", "Lápis"]

    def test_relatorio_vazio(self):
        assert estoque.gerar_relatorio([]) == {
            "total_produtos": 0,
            "total_itens": 0,
            "valor_total": 0,
            "abaixo_do_minimo": [],
        }
