// Dashboard: indicadores (GET /relatorio), reposição e últimas movimentações.
"use strict";

function mostrarIndicadores(r) {
  document.getElementById("i-produtos").textContent = inteiro.format(r.total_produtos);
  document.getElementById("i-itens").textContent = inteiro.format(r.total_itens);
  document.getElementById("i-valor").textContent = moeda.format(r.valor_total);
  document.getElementById("i-criticos").textContent = inteiro.format(r.abaixo_do_minimo.length);
  document.getElementById("i-criticos-bloco").classList.toggle("critico", r.abaixo_do_minimo.length > 0);
}

function mostrarRepor(itens) {
  const lista = document.getElementById("lista-repor");
  lista.replaceChildren(...itens.map((p) => el("li", {},
    el("span", { class: "item-nome", text: p.nome },
      el("span", { class: "item-detalhe", text: `Faltam ${plural(p.minimo - p.quantidade, "unidade", "unidades")} para o mínimo` }),
    ),
    nivelEstoque(p.quantidade, p.minimo),
    el("a", {
      class: "botao claro pequeno",
      href: `movimentacoes.html?produto=${encodeURIComponent(p.id)}&tipo=entrada`,
      text: "Registrar entrada",
    }),
  )));
  document.getElementById("repor-vazio").hidden = itens.length > 0;
  document.getElementById("painel-repor").classList.toggle("tudo-ok", itens.length === 0);
}

function mostrarUltimas(movimentacoes) {
  const lista = document.getElementById("lista-ultimas");
  lista.replaceChildren(...movimentacoes.map((m) => el("li", {},
    el("span", { class: "item-nome", text: m.produto_nome },
      el("span", { class: "item-detalhe", text: dataHora.format(new Date(m.data)) }),
    ),
    el("span", { class: "mov-resumo" },
      el("span", {}, seloTipo(m.tipo), " ", quantidadeComSinal(m)),
      el("span", { class: "item-detalhe", text: `saldo ${inteiro.format(m.saldo)}` }),
    ),
  )));
  document.getElementById("ultimas-vazio").hidden = movimentacoes.length > 0;
}

async function carregar() {
  try {
    const [relatorio, movimentacoes] = await Promise.all([api("/relatorio"), api("/movimentacoes")]);
    mostrarIndicadores(relatorio);
    mostrarRepor(relatorio.abaixo_do_minimo);
    mostrarUltimas(movimentacoes.slice(0, 6));
  } catch (e) {
    avisar(e.message, "erro");
    for (const id of ["repor-vazio", "ultimas-vazio"]) {
      const vazio = document.getElementById(id);
      vazio.textContent = "Não foi possível carregar os dados.";
      vazio.hidden = false;
    }
    document.getElementById("painel-repor").classList.add("tudo-ok");
  }
}

carregar();
