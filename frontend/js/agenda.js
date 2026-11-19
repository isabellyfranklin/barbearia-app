const usuario = Sessao.usuario();
if (!usuario || !["barbeiro", "administrador"].includes(usuario.perfil)) {
  alert("Acesso restrito a barbeiros.");
  window.location.href = "../index.html";
}

const lista = document.getElementById("lista");
const abas = document.querySelectorAll(".abas .btn");

let visao = "hoje";
let agendamentos = [];

const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

const horaDe = (dataHora) => dataHora.slice(11, 16);
const diaDe = (dataHora) => dataHora.slice(0, 10);

const BADGE = {
  pendente: { classe: "pendente", texto: "Pendente" },
  confirmado: { classe: "confirmado", texto: "Confirmado" },
  concluido: { classe: "finalizado", texto: "Finalizado" },
  cancelado: { classe: "cancelado", texto: "Cancelado" },
};

const ACOES = {
  pendente: [
    { status: "confirmado", texto: "Confirmar", classe: "primario" },
    { status: "cancelado", texto: "Cancelar", classe: "perigo" },
  ],
  confirmado: [
    { status: "concluido", texto: "Finalizar", classe: "primario" },
    { status: "cancelado", texto: "Cancelar", classe: "perigo" },
  ],
};

function nomeDoDia(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function itemHTML(ag) {
  const badge = BADGE[ag.status] || { classe: "", texto: ag.status };
  const cliente = ag.cliente?.nome || ag.cliente?.username || "Cliente";
  const botoes = (ACOES[ag.status] || [])
    .map(
      (a) =>
        `<button type="button" class="btn ${a.classe}" data-id="${ag.id}" data-status="${a.status}">${a.texto}</button>`
    )
    .join("");

  return `
    <article class="item">
      <span class="hora">${horaDe(ag.data_hora)}</span>
      <div class="info">
        <strong>${esc(cliente)}</strong>
        <span class="servico">${esc(ag.servico_nome)}${
          usuario.perfil === "administrador" ? ` · ${esc(ag.profissional_nome)}` : ""
        }</span>
      </div>
      <div class="acoes">
        <span class="badge ${badge.classe}">${badge.texto}</span>
        ${botoes}
      </div>
    </article>`;
}

function mostrar() {
  document.getElementById("n-confirmado").textContent =
    agendamentos.filter((a) => a.status === "confirmado").length;
  document.getElementById("n-finalizado").textContent =
    agendamentos.filter((a) => a.status === "concluido").length;
  document.getElementById("n-cancelado").textContent =
    agendamentos.filter((a) => a.status === "cancelado").length;

  if (agendamentos.length === 0) {
    const quando = { hoje: "hoje", semana: "nesta semana", historico: "no período" }[visao];
    lista.innerHTML = `<p class="vazio">Nenhum atendimento ${quando}.</p>`;
    return;
  }

  if (visao === "hoje") {
    lista.innerHTML = agendamentos.map(itemHTML).join("");
    return;
  }

  const porDia = {};
  agendamentos.forEach((ag) => {
    (porDia[diaDe(ag.data_hora)] ||= []).push(ag);
  });

  // Semana em ordem cronológica; histórico do mais recente para o mais antigo
  const dias = Object.keys(porDia).sort();
  if (visao === "historico") dias.reverse();

  lista.innerHTML = dias
    .map((dia) => `<p class="dia">${nomeDoDia(dia)}</p>${porDia[dia].map(itemHTML).join("")}`)
    .join("");
}

function caminhoHistorico() {
  const params = new URLSearchParams();
  const status = document.getElementById("f-status").value;
  const de = document.getElementById("f-de").value;
  const ate = document.getElementById("f-ate").value;
  if (status) params.set("status", status);
  if (de) params.set("from", de);
  if (ate) params.set("to", ate);
  const base = usuario.perfil === "administrador" ? "/admin/history" : "/me/history/professional";
  return params.toString() ? `${base}?${params}` : base;
}

async function carregar() {
  lista.innerHTML = '<p class="vazio">Carregando...</p>';

  const caminhos = {
    hoje: "/me/agenda",
    semana: "/me/agenda/week",
    historico: caminhoHistorico(),
  };

  try {
    const { ok, status, dados } = await api(caminhos[visao]);

    if (status === 401) {
      alert("Sua sessão expirou. Entre novamente.");
      Sessao.limpar();
      window.location.href = "../index.html";
      return;
    }
    if (!ok) {
      lista.innerHTML = `<p class="vazio">${esc(mensagemDeErro(dados))}</p>`;
      return;
    }

    agendamentos = (visao === "semana" ? dados.appointments : dados).sort((a, b) =>
      a.data_hora.localeCompare(b.data_hora)
    );
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
    document.getElementById("filtros").hidden = visao !== "historico";
    carregar();
  });
});

document.getElementById("filtros").addEventListener("submit", (e) => {
  e.preventDefault();
  carregar();
});

lista.addEventListener("click", async (e) => {
  const botao = e.target.closest("button[data-status]");
  if (!botao) return;

  const novoStatus = botao.dataset.status;
  if (novoStatus === "cancelado" && !confirm("Cancelar este atendimento?")) return;

  botao.disabled = true;

  try {
    const { ok, dados } = await api(`/me/agenda/${botao.dataset.id}/status`, {
      method: "PATCH",
      body: { status: novoStatus },
    });

    if (!ok) {
      alert(mensagemDeErro(dados));
      botao.disabled = false;
      return;
    }

    agendamentos = agendamentos.map((a) => (a.id === dados.id ? dados : a));
    mostrar();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
    botao.disabled = false;
  }
});

document.querySelector(".sair").addEventListener("click", sair);

if (usuario) carregar();
