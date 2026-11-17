// Endereço da API (backend Django)
const API_URL = "http://localhost:8000/api/v1";

// ---------- Sessão (token e usuário salvos no navegador) ----------
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

// Para onde cada perfil vai depois de entrar (caminhos a partir do index.html)
const ROTAS_POR_PERFIL = {
  cliente: "pages/home.html",
  barbeiro: "pages/agenda.html",
  administrador: "pages/admin.html",
};

// ---------- Renova o token quando ele expira (30 min) ----------
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
  if (dados.refresh) localStorage.setItem("refresh", dados.refresh); // a API troca o refresh
  return true;
}

// ---------- Função principal para chamar a API ----------
// Uso: const { ok, status, dados } = await api("/services");
//      await api("/auth/login", { method: "POST", body: {...}, auth: false });
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

  // Token venceu? Renova uma vez e tenta de novo
  if (resposta.status === 401 && auth && (await renovarToken())) {
    resposta = await fetch(API_URL + caminho, montar());
  }

  // 204 não tem corpo
  const texto = await resposta.text();
  const dados = texto ? JSON.parse(texto) : null;

  return { ok: resposta.ok, status: resposta.status, dados };
}

// Transforma o erro da API em texto legível
// Ex.: {"email":["Já existe..."]} -> "email: Já existe..."
function mensagemDeErro(dados) {
  if (!dados) return "Erro inesperado. Tente novamente.";
  if (dados.detail) return dados.detail;
  return Object.entries(dados)
    .map(([campo, msgs]) => `${campo}: ${[].concat(msgs).join(" ")}`)
    .join("\n");
}
