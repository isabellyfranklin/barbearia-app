const apiConfigurada = document.querySelector('meta[name="api-url"]')?.content.trim();
const ambienteLocal = ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname);
const API_URL = (apiConfigurada || (ambienteLocal ? "http://localhost:8000/api/v1" : "/api/v1"))
  .replace(/\/+$/, "");

let renovacaoEmCurso = null;
let encerrandoSessao = false;
let versaoSessao = 0;

const Sessao = {
  salvar(dados) {
    versaoSessao++;
    localStorage.setItem("access", dados.access);
    localStorage.setItem("refresh", dados.refresh);
    localStorage.setItem("usuario", JSON.stringify(dados.user));
  },
  usuario() {
    const salvo = localStorage.getItem("usuario");
    return salvo ? JSON.parse(salvo) : null;
  },
  limpar() {
    versaoSessao++;
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("usuario");
  },
};

const ROTAS_POR_PERFIL = {
  cliente: "frontend/pages/agendamento.html",
  barbeiro: "frontend/pages/agenda.html",
  administrador: "frontend/pages/admin.html",
};

function renovarToken() {
  if (!renovacaoEmCurso) {
    renovacaoEmCurso = solicitarRenovacao().finally(() => {
      renovacaoEmCurso = null;
    });
  }
  return renovacaoEmCurso;
}

async function solicitarRenovacao() {
  const versao = versaoSessao;
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return false;

  const resposta = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!resposta.ok) return false;

  const dados = await resposta.json();
  if (versao !== versaoSessao || localStorage.getItem("refresh") !== refresh) return false;
  localStorage.setItem("access", dados.access);
  if (dados.refresh) localStorage.setItem("refresh", dados.refresh);
  return true;
}

async function sair(evento) {
  evento.preventDefault();
  if (encerrandoSessao) return;
  encerrandoSessao = true;
  const destino = evento.currentTarget.href;

  const revogarRefresh = () => fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${localStorage.getItem("access")}`,
    },
    body: JSON.stringify({ refresh: localStorage.getItem("refresh") }),
  });

  try {
    await renovacaoEmCurso?.catch(() => {});
    if (localStorage.getItem("refresh")) {
      const resposta = await revogarRefresh();
      const resultado = resposta.status === 401 && await renovarToken()
        ? await revogarRefresh()
        : resposta;
      if (!resultado.ok) console.warn("A API não confirmou a revogação da sessão.");
    }
  } catch (erro) {
    console.warn("Não foi possível revogar a sessão na API.", erro);
  } finally {
    Sessao.limpar();
    window.location.href = destino;
  }
}

async function api(caminho, { method = "GET", body, auth = true, signal } = {}) {
  const montar = () => {
    const headers = { "Content-Type": "application/json" };
    const access = localStorage.getItem("access");
    if (auth && access) headers.Authorization = `Bearer ${access}`;
    return {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    };
  };

  const requisicao = montar();
  const versao = versaoSessao;
  const refreshInicial = localStorage.getItem("refresh");
  let resposta = await fetch(API_URL + caminho, requisicao);

  if (resposta.status === 401 && auth && !encerrandoSessao && refreshInicial && versao === versaoSessao) {
    const atualizada = montar();
    const tokenMudou = atualizada.headers.Authorization &&
      atualizada.headers.Authorization !== requisicao.headers.Authorization;
    const mesmaSessao = localStorage.getItem("refresh") === refreshInicial;
    if ((tokenMudou || (mesmaSessao && await renovarToken())) &&
        !encerrandoSessao && versao === versaoSessao) {
      resposta = await fetch(API_URL + caminho, montar());
    }
  }

  const texto = await resposta.text();
  const dados = texto ? JSON.parse(texto) : null;

  return { ok: resposta.ok, status: resposta.status, dados };
}

function mensagemDeErro(dados) {
  if (!dados) return "Erro inesperado. Tente novamente.";
  if (dados.detail) return dados.detail;
  return Object.entries(dados)
    .map(([campo, msgs]) => `${campo}: ${[].concat(msgs).join(" ")}`)
    .join("\n");
}
