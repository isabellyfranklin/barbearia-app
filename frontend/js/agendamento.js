const usuario = Sessao.usuario();
if (!usuario) {
  alert("Faça login para agendar.");
  window.location.href = "../index.html";
}

let servicos = [];
let barbeiros = [];
let horarios = [];

// O que a pessoa já escolheu
const estado = { servico: null, barbeiro: null, data: null, hora: null };

const moeda = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const doisDigitos = (n) => String(n).padStart(2, "0");
const horaDoSlot = (slot) => slot.slice(11, 16);

const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

// ---------- Dias e horários ----------
const hoje = new Date();
const dias = [];
for (let i = 0; i < 7; i++) {
  dias.push(new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + i));
}

const iso = (d) => `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`;

async function carregarDados() {
  try {
    const [barbearia, respServicos, respBarbeiros] = await Promise.all([
      api("/barbershop", { auth: false }),
      api("/services", { auth: false }),
      api("/professionals", { auth: false }),
    ]);

    if (barbearia.ok && barbearia.dados) {
      document.getElementById("nome-barbearia").textContent = barbearia.dados.nome;
    }
    servicos = respServicos.ok ? respServicos.dados : [];
    barbeiros = respBarbeiros.ok ? respBarbeiros.dados : [];
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor. O backend está rodando?");
  }
  atualizarTudo();
}

let ultimaBusca = 0;
async function carregarHorarios() {
  horarios = [];
  if (!estado.servico || !estado.barbeiro || !estado.data) return;

  const minhaBusca = ++ultimaBusca;
  document.getElementById("lista-horarios").innerHTML = '<p class="aviso">Carregando horários...</p>';

  let resultado = [];
  try {
    const { ok, dados } = await api(
      `/professionals/${estado.barbeiro.id}/availability?service=${estado.servico.id}&date=${estado.data}`,
      { auth: false }
    );
    resultado = ok ? dados.slots : [];
  } catch (erro) {
    console.error(erro);
  }

  if (minhaBusca !== ultimaBusca) return;
  horarios = resultado;
  mostrarHorarios();
}

// ---------- Desenhar na tela ----------
function mostrarServicos() {
  const caixa = document.getElementById("lista-servicos");
  if (servicos.length === 0) {
    caixa.innerHTML = '<p class="aviso">Nenhum serviço disponível.</p>';
    return;
  }
  caixa.innerHTML = servicos
    .map(
      (s) => `
      <button type="button" class="opcao-card ${estado.servico?.id === s.id ? "selecionado" : ""}"
              data-tipo="servico" data-valor="${s.id}">
        <strong>${esc(s.nome)}</strong>
        <small>${s.duracao_minutos} min</small>
        <span>${moeda(s.preco)}</span>
      </button>`
    )
    .join("");
}

function mostrarBarbeiros() {
  const caixa = document.getElementById("lista-barbeiros");
  if (barbeiros.length === 0) {
    caixa.innerHTML = '<p class="aviso">Nenhum barbeiro disponível.</p>';
    return;
  }
  caixa.innerHTML = barbeiros
    .map(
      (b) => `
      <button type="button" class="opcao-card ${estado.barbeiro?.id === b.id ? "selecionado" : ""}"
              data-tipo="barbeiro" data-valor="${b.id}">
        <strong>${esc(b.nome)}</strong>
      </button>`
    )
    .join("");
}

function mostrarDias() {
  document.getElementById("lista-dias").innerHTML = dias
    .map((d) => {
      const semana = d.toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "");
      return `
      <button type="button" class="chip chip-dia ${estado.data === iso(d) ? "selecionado" : ""}"
              data-tipo="data" data-valor="${iso(d)}">
        <small>${semana}</small>
        <strong>${d.getDate()}</strong>
      </button>`;
    })
    .join("");
}

function mostrarHorarios() {
  const caixa = document.getElementById("lista-horarios");

  if (!estado.servico || !estado.barbeiro || !estado.data) {
    caixa.innerHTML = '<p class="aviso">Escolha o serviço, o barbeiro e o dia para ver os horários.</p>';
    return;
  }
  if (horarios.length === 0) {
    caixa.innerHTML = '<p class="aviso">Nenhum horário livre neste dia.</p>';
    return;
  }

  caixa.innerHTML = horarios
    .map(
      (slot) => `
      <button type="button" class="chip ${estado.hora === slot ? "selecionado" : ""}"
              data-tipo="hora" data-valor="${slot}">
        ${horaDoSlot(slot)}
      </button>`
    )
    .join("");
}

function mostrarResumo() {
  document.getElementById("r-servico").textContent = estado.servico ? estado.servico.nome : "—";
  document.getElementById("r-barbeiro").textContent = estado.barbeiro ? estado.barbeiro.nome : "—";
  document.getElementById("r-hora").textContent = estado.hora ? horaDoSlot(estado.hora) : "—";
  document.getElementById("r-total").textContent = moeda(estado.servico ? estado.servico.preco : 0);

  if (estado.data) {
    const [a, m, d] = estado.data.split("-").map(Number);
    document.getElementById("r-data").textContent = new Date(a, m - 1, d).toLocaleDateString(
      "pt-BR",
      { weekday: "short", day: "numeric", month: "short" }
    );
  } else {
    document.getElementById("r-data").textContent = "—";
  }

  // O botão só libera quando tudo foi escolhido
  const completo = estado.servico && estado.barbeiro && estado.data && estado.hora;
  document.getElementById("btn-continuar").disabled = !completo;
}

function atualizarTudo() {
  mostrarServicos();
  mostrarBarbeiros();
  mostrarDias();
  mostrarHorarios();
  mostrarResumo();
}

// ---------- Cliques ----------
document.addEventListener("click", (e) => {
  const botao = e.target.closest("[data-tipo]");
  if (!botao || botao.disabled) return;

  const { tipo, valor } = botao.dataset;

  if (tipo === "servico") estado.servico = servicos.find((s) => s.id === Number(valor));
  if (tipo === "barbeiro") estado.barbeiro = barbeiros.find((b) => b.id === Number(valor));
  if (tipo === "data") estado.data = valor;
  if (tipo === "hora") estado.hora = valor;

  if (tipo !== "hora") {
    estado.hora = null;
    atualizarTudo();
    carregarHorarios();
  } else {
    atualizarTudo();
  }
});

document.getElementById("btn-continuar").addEventListener("click", async () => {
  const botao = document.getElementById("btn-continuar");
  botao.disabled = true;
  botao.textContent = "Agendando...";

  try {
    const { ok, status, dados } = await api("/appointments", {
      method: "POST",
      body: {
        profissional: estado.barbeiro.id,
        servico: estado.servico.id,
        data_hora: estado.hora,
      },
    });

    if (status === 401) {
      alert("Sua sessão expirou. Entre novamente.");
      Sessao.limpar();
      window.location.href = "../index.html";
      return;
    }
    if (status === 403) {
      alert("Só clientes podem fazer agendamentos.");
      return;
    }
    if (!ok) {
      alert(mensagemDeErro(dados));
      estado.hora = null;
      await carregarHorarios();
      return;
    }

    alert(`Agendamento feito! ${horaDoSlot(estado.hora)} com ${estado.barbeiro.nome}.`);
    window.location.href = "home.html";
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor. O backend está rodando?");
  } finally {
    botao.textContent = "Confirmar agendamento";
    mostrarResumo();
  }
});

if (usuario) carregarDados();
