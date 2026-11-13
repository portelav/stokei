// Endereço da API (Cloud Run functions), sem barra no final.
// O scripts/deploy.sh preenche esta linha automaticamente.
// Local (functions-framework): http://localhost:8080
const API_URL = "http://localhost:8080";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const mensagem = document.getElementById("mensagem");

function avisar(texto, tipo) {
  mensagem.textContent = texto;
  mensagem.className = tipo;
}

// Chama a API e devolve o JSON da resposta; em caso de erro, lança a mensagem enviada pela API.
async function api(caminho, opcoes = {}) {
  const resp = await fetch(API_URL + caminho, {
    ...opcoes,
    headers: { "Content-Type": "application/json" },
  });
  if (resp.status === 204) return null;
  const corpo = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(corpo.erro || `Erro ${resp.status}`);
  return corpo;
}

// Sempre textContent (nunca innerHTML): o texto digitado pelo usuário não vira HTML (evita XSS).
function celula(texto, classe) {
  const td = document.createElement("td");
  td.textContent = texto;
  if (classe) td.className = classe;
  return td;
}

function linhaVazia(corpo, texto, colunas) {
  const tr = document.createElement("tr");
  const td = celula(texto);
  td.colSpan = colunas;
  tr.append(td);
  corpo.append(tr);
}

function renderizarProdutos(produtos) {
  const lista = document.getElementById("lista");
  lista.replaceChildren();

  for (const p of produtos) {
    const tr = document.createElement("tr");
    if (p.alerta) tr.className = "alerta";
    tr.append(
      celula(p.codigo || "—", "codigo"),
      celula(p.nome),
      celula(p.categoria || "—"),
      celula(p.quantidade),
      celula(p.minimo),
      celula(moeda.format(p.preco)),
    );

    const situacao = document.createElement("td");
    const tag = document.createElement("span");
    tag.className = "tag " + (p.alerta ? "alerta" : "ok");
    tag.textContent = p.alerta ? "Abaixo do mínimo" : "OK";
    situacao.append(tag);

    const acoes = document.createElement("td");
    const remover = document.createElement("button");
    remover.className = "secundario";
    remover.textContent = "Remover";
    remover.addEventListener("click", () => removerProduto(p));
    acoes.append(remover);

    tr.append(situacao, acoes);
    lista.append(tr);
  }

  if (produtos.length === 0) linhaVazia(lista, "Nenhum produto encontrado.", 8);
}

function renderizarRelatorio(r) {
  document.getElementById("r-produtos").textContent = r.total_produtos;
  document.getElementById("r-itens").textContent = r.total_itens;
  document.getElementById("r-valor").textContent = moeda.format(r.valor_total);
  document.getElementById("r-alertas").textContent = r.abaixo_do_minimo.length;
}

function renderizarOpcoes(produtos) {
  const select = document.querySelector("#form-movimentacao select[name=id]");
  const selecionado = select.value;
  select.replaceChildren(...produtos.map((p) => {
    const rotulo = `${p.codigo ? p.codigo + " · " : ""}${p.nome} (saldo ${p.quantidade})`;
    return new Option(rotulo, p.id);
  }));
  if (produtos.some((p) => p.id === selecionado)) select.value = selecionado;
}

function renderizarHistorico(movimentacoes) {
  const corpo = document.getElementById("historico");
  corpo.replaceChildren();
  for (const m of movimentacoes) {
    const tr = document.createElement("tr");
    tr.append(
      celula(new Date(m.data).toLocaleString("pt-BR")),
      celula(m.produto_nome),
      celula(m.tipo === "entrada" ? "Entrada" : "Saída"),
      celula(m.quantidade),
      celula(m.saldo),
    );
    corpo.append(tr);
  }
  if (movimentacoes.length === 0) linhaVazia(corpo, "Nenhuma movimentação registrada.", 5);
}

// Busca tudo de novo na API e redesenha a tela.
async function atualizar() {
  const busca = document.getElementById("busca").value.trim();
  const filtro = busca ? "?busca=" + encodeURIComponent(busca) : "";
  try {
    const [todos, filtrados, relatorio, historico] = await Promise.all([
      api("/produtos"),
      filtro ? api("/produtos" + filtro) : null,
      api("/relatorio"),
      api("/movimentacoes"),
    ]);
    renderizarOpcoes(todos);
    renderizarProdutos(filtrados ?? todos);
    renderizarRelatorio(relatorio);
    renderizarHistorico(historico);
  } catch (e) {
    avisar("Não foi possível carregar os dados: " + e.message, "erro");
  }
}

async function removerProduto(p) {
  try {
    await api("/produtos/" + encodeURIComponent(p.id), { method: "DELETE" });
    avisar(`Produto "${p.nome}" removido.`, "sucesso");
    await atualizar();
  } catch (e) {
    avisar(e.message, "erro");
  }
}

let esperaBusca;
document.getElementById("busca").addEventListener("input", () => {
  clearTimeout(esperaBusca);
  esperaBusca = setTimeout(atualizar, 300);
});

document.getElementById("form-produto").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  try {
    await api("/produtos", {
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
    ev.target.reset();
    avisar("Produto cadastrado.", "sucesso");
    await atualizar();
  } catch (e) {
    avisar(e.message, "erro");
  }
});

document.getElementById("form-movimentacao").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  try {
    await api("/movimentacao", {
      method: "POST",
      body: JSON.stringify({
        id: f.get("id"),
        tipo: f.get("tipo"),
        quantidade: Number(f.get("quantidade")),
      }),
    });
    avisar("Movimentação registrada.", "sucesso");
    await atualizar();
  } catch (e) {
    avisar(e.message, "erro");
  }
});

atualizar();
