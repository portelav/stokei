// Funções usadas por todas as páginas: chamada à API, avisos e montagem da tela.
"use strict";

const LIMITE_HISTORICO = 50; // a API devolve no máximo 50 movimentações

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const inteiro = new Intl.NumberFormat("pt-BR");
const dataHora = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

const TIPOS = { entrada: "Entrada", saida: "Saída" };

// Cria um elemento. O texto sempre entra como texto (textContent / nós de texto),
// nunca como HTML: o que o usuário digita não vira código na página (evita XSS).
function el(tag, attrs = {}, ...filhos) {
  const elemento = document.createElement(tag);
  for (const [nome, valor] of Object.entries(attrs)) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (nome === "class") elemento.className = valor;
    else if (nome === "text") elemento.textContent = valor;
    else elemento.setAttribute(nome, valor === true ? "" : valor);
  }
  elemento.append(...filhos.flat().filter((f) => f !== null && f !== undefined && f !== false));
  return elemento;
}

function plural(n, singular, pluralTexto) {
  return `${inteiro.format(n)} ${n === 1 ? singular : pluralTexto}`;
}

function parametro(nome) {
  return new URLSearchParams(location.search).get(nome);
}

// ---------- Status da API (canto do menu) ----------

const statusApi = document.getElementById("status-api");

function marcarApi(conectada) {
  if (!statusApi) return;
  statusApi.classList.toggle("on", conectada);
  statusApi.classList.toggle("off", !conectada);
  statusApi.querySelector(".texto").textContent = conectada ? "API conectada" : "API fora do ar";
}

// Chama a API e devolve o JSON. Em caso de erro, lança a mensagem enviada pela API.
async function api(caminho, opcoes = {}) {
  let resp;
  try {
    resp = await fetch(API_URL + caminho, {
      ...opcoes,
      headers: opcoes.body ? { "Content-Type": "application/json" } : undefined,
    });
  } catch {
    marcarApi(false);
    throw new Error(`Sem conexão com a API (${API_URL}). Confira se ela está no ar e recarregue a página.`);
  }
  marcarApi(true);
  if (resp.status === 204) return null;
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(corpo.erro || `A API respondeu com erro ${resp.status}.`);
  return corpo;
}

// ---------- Avisos de sucesso e erro ----------

const caixaAvisos = document.getElementById("avisos");

function avisar(texto, tipo = "sucesso") {
  const aviso = el("div", { class: `aviso ${tipo}`, role: tipo === "erro" ? "alert" : null, text: texto });
  caixaAvisos.append(aviso);
  setTimeout(() => aviso.remove(), tipo === "erro" ? 8000 : 4500);
}

// ---------- Peças de tela reaproveitadas ----------

// Nível de estoque: quantidade, mínimo e uma barra com a marca do mínimo.
function nivelEstoque(quantidade, minimo) {
  const escala = Math.max(quantidade, minimo * 2, 1);
  const baixo = quantidade < minimo;
  return el("div", { class: "nivel" + (baixo ? " baixo" : "") },
    el("span", { class: "nivel-numeros" },
      el("strong", { text: inteiro.format(quantidade) }),
      ` / mín. ${inteiro.format(minimo)}`,
    ),
    el("div", { class: "nivel-barra", "aria-hidden": "true" },
      el("span", { class: "cheio", style: `width: ${(quantidade / escala) * 100}%` }),
      minimo > 0 ? el("span", { class: "minimo", style: `left: calc(${(minimo / escala) * 100}% - 1px)` }) : null,
    ),
  );
}

function seloTipo(tipo) {
  return el("span", { class: `selo ${tipo}`, text: TIPOS[tipo] || tipo });
}

function quantidadeComSinal(m) {
  const sinal = m.tipo === "entrada" ? "+" : "−";
  return el("span", { class: `qtd-${m.tipo}`, text: sinal + inteiro.format(m.quantidade) });
}

// Célula de tabela. "rotulo" aparece no celular, quando a tabela vira cartões.
function celula(conteudo, rotulo, classe) {
  return el("td", { class: classe, "data-rotulo": rotulo }, conteudo);
}

function linhaVazia(corpo, colunas, ...conteudo) {
  corpo.replaceChildren(el("tr", {}, el("td", { colspan: colunas, class: "vazio vazio-linha" }, ...conteudo)));
}

function rotuloProduto(p) {
  return p.codigo ? `${p.nome} (${p.codigo})` : p.nome;
}
