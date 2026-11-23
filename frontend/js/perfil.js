const usuario = Sessao.usuario();
if (!usuario) {
  alert("Entre na sua conta para ver o perfil.");
  window.location.href = "../../index.html";
}

const NOME_PERFIL = {
  cliente: "Cliente",
  barbeiro: "Barbeiro",
  administrador: "Administrador",
};

const LINKS_POR_PERFIL = {
  cliente: [
    ["agendamento.html", "Agendar"],
    ["meus-agendamentos.html", "Meus agendamentos"],
  ],
  barbeiro: [["agenda.html", "Minha agenda"]],
  administrador: [["admin.html", "Painel"]],
};

if (usuario) {
  const nav = document.getElementById("nav-topo");
  const links = (LINKS_POR_PERFIL[usuario.perfil] || [])
    .map(([href, texto]) => `<a href="${href}">${texto}</a>`)
    .join("");
  nav.insertAdjacentHTML("afterbegin", `${links}<a href="perfil.html" class="atual">Meu perfil</a>`);
}

const campo = (id) => document.getElementById(id);

function sessaoExpirada() {
  alert("Sua sessão expirou. Entre novamente.");
  Sessao.limpar();
  window.location.href = "../../index.html";
}

function preencher(dados) {
  campo("p-nome").value = dados.first_name || "";
  campo("p-sobrenome").value = dados.last_name || "";
  campo("p-email").value = dados.email || "";
  campo("p-telefone").value = dados.telefone || "";
  campo("resumo-conta").textContent =
    `Usuário ${dados.username} · ${NOME_PERFIL[dados.perfil] || dados.perfil}`;
}

async function carregar() {
  try {
    const { ok, status, dados } = await api("/me");
    if (status === 401) return sessaoExpirada();
    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    preencher(dados);
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  }
}

campo("form-dados").addEventListener("submit", async (e) => {
  e.preventDefault();
  const botao = e.target.querySelector("button[type=submit]");
  botao.disabled = true;

  try {
    const { ok, status, dados } = await api("/me", {
      method: "PATCH",
      body: {
        first_name: campo("p-nome").value.trim(),
        last_name: campo("p-sobrenome").value.trim(),
        email: campo("p-email").value.trim(),
        telefone: campo("p-telefone").value.replace(/\D/g, ""),
      },
    });
    if (status === 401) return sessaoExpirada();
    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    localStorage.setItem("usuario", JSON.stringify({ ...usuario, ...dados }));
    preencher(dados);
    alert("Dados atualizados.");
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

campo("form-senha").addEventListener("submit", async (e) => {
  e.preventDefault();
  const botao = e.target.querySelector("button[type=submit]");

  if (campo("s-nova").value !== campo("s-confirma").value) {
    alert("A confirmação não confere com a nova senha.");
    return;
  }

  botao.disabled = true;
  try {
    const { ok, status, dados } = await api("/me/password", {
      method: "POST",
      body: {
        current_password: campo("s-atual").value,
        new_password: campo("s-nova").value,
        new_password_confirm: campo("s-confirma").value,
      },
    });
    if (status === 401) return sessaoExpirada();
    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }
    alert("Senha alterada. Entre novamente com a nova senha.");
    Sessao.limpar();
    window.location.href = "../../index.html";
  } catch (erro) {
    console.error(erro);
    alert("Não foi possível conectar ao servidor.");
  } finally {
    botao.disabled = false;
  }
});

document.querySelector(".sair").addEventListener("click", sair);

if (usuario) carregar();
