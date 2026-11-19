const usuario = Sessao.usuario();
if (!usuario || usuario.perfil !== "administrador") {
  alert("Acesso restrito ao administrador.");
  window.location.href = "../index.html";
}

const moeda = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const doisDigitos = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${doisDigitos(d.getMonth() + 1)}-${doisDigitos(d.getDate())}`;
const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

const DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const STATUS = {
  pendente: "Pendente",
  confirmado: "Confirmado",
  concluido: "Finalizado",
  cancelado: "Cancelado",
};

async function chamar(caminho, opcoes) {
  const resposta = await api(caminho, opcoes);
  if (resposta.status === 401) {
    alert("Sua sessão expirou. Entre novamente.");
    Sessao.limpar();
    window.location.href = "../index.html";
  }
  return resposta;
}

function semanaAtual() {
  const hoje = new Date();
  const segunda = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() - ((hoje.getDay() + 6) % 7));
  const domingo = new Date(segunda.getFullYear(), segunda.getMonth(), segunda.getDate() + 6);
  return { de: iso(segunda), ate: iso(domingo) };
}

document.querySelectorAll(".item-menu").forEach((item) => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".item-menu").forEach((i) => i.classList.remove("ativo"));
    document.querySelectorAll(".secao").forEach((s) => s.classList.remove("ativa"));
    item.classList.add("ativo");
    document.getElementById(item.dataset.secao).classList.add("ativa");

    if (item.dataset.secao === "dashboard") carregarDashboard();
    if (item.dataset.secao === "servicos") carregarServicos();
    if (item.dataset.secao === "equipe") carregarEquipe();
    if (item.dataset.secao === "relatorios") carregarRelatorio();
    if (item.dataset.secao === "barbearia") carregarBarbearia();
  });
});

// Janelas de edição: fecha pelo botão Cancelar
document.querySelectorAll("dialog [data-fechar]").forEach((botao) => {
  botao.addEventListener("click", () => botao.closest("dialog").close());
});

async function carregarDashboard() {
  const { de, ate } = semanaAtual();
  const { ok, dados } = await chamar(`/admin/appointments?from=${de}&to=${ate}`);
  const lista = ok ? dados : [];

  const validos = lista.filter((a) => a.status !== "cancelado");
  const concluidos = lista.filter((a) => a.status === "concluido");
  document.getElementById("c-agend").textContent = validos.length;
  document.getElementById("c-fat").textContent = moeda(concluidos.reduce((soma, a) => soma + Number(a.preco), 0));
  document.getElementById("c-canc").textContent = lista.length - validos.length;

  const porDia = [0, 0, 0, 0, 0, 0, 0];
  validos.forEach((a) => {
    const [ano, mes, dia] = a.data_hora.slice(0, 10).split("-").map(Number);
    porDia[(new Date(ano, mes - 1, dia).getDay() + 6) % 7]++;
  });
  const maior = Math.max(...porDia, 1);

  document.getElementById("grafico").innerHTML = porDia
    .map(
      (qtd, i) => `
      <div class="barra">
        <span>${qtd}</span>
        <div style="height: ${(qtd / maior) * 100}%"></div>
        <span>${DIAS_SEMANA[i]}</span>
      </div>`
    )
    .join("");
}

const tabelaServicos = document.getElementById("tabela-servicos");
let servicos = [];

async function carregarServicos() {
  const { ok, dados } = await chamar("/admin/services");
  servicos = ok ? dados : [];

  if (servicos.length === 0) {
    tabelaServicos.innerHTML = '<tr><td colspan="4">Nenhum serviço cadastrado.</td></tr>';
    return;
  }

  tabelaServicos.innerHTML = servicos
    .map(
      (s) => `
      <tr${s.ativo ? "" : ' style="opacity: 0.5"'}>
        <td>${esc(s.nome)}</td>
        <td>${moeda(s.preco)}</td>
        <td>${s.duracao_minutos} min</td>
        <td style="white-space: nowrap">
          <button type="button" class="btn" data-editar-servico="${s.id}">Editar</button>
          <button type="button" class="btn ${s.ativo ? "perigo" : ""}" data-servico="${s.id}" data-ativo="${s.ativo}">
            ${s.ativo ? "Desativar" : "Reativar"}
          </button>
        </td>
      </tr>`
    )
    .join("");
}

document.getElementById("form-servico").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const botao = form.querySelector("button[type=submit]");
  botao.disabled = true;

  try {
    const { ok, dados } = await chamar("/admin/services", {
      method: "POST",
      body: {
        nome: document.getElementById("s-nome").value.trim(),
        preco: Number(document.getElementById("s-preco").value).toFixed(2),
        duracao_minutos: Number(document.getElementById("s-duracao").value),
        ativo: true,
      },
    });

    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    form.reset();
    carregarServicos();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

const modalServico = document.getElementById("modal-servico");
let servicoEmEdicao = null;

function abrirEdicaoServico(id) {
  const s = servicos.find((item) => item.id === id);
  if (!s) return;
  servicoEmEdicao = id;
  document.getElementById("es-nome").value = s.nome;
  document.getElementById("es-descricao").value = s.descricao || "";
  document.getElementById("es-preco").value = Number(s.preco);
  document.getElementById("es-duracao").value = s.duracao_minutos;
  modalServico.showModal();
}

document.getElementById("form-editar-servico").addEventListener("submit", async (e) => {
  e.preventDefault();
  const botao = e.target.querySelector("button[type=submit]");
  botao.disabled = true;

  try {
    const { ok, dados } = await chamar(`/admin/services/${servicoEmEdicao}`, {
      method: "PATCH",
      body: {
        nome: document.getElementById("es-nome").value.trim(),
        descricao: document.getElementById("es-descricao").value.trim(),
        preco: Number(document.getElementById("es-preco").value).toFixed(2),
        duracao_minutos: Number(document.getElementById("es-duracao").value),
      },
    });
    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    modalServico.close();
    carregarServicos();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

tabelaServicos.addEventListener("click", async (e) => {
  const editar = e.target.closest("button[data-editar-servico]");
  if (editar) {
    abrirEdicaoServico(Number(editar.dataset.editarServico));
    return;
  }

  const botao = e.target.closest("button[data-servico]");
  if (!botao) return;

  const ativo = botao.dataset.ativo === "true";
  if (ativo && !confirm("Desativar este serviço? Ele deixa de aparecer para os clientes.")) return;

  botao.disabled = true;
  const { ok, dados } = await chamar(`/admin/services/${botao.dataset.servico}`, {
    method: "PATCH",
    body: { ativo: !ativo },
  });
  if (!ok) alert(mensagemDeErro(dados));
  carregarServicos();
});

const listaEquipe = document.getElementById("lista-equipe");
const selectBarbeiro = document.getElementById("h-barbeiro");
let equipe = [];

async function carregarEquipe() {
  const [profissionais, horarios] = await Promise.all([
    chamar("/admin/professionals"),
    chamar("/admin/availability"),
  ]);

  equipe = profissionais.ok ? profissionais.dados : [];
  const blocos = horarios.ok ? horarios.dados : [];

  const ativos = equipe.filter((p) => p.ativo);
  selectBarbeiro.innerHTML = ativos.length
    ? ativos.map((p) => `<option value="${p.id}">${esc(p.nome)}</option>`).join("")
    : '<option value="">Cadastre um barbeiro primeiro</option>';

  if (equipe.length === 0) {
    listaEquipe.innerHTML = '<p class="subtitulo">Nenhum barbeiro cadastrado.</p>';
    return;
  }

  listaEquipe.innerHTML = equipe
    .map((p) => {
      const meus = blocos
        .filter((b) => b.profissional === p.id && b.ativo)
        .sort((a, b) => a.dia_semana - b.dia_semana || a.hora_inicio.localeCompare(b.hora_inicio))
        .map(
          (b) => `
          <span>
            ${DIAS_SEMANA[b.dia_semana]} ${b.hora_inicio.slice(0, 5)}–${b.hora_fim.slice(0, 5)}
            <button type="button" class="btn perigo" style="padding: 2px 8px" data-horario="${b.id}" title="Remover horário">✕</button>
          </span>`
        );

      return `
      <div class="card"${p.ativo ? "" : ' style="opacity: 0.5"'}>
        <strong>${esc(p.nome)}</strong>
        ${p.especialidades ? `<span>${esc(p.especialidades)}</span>` : ""}
        ${meus.length ? meus.join("") : "<span>Sem horários cadastrados</span>"}
        <div class="acoes-card">
          <button type="button" class="btn" data-editar-barbeiro="${p.id}">Editar</button>
          <button type="button" class="btn ${p.ativo ? "perigo" : ""}" data-barbeiro="${p.id}" data-ativo="${p.ativo}">
            ${p.ativo ? "Desativar" : "Reativar"}
          </button>
        </div>
      </div>`;
    })
    .join("");
}

document.getElementById("form-barbeiro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const botao = form.querySelector("button[type=submit]");
  const [primeiro, ...resto] = document.getElementById("b-nome").value.trim().split(/\s+/);

  botao.disabled = true;
  try {
    const { ok, dados } = await chamar("/admin/professionals", {
      method: "POST",
      body: {
        username: document.getElementById("b-usuario").value.trim(),
        password: document.getElementById("b-senha").value,
        telefone: document.getElementById("b-telefone").value.replace(/\D/g, ""),
        first_name: primeiro || "",
        last_name: resto.join(" "),
      },
    });

    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    form.reset();
    filtroBarbeiro.innerHTML = "";
    carregarEquipe();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

document.getElementById("form-horario").addEventListener("submit", async (e) => {
  e.preventDefault();
  const botao = e.target.querySelector("button[type=submit]");
  const inicio = document.getElementById("h-inicio").value;
  const fim = document.getElementById("h-fim").value;

  if (!selectBarbeiro.value) {
    alert("Cadastre um barbeiro primeiro.");
    return;
  }
  if (fim <= inicio) {
    alert("O horário de fim precisa ser depois do início.");
    return;
  }

  botao.disabled = true;
  try {
    const { ok, dados } = await chamar("/admin/availability", {
      method: "POST",
      body: {
        profissional: Number(selectBarbeiro.value),
        dia_semana: Number(document.getElementById("h-dia").value),
        hora_inicio: inicio,
        hora_fim: fim,
        ativo: true,
      },
    });

    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    carregarEquipe();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

const modalBarbeiro = document.getElementById("modal-barbeiro");
let barbeiroEmEdicao = null;

function abrirEdicaoBarbeiro(id) {
  const p = equipe.find((item) => item.id === id);
  if (!p) return;
  barbeiroEmEdicao = id;
  document.getElementById("eb-usuario").textContent = `Usuário de acesso: ${p.username}`;
  document.getElementById("eb-nome").value = p.first_name || "";
  document.getElementById("eb-sobrenome").value = p.last_name || "";
  document.getElementById("eb-telefone").value = p.telefone || "";
  document.getElementById("eb-email").value = p.email || "";
  document.getElementById("eb-especialidades").value = p.especialidades || "";
  document.getElementById("eb-bio").value = p.bio || "";
  modalBarbeiro.showModal();
}

document.getElementById("form-editar-barbeiro").addEventListener("submit", async (e) => {
  e.preventDefault();
  const botao = e.target.querySelector("button[type=submit]");
  botao.disabled = true;

  try {
    const { ok, dados } = await chamar(`/admin/professionals/${barbeiroEmEdicao}`, {
      method: "PATCH",
      body: {
        first_name: document.getElementById("eb-nome").value.trim(),
        last_name: document.getElementById("eb-sobrenome").value.trim(),
        telefone: document.getElementById("eb-telefone").value.replace(/\D/g, ""),
        email: document.getElementById("eb-email").value.trim(),
        especialidades: document.getElementById("eb-especialidades").value.trim(),
        bio: document.getElementById("eb-bio").value.trim(),
      },
    });
    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    modalBarbeiro.close();
    filtroBarbeiro.innerHTML = "";
    carregarEquipe();
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

listaEquipe.addEventListener("click", async (e) => {
  const removerHorario = e.target.closest("button[data-horario]");
  const alterarBarbeiro = e.target.closest("button[data-barbeiro]");
  const editarBarbeiro = e.target.closest("button[data-editar-barbeiro]");

  if (editarBarbeiro) {
    abrirEdicaoBarbeiro(Number(editarBarbeiro.dataset.editarBarbeiro));
    return;
  }

  if (removerHorario) {
    if (!confirm("Remover este horário de trabalho?")) return;
    removerHorario.disabled = true;
    const { ok, dados } = await chamar(`/admin/availability/${removerHorario.dataset.horario}`, {
      method: "DELETE",
    });
    if (!ok) alert(mensagemDeErro(dados));
    carregarEquipe();
  }

  if (alterarBarbeiro) {
    const ativo = alterarBarbeiro.dataset.ativo === "true";
    if (ativo && !confirm("Desativar este barbeiro? Ele deixa de aparecer para os clientes.")) return;
    alterarBarbeiro.disabled = true;
    const { ok, dados } = await chamar(`/admin/professionals/${alterarBarbeiro.dataset.barbeiro}`, {
      method: "PATCH",
      body: { ativo: !ativo },
    });
    if (!ok) alert(mensagemDeErro(dados));
    filtroBarbeiro.innerHTML = "";
    carregarEquipe();
  }
});

const filtroBarbeiro = document.getElementById("filtro-barbeiro");

async function carregarFiltroBarbeiros() {
  const { ok, dados } = await chamar("/admin/professionals");
  const equipe = ok ? dados : [];
  filtroBarbeiro.innerHTML =
    '<option value="">Todos os barbeiros</option>' +
    equipe.map((p) => `<option value="${p.id}">${esc(p.nome)}</option>`).join("");
}

async function carregarRelatorio() {
  if (filtroBarbeiro.options.length === 0) await carregarFiltroBarbeiros();

  const corpo = document.getElementById("tabela-relatorio");
  const params = new URLSearchParams();
  const filtros = {
    professional: filtroBarbeiro.value,
    status: document.getElementById("filtro-status").value,
    from: document.getElementById("filtro-de").value,
    to: document.getElementById("filtro-ate").value,
  };
  Object.entries(filtros).forEach(([chave, valor]) => {
    if (valor) params.set(chave, valor);
  });

  const { ok, dados } = await chamar(`/admin/appointments${params.toString() ? `?${params}` : ""}`);
  if (!ok) {
    corpo.innerHTML = `<tr><td colspan="6">${esc(mensagemDeErro(dados))}</td></tr>`;
    document.getElementById("total-relatorio").textContent = "";
    return;
  }
  const lista = dados;

  if (lista.length === 0) {
    corpo.innerHTML = '<tr><td colspan="6">Nenhum atendimento encontrado.</td></tr>';
    document.getElementById("total-relatorio").textContent = "";
    return;
  }

  corpo.innerHTML = lista
    .map((a) => {
      const [ano, mes, dia] = a.data_hora.slice(0, 10).split("-");
      return `
      <tr>
        <td>${dia}/${mes}/${ano} ${a.data_hora.slice(11, 16)}</td>
        <td>${esc(a.cliente?.nome || a.cliente?.username)}</td>
        <td>${esc(a.servico_nome)}</td>
        <td>${esc(a.profissional_nome)}</td>
        <td>${moeda(a.preco)}</td>
        <td>${STATUS[a.status] || esc(a.status)}</td>
      </tr>`;
    })
    .join("");

  const concluidos = lista.filter((a) => a.status === "concluido");
  document.getElementById("total-relatorio").textContent =
    `Total finalizado: ${moeda(concluidos.reduce((soma, a) => soma + Number(a.preco), 0))} (${concluidos.length} atendimentos)`;
}

document.getElementById("form-relatorio").addEventListener("submit", (e) => {
  e.preventDefault();
  carregarRelatorio();
});

document.getElementById("limpar-relatorio").addEventListener("click", () => {
  document.getElementById("form-relatorio").reset();
  carregarRelatorio();
});

const campoBarbearia = (id) => document.getElementById(`bb-${id}`);

function preencherBarbearia(b) {
  campoBarbearia("nome").value = b.nome || "";
  campoBarbearia("descricao").value = b.descricao || "";
  campoBarbearia("endereco").value = b.endereco || "";
  campoBarbearia("cidade").value = b.cidade || "";
  campoBarbearia("telefone").value = b.telefone || "";
  campoBarbearia("email").value = b.email || "";
  campoBarbearia("atualizado").textContent = b.atualizado_em
    ? `Última atualização: ${new Date(b.atualizado_em).toLocaleString("pt-BR")}`
    : "";
}

async function carregarBarbearia() {
  const { ok, dados } = await chamar("/barbershop");
  if (!ok) {
    alert(mensagemDeErro(dados));
    return;
  }
  preencherBarbearia(dados);
}

document.getElementById("form-barbearia").addEventListener("submit", async (e) => {
  e.preventDefault();
  const botao = e.target.querySelector("button[type=submit]");
  botao.disabled = true;

  try {
    const { ok, dados } = await chamar("/admin/barbershop", {
      method: "PATCH",
      body: {
        nome: campoBarbearia("nome").value.trim(),
        descricao: campoBarbearia("descricao").value.trim(),
        endereco: campoBarbearia("endereco").value.trim(),
        cidade: campoBarbearia("cidade").value.trim(),
        telefone: campoBarbearia("telefone").value.trim(),
        email: campoBarbearia("email").value.trim(),
      },
    });
    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    preencherBarbearia(dados);
    alert("Dados da barbearia atualizados.");
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

document.getElementById("btn-sair").addEventListener("click", sair);

if (usuario) carregarDashboard().catch((erro) => console.error(erro));
