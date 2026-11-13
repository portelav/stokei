"""Regras de negócio do estoque.

Funções puras, sem dependência do Azure, para poderem ser testadas localmente.
"""


class ErroValidacao(Exception):
    """Entrada inválida enviada pelo usuário (vira HTTP 400)."""


def _inteiro_nao_negativo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ErroValidacao(f"'{campo}' deve ser um número inteiro maior ou igual a zero")
    return valor


def _texto_opcional(valor, campo, maximo):
    if valor is None:
        return ""
    if not isinstance(valor, str):
        raise ErroValidacao(f"'{campo}' deve ser um texto")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ErroValidacao(f"'{campo}' deve ter no máximo {maximo} caracteres")
    return valor


def validar_produto(dados):
    """Valida o corpo de um cadastro de produto e devolve os campos normalizados."""
    if not isinstance(dados, dict):
        raise ErroValidacao("Corpo da requisição deve ser um objeto JSON")

    nome = dados.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        raise ErroValidacao("'nome' é obrigatório")
    nome = nome.strip()
    if len(nome) > 100:
        raise ErroValidacao("'nome' deve ter no máximo 100 caracteres")

    codigo = _texto_opcional(dados.get("codigo"), "codigo", 30)
    categoria = _texto_opcional(dados.get("categoria"), "categoria", 50)

    quantidade = _inteiro_nao_negativo(dados.get("quantidade", 0), "quantidade")
    minimo = _inteiro_nao_negativo(dados.get("minimo", 0), "minimo")

    preco = dados.get("preco", 0)
    if isinstance(preco, bool) or not isinstance(preco, (int, float)) or preco < 0:
        raise ErroValidacao("'preco' deve ser um número maior ou igual a zero")

    return {
        "codigo": codigo,
        "nome": nome,
        "categoria": categoria,
        "quantidade": quantidade,
        "minimo": minimo,
        "preco": float(preco),
    }


def verificar_codigo_unico(produtos, codigo):
    """Impede dois produtos com o mesmo código (sem diferenciar maiúsculas). Código vazio é permitido."""
    if codigo and any(p.get("codigo", "").lower() == codigo.lower() for p in produtos):
        raise ErroValidacao(f"Já existe um produto com o código '{codigo}'")


def aplicar_movimentacao(quantidade_atual, tipo, quantidade):
    """Calcula o novo saldo após uma entrada ou saída. Saldo nunca fica negativo."""
    if tipo not in ("entrada", "saida"):
        raise ErroValidacao("'tipo' deve ser 'entrada' ou 'saida'")
    if isinstance(quantidade, bool) or not isinstance(quantidade, int) or quantidade <= 0:
        raise ErroValidacao("'quantidade' deve ser um número inteiro maior que zero")

    if tipo == "entrada":
        return quantidade_atual + quantidade
    if quantidade > quantidade_atual:
        raise ErroValidacao(
            f"Estoque insuficiente: saldo atual {quantidade_atual}, saída solicitada {quantidade}"
        )
    return quantidade_atual - quantidade


def filtrar_produtos(produtos, termo):
    """Busca por nome, código ou categoria, sem diferenciar maiúsculas. Termo vazio devolve tudo."""
    termo = (termo or "").strip().lower()
    if not termo:
        return list(produtos)
    return [
        p for p in produtos
        if termo in p["nome"].lower()
        or termo in p.get("codigo", "").lower()
        or termo in p.get("categoria", "").lower()
    ]


def em_alerta(produto):
    """Produto está em alerta quando a quantidade fica abaixo do mínimo."""
    return produto["quantidade"] < produto["minimo"]


def gerar_relatorio(produtos):
    """Resumo do estoque: totais, valor e produtos abaixo do mínimo."""
    abaixo = [p for p in produtos if em_alerta(p)]
    return {
        "total_produtos": len(produtos),
        "total_itens": sum(p["quantidade"] for p in produtos),
        "valor_total": round(sum(p["quantidade"] * p["preco"] for p in produtos), 2),
        "abaixo_do_minimo": [
            {
                "id": p["id"],
                "codigo": p.get("codigo", ""),
                "nome": p["nome"],
                "quantidade": p["quantidade"],
                "minimo": p["minimo"],
            }
            for p in sorted(abaixo, key=lambda p: p["nome"].lower())
        ],
    }
