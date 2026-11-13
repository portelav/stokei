// Produtos: cadastro (POST /produtos), busca (GET /produtos?busca=) e remoção (DELETE).
"use strict";

const painelCadastro = document.getElementById("cadastro");
const botaoAbrir = document.getElementById("abrir-cadastro");
const formProduto = document.getElementById("form-produto");
const campoBusca = document.getElementById("busca");
const soBaixos = document.getElementById("so-baixos");
const lista = document.getElementById("lista");
const contagem = document.getElementById("contagem");

let produtos = []; // resultado da busca atual
let primeiraCarga = true;

function abrirCadastro(abrir) {
  painelCadastro.hidden = !abrir;
  botaoAbrir.setAttribute("aria-expanded", String(abrir));
  if (abrir) formProduto.elements.codigo.focus();
}

function botaoRemover(p) {
  const botao = el("button", { type: "button", class: "acao-texto perigo", text: "Remover" });
  let espera;
  botao.addEventListener("click", async () => {
    // Primeiro clique pede confirmação; o segundo remove.
    if (!botao.classList.contains("confirmar")) {
      botao.classList.add("confirmar");
      botao.textContent = "Confirmar remoção";
      espera = setTimeout(() => {
        botao.classList.remove("confirmar");
        botao.textContent = "Remover";
      }, 4000);
      return;
    }
    clearTimeout(espera);
    botao.disabled = true;
    try {
      await api(`/produtos/${encodeURIComponent(p.id)}`, { method: "DELETE" });
      avisar(`Produto "${p.nome}" removido.`);
      await carregar();
    } catch (e) {
      avisar(e.message, "erro");
      botao.disabled = false;
    }
  });
  return botao;
}

function linhaProduto(p) {
  return el("tr", { class: p.alerta ? "baixo" : null },
    celula(p.codigo ? el("span", { class: "etiqueta", text: p.codigo }) : el("span", { class: "sem-codigo", text: "sem código" }), "Código"),
    celula(el("span", { class: "nome-produto", text: p.nome }, p.categoria ? el("small", { text: p.categoria }) : null), "Produto", "principal"),
    celula(nivelEstoque(p.quantidade, p.minimo), "Estoque"),
    celula(moeda.format(p.preco), "Preço", "num"),
    celula(moeda.format(p.quantidade * p.preco), "Valor em estoque", "num"),
    celula(el("span", { class: `selo ${p.alerta ? "baixo" : "ok"}`, text: p.alerta ? "Abaixo do mínimo" : "Em dia" }), "Situação"),
    celula(el("div", { class: "acoes-linha" },
      el("a", { class: "acao-texto", href: `movimentacoes.html?produto=${encodeURIComponent(p.id)}`, text: "Movimentar" }),
      botaoRemover(p),
    ), "Ações", "acoes"),
  );
}

function mostrar() {
  const visiveis = soBaixos.checked ? produtos.filter((p) => p.alerta) : produtos;
  const termo = campoBusca.value.trim();
  contagem.textContent = plural(visiveis.length, "produto", "produtos");

  if (visiveis.length > 0) {
    lista.replaceChildren(...visiveis.map(linhaProduto));
  } else if (termo) {
    linhaVazia(lista, 7, `Nenhum produto encontrado para "${termo}".`);
  } else if (soBaixos.checked) {
    linhaVazia(lista, 7, "Nenhum produto abaixo do mínimo.");
  } else {
    const botao = el("button", { type: "button", class: "acao-texto", text: "Cadastre o primeiro" });
    botao.addEventListener("click", () => abrirCadastro(true));
    linhaVazia(lista, 7, "Nenhum produto cadastrado ainda. ", botao);
  }
}

function atualizarCategorias() {
  const categorias = [...new Set(produtos.map((p) => p.categoria).filter(Boolean))].sort();
  document.getElementById("categorias").replaceChildren(...categorias.map((c) => el("option", { value: c })));
}

async function carregar() {
  const termo = campoBusca.value.trim();
  try {
    produtos = await api("/produtos" + (termo ? "?busca=" + encodeURIComponent(termo) : ""));
    if (!termo) atualizarCategorias();
    mostrar();
    if (primeiraCarga && !termo && produtos.length === 0) abrirCadastro(true);
  } catch (e) {
    avisar(e.message, "erro");
    linhaVazia(lista, 7, "Não foi possível carregar os produtos.");
  }
  primeiraCarga = false;
}

botaoAbrir.addEventListener("click", () => abrirCadastro(painelCadastro.hidden));
document.getElementById("fechar-cadastro").addEventListener("click", () => abrirCadastro(false));

let esperaBusca;
campoBusca.addEventListener("input", () => {
  clearTimeout(esperaBusca);
  esperaBusca = setTimeout(carregar, 300);
});
soBaixos.addEventListener("change", mostrar);

formProduto.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(formProduto);
  const botao = formProduto.querySelector("button[type=submit]");
  botao.disabled = true;
  try {
    const novo = await api("/produtos", {
      method: "POST",
      body: JSON.stringify({
        codigo: f.get("codigo"),
        nome: f.get("nome"),
        categoria: f.get("categoria"),
        quantidade: Number(f.get("quantidade")),
        minimo: Number(f.get("minimo")),
        preco: Number(f.get("preco")),
      }),
    });
    avisar(`Produto "${novo.nome}" cadastrado.`);
    formProduto.reset();
    formProduto.elements.codigo.focus();
    await carregar();
  } catch (e) {
    avisar(e.message, "erro");
  } finally {
    botao.disabled = false;
  }
});

carregar();
