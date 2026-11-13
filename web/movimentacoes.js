// Movimentações: entrada e saída (POST /movimentacao) com prévia do saldo.
"use strict";

const form = document.getElementById("form-movimentacao");
const selectProduto = document.getElementById("produto");
const campoQuantidade = document.getElementById("quantidade");
const botaoRegistrar = document.getElementById("botao-registrar");
const previa = document.getElementById("previa");
const previaAviso = document.getElementById("previa-aviso");

let produtos = [];

function produtoAtual() {
  return produtos.find((p) => p.id === selectProduto.value);
}

function tipoAtual() {
  return form.elements.tipo.value;
}

async function carregarProdutos(manterId) {
  produtos = await api("/produtos");
  const vazio = produtos.length === 0;
  form.hidden = vazio;
  document.getElementById("sem-produtos").hidden = !vazio;
  document.getElementById("painel-recentes").hidden = vazio;
  if (vazio) return;

  selectProduto.replaceChildren(...produtos.map((p) =>
    new Option(`${rotuloProduto(p)}, saldo ${inteiro.format(p.quantidade)}`, p.id)));
  const desejado = manterId || parametro("produto");
  if (desejado && produtos.some((p) => p.id === desejado)) selectProduto.value = desejado;
}

function atualizarPrevia() {
  const p = produtoAtual();
  if (!p) return;
  const tipo = tipoAtual();
  const q = Number(campoQuantidade.value);
  const valida = Number.isInteger(q) && q > 0;
  const apos = tipo === "entrada" ? p.quantidade + q : p.quantidade - q;

  document.getElementById("saldo-atual").textContent = inteiro.format(p.quantidade);
  document.getElementById("saldo-minimo").textContent = inteiro.format(p.minimo);
  document.getElementById("saldo-apos").textContent = valida ? inteiro.format(apos) : "–";
  botaoRegistrar.textContent = tipo === "entrada" ? "Registrar entrada" : "Registrar saída";

  // Só avisa. Quem recusa a saída maior que o saldo é a API.
  const insuficiente = valida && apos < 0;
  const ficaBaixo = valida && !insuficiente && apos < p.minimo;
  previa.classList.toggle("invalida", insuficiente);
  previaAviso.classList.toggle("leve", ficaBaixo);
  previaAviso.hidden = !insuficiente && !ficaBaixo;
  previaAviso.textContent = insuficiente
    ? `A saída é maior que o saldo atual (${inteiro.format(p.quantidade)}). A API vai recusar.`
    : ficaBaixo ? "Depois desta movimentação o produto fica abaixo do mínimo." : "";
}

async function carregarRecentes() {
  const p = produtoAtual();
  if (!p) return;
  document.getElementById("recentes-produto").textContent = rotuloProduto(p);
  document.getElementById("link-historico").href = `historico.html?produto=${encodeURIComponent(p.id)}`;

  const movimentacoes = (await api(`/movimentacoes?produto_id=${encodeURIComponent(p.id)}`)).slice(0, 8);
  document.getElementById("lista-recentes").replaceChildren(...movimentacoes.map((m) => el("li", {},
    el("span", { class: "item-nome", text: dataHora.format(new Date(m.data)) }),
    el("span", { class: "mov-resumo" },
      el("span", {}, seloTipo(m.tipo), " ", quantidadeComSinal(m)),
      el("span", { class: "item-detalhe", text: `saldo ${inteiro.format(m.saldo)}` }),
    ),
  )));
  document.getElementById("recentes-vazio").hidden = movimentacoes.length > 0;
}

async function trocarProduto() {
  atualizarPrevia();
  try {
    await carregarRecentes();
  } catch (e) {
    avisar(e.message, "erro");
  }
}

selectProduto.addEventListener("change", trocarProduto);
campoQuantidade.addEventListener("input", atualizarPrevia);
form.addEventListener("change", (ev) => {
  if (ev.target.name === "tipo") atualizarPrevia();
});

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const p = produtoAtual();
  const tipo = tipoAtual();
  const q = Number(campoQuantidade.value);
  botaoRegistrar.disabled = true;
  try {
    const atualizado = await api("/movimentacao", {
      method: "POST",
      body: JSON.stringify({ id: p.id, tipo, quantidade: q }),
    });
    avisar(`${TIPOS[tipo]} de ${inteiro.format(q)} registrada em "${atualizado.nome}". Saldo agora: ${inteiro.format(atualizado.quantidade)}.`);
    campoQuantidade.value = 1;
    await carregarProdutos(p.id);
    await trocarProduto();
  } catch (e) {
    avisar(e.message, "erro");
  } finally {
    botaoRegistrar.disabled = false;
  }
});

async function iniciar() {
  if (parametro("tipo") === "saida") form.elements.tipo.value = "saida";
  try {
    await carregarProdutos();
  } catch (e) {
    avisar(e.message, "erro");
    return;
  }
  await trocarProduto();
}

iniciar();
