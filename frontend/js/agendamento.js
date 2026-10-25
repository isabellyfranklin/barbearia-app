// Dados fictícios. Depois vêm da API.
const barbearias = [
  { id: 1, nome: "Barba & Cia" },
  { id: 2, nome: "Navalha de Ouro" },
  { id: 3, nome: "Corte Nobre" },
  { id: 4, nome: "Old School Barber" },
  { id: 5, nome: "Alfaiate da Barba" },
  { id: 6, nome: "Estilo Prumo" },
];

const servicos = [
  { id: 1, nome: "Corte", preco: 45, duracao: 30 },
  { id: 2, nome: "Barba", preco: 30, duracao: 20 },
  { id: 3, nome: "Corte + barba", preco: 70, duracao: 50 },
  { id: 4, nome: "Selagem", preco: 90, duracao: 60 },
];

const barbeiros = [
  { id: 1, nome: "Carlos" },
  { id: 2, nome: "André" },
  { id: 3, nome: "Felipe" },
];

// Descobre qual barbearia foi escolhida pela URL (?id=1)
const params = new URLSearchParams(location.search);
const barbearia =
  barbearias.find((b) => b.id === Number(params.get("id"))) || barbearias[0];
document.getElementById("nome-barbearia").textContent = barbearia.nome;

// O que a pessoa já escolheu
const estado = { servico: null, barbeiro: null, data: null, hora: null };

const moeda = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const doisDigitos = (n) => String(n).padStart(2, "0");

// ---------- Dias e horários ----------
const hoje = new Date();
const dias = [];
for (let i = 0; i < 7; i++) {
  dias.push(new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + i));
}

const iso = (d) => `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`;

const horarios = [];
for (let h = 9; h < 18; h++) {
  horarios.push(`${doisDigitos(h)}:00`, `${doisDigitos(h)}:30`);
}

// Simulação de horários ocupados. Depois vem da API.
function estaOcupado(hora, indice) {
  const indiceDia = dias.findIndex((d) => iso(d) === estado.data);
  const indiceBarbeiro = barbeiros.findIndex((b) => b.id === estado.barbeiro.id);

  // horários que já passaram hoje
  const [h, m] = hora.split(":").map(Number);
  const agora = new Date();
  const jaPassou =
    estado.data === iso(agora) && h * 60 + m <= agora.getHours() * 60 + agora.getMinutes();

  return jaPassou || (indice + indiceDia + indiceBarbeiro) % 4 === 0;
}

// ---------- Desenhar na tela ----------
function mostrarServicos() {
  document.getElementById("lista-servicos").innerHTML = servicos
    .map(
      (s) => `
      <button type="button" class="opcao-card ${estado.servico?.id === s.id ? "selecionado" : ""}"
              data-tipo="servico" data-valor="${s.id}">
        <strong>${s.nome}</strong>
        <small>${s.duracao} min</small>
        <span>${moeda(s.preco)}</span>
      </button>`
    )
    .join("");
}

function mostrarBarbeiros() {
  document.getElementById("lista-barbeiros").innerHTML = barbeiros
    .map(
      (b) => `
      <button type="button" class="opcao-card ${estado.barbeiro?.id === b.id ? "selecionado" : ""}"
              data-tipo="barbeiro" data-valor="${b.id}">
        <strong>${b.nome}</strong>
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

  if (!estado.barbeiro || !estado.data) {
    caixa.innerHTML = '<p class="aviso">Escolha o barbeiro e o dia para ver os horários.</p>';
    return;
  }

  caixa.innerHTML = horarios
    .map(
      (h, i) => `
      <button type="button" class="chip ${estado.hora === h ? "selecionado" : ""}"
              data-tipo="hora" data-valor="${h}" ${estaOcupado(h, i) ? "disabled" : ""}>
        ${h}
      </button>`
    )
    .join("");
}

function mostrarResumo() {
  document.getElementById("r-servico").textContent = estado.servico ? estado.servico.nome : "—";
  document.getElementById("r-barbeiro").textContent = estado.barbeiro ? estado.barbeiro.nome : "—";
  document.getElementById("r-hora").textContent = estado.hora || "—";
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

  // Trocou o barbeiro ou o dia: o horário escolhido pode não valer mais
  if (tipo === "barbeiro" || tipo === "data") estado.hora = null;

  atualizarTudo();
});

document.getElementById("btn-continuar").addEventListener("click", () => {
  // Guarda a escolha para a próxima tela (checkout) ler
  sessionStorage.setItem(
    "agendamento",
    JSON.stringify({
      barbearia: barbearia.nome,
      servico: estado.servico,
      barbeiro: estado.barbeiro,
      data: estado.data,
      hora: estado.hora,
    })
  );
  window.location.href = "checkout.html";
});

atualizarTudo();