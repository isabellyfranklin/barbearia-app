const usuario = Sessao.usuario();
if (!usuario || usuario.perfil !== "cliente") {
  alert("Acesso restrito a clientes.");
  window.location.href = "../index.html";
}

const lista = document.getElementById("lista");
const abas = document.querySelectorAll(".abas button[data-visao]");
const filtros = document.getElementById("filtros");

let visao = "proximos";
let agendamentos = [];

const moeda = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
const doisDigitos = (n) => String(n).padStart(2, "0");
const hojeISO = () => {
  const d = new Date();
  return `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`;
};

const BADGE = {
  pendente: { classe: "pendente", texto: "Pendente" },
  confirmado: { classe: "confirmado", texto: "Confirmado" },
  concluido: { classe: "finalizado", texto: "Finalizado" },
  cancelado: { classe: "cancelado", texto: "Cancelado" },
};

const ATIVOS = ["pendente", "confirmado"];

function dataLegivel(dataHora) {
  const [a, m, d] = dataHora.slice(0, 10).split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("pt-BR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  });
}

const podeCancelar = (ag) => ATIVOS.includes(ag.status) && new Date(ag.data_hora) > new Date();

function itemHTML(ag) {
  const badge = BADGE[ag.status] || { classe: "", texto: ag.status };
  return `
    <article class="item">
      <span class="hora">${ag.data_hora.slice(11, 16)}</span>
      <div class="info">
        <strong>${esc(ag.servico_nome)}</strong>
        <span class="servico">${dataLegivel(ag.data_hora)} · ${esc(ag.profissional_nome)} · ${moeda(ag.preco)}</span>
      </div>
      <div class="acoes">
        <span class="badge ${badge.classe}">${badge.texto}</span>
        ${podeCancelar(ag)
          ? `<button type="button" class="btn perigo" data-cancelar="${ag.id}">Cancelar</button>`
          : ""}
      </div>
    </article>`;
}

function mostrar() {
  if (agendamentos.length === 0) {
    lista.innerHTML =
      visao === "proximos"
        ? '<p class="vazio">Você não tem agendamentos futuros. <a href="agendamento.html" style="color: var(--dourado)">Agende agora</a>.</p>'
        : '<p class="vazio">Nenhum agendamento encontrado.</p>';
    return;
  }
  lista.innerHTML = agendamentos.map(itemHTML).join("");
}

function sessaoExpirada() {
  alert("Sua sessão expirou. Entre novamente.");
  Sessao.limpar();
  window.location.href = "../index.html";
}

async function carregar() {
  lista.innerHTML = '<p class="vazio">Carregando...</p>';

  let caminho;
  if (visao === "proximos") {
    caminho = `/appointments?from=${hojeISO()}`;
  } else {
    const params = new URLSearchParams();
    const status = document.getElementById("f-status").value;
    const de = document.getElementById("f-de").value;
    const ate = document.getElementById("f-ate").value;
    if (status) params.set("status", status);
    if (de) params.set("from", de);
    if (ate) params.set("to", ate);
    caminho = `/me/history${params.toString() ? `?${params}` : ""}`;
  }

  try {
    const { ok, status, dados } = await api(caminho);
    if (status === 401) return sessaoExpirada();
    if (!ok) {
      lista.innerHTML = `<p class="vazio">${esc(mensagemDeErro(dados))}</p>`;
      return;
    }

    if (visao === "proximos") {
      const agora = new Date();
      agendamentos = dados
        .filter((a) => ATIVOS.includes(a.status) && new Date(a.data_hora) > agora)
        .sort((a, b) => a.data_hora.localeCompare(b.data_hora));
    } else {
      agendamentos = dados.sort((a, b) => b.data_hora.localeCompare(a.data_hora));
    }
    mostrar();
  } catch (erro) {
    console.error(erro);
    lista.innerHTML = '<p class="vazio">Não foi possível conectar ao servidor.</p>';
  }
}

abas.forEach((aba) => {
  aba.addEventListener("click", () => {
    abas.forEach((a) => a.classList.remove("ativo"));
    aba.classList.add("ativo");
    visao = aba.dataset.visao;
    filtros.hidden = visao !== "historico";
    carregar();
  });
});

filtros.addEventListener("submit", (e) => {
  e.preventDefault();
  carregar();
});

lista.addEventListener("click", async (e) => {
  const botao = e.target.closest("button[data-cancelar]");
  if (!botao) return;
  if (!confirm("Cancelar este agendamento? O horário ficará livre para outros clientes.")) return;

  botao.disabled = true;
  try {
    const { ok, status, dados } = await api(`/appointments/${botao.dataset.cancelar}/cancel`, {
      method: "PATCH",
    });
    if (status === 401) return sessaoExpirada();
    if (!ok) {
      alert(mensagemDeErro(dados));
      botao.disabled = false;
      return;
    }
    carregar();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
    botao.disabled = false;
  }
});

document.querySelector(".sair").addEventListener("click", sair);

if (usuario) carregar();
