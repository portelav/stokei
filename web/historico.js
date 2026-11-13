// Histórico: movimentações (GET /movimentacoes, com filtro opcional por produto).
"use strict";

const filtroProduto = document.getElementById("filtro-produto");
const filtroTipo = document.getElementById("filtro-tipo");
const corpo = document.getElementById("historico");
const contagem = document.getElementById("contagem");

let movimentacoes = [];

function mostrar() {
  const tipo = filtroTipo.value;
  const visiveis = tipo ? movimentacoes.filter((m) => m.tipo === tipo) : movimentacoes;
  contagem.textContent = plural(visiveis.length, "movimentação", "movimentações");
  document.getElementById("nota-limite").hidden = movimentacoes.length < LIMITE_HISTORICO;

  if (visiveis.length === 0) {
    const filtrando = filtroProduto.value || tipo;
    linhaVazia(corpo, 5, filtrando ? "Nenhuma movimentação com esses filtros." : "Nenhuma movimentação registrada ainda.");
    return;
  }
  corpo.replaceChildren(...visiveis.map((m) => el("tr", {},
    celula(dataHora.format(new Date(m.data)), "Data e hora"),
    celula(el("span", { class: "nome-produto", text: m.produto_nome }), "Produto", "principal"),
    celula(seloTipo(m.tipo), "Tipo"),
    celula(quantidadeComSinal(m), "Quantidade", "num"),
    celula(inteiro.format(m.saldo), "Saldo depois", "num"),
  )));
}

async function carregar() {
  const id = filtroProduto.value;
  try {
    movimentacoes = await api("/movimentacoes" + (id ? "?produto_id=" + encodeURIComponent(id) : ""));
    mostrar();
  } catch (e) {
    avisar(e.message, "erro");
    linhaVazia(corpo, 5, "Não foi possível carregar o histórico.");
  }
}

async function iniciar() {
  try {
    const produtos = await api("/produtos");
    filtroProduto.append(...produtos.map((p) => new Option(rotuloProduto(p), p.id)));
    const pedido = parametro("produto");
    if (pedido && produtos.some((p) => p.id === pedido)) filtroProduto.value = pedido;
  } catch (e) {
    avisar(e.message, "erro");
    linhaVazia(corpo, 5, "Não foi possível carregar o histórico.");
    return;
  }
  await carregar();
}

filtroProduto.addEventListener("change", carregar);
filtroTipo.addEventListener("change", mostrar);

iniciar();
