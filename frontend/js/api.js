const API_URL = "http://localhost:8000/api/v1";

const Sessao = {
  salvar(dados) {
    localStorage.setItem("access", dados.access);
    localStorage.setItem("refresh", dados.refresh);
    localStorage.setItem("usuario", JSON.stringify(dados.user));
  },
  usuario() {
    const salvo = localStorage.getItem("usuario");
    return salvo ? JSON.parse(salvo) : null;
  },
  limpar() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("usuario");
  },
};

const ROTAS_POR_PERFIL = {
  cliente: "pages/home.html",
  barbeiro: "pages/agenda.html",
  administrador: "pages/admin.html",
};

async function renovarToken() {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return false;

  const resposta = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!resposta.ok) return false;

  const dados = await resposta.json();
  localStorage.setItem("access", dados.access);
  if (dados.refresh) localStorage.setItem("refresh", dados.refresh);
  return true;
}

async function api(caminho, { method = "GET", body, auth = true } = {}) {
  const montar = () => {
    const headers = { "Content-Type": "application/json" };
    const access = localStorage.getItem("access");
    if (auth && access) headers.Authorization = `Bearer ${access}`;
    return {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    };
  };

  let resposta = await fetch(API_URL + caminho, montar());

  if (resposta.status === 401 && auth && (await renovarToken())) {
    resposta = await fetch(API_URL + caminho, montar());
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
