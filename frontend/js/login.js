const form = document.getElementById("form-login");

// Ao enviar o formulário
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("usuario").value.trim();
  const password = document.getElementById("senha").value;
  const botao = form.querySelector("button[type=submit]");

  botao.disabled = true;
  botao.textContent = "Entrando...";

  try {
    Sessao.limpar();

    const { ok, status, dados } = await api("/auth/login", {
      method: "POST",
      body: { username, password },
      auth: false,
    });

    if (!ok) {
      alert(status === 401 ? "Usuário ou senha inválidos." : mensagemDeErro(dados));
      return;
    }

    Sessao.salvar(dados);
    window.location.href = ROTAS_POR_PERFIL[dados.user.perfil] || ROTAS_POR_PERFIL.cliente;
  } catch (erro) {
    alert("Não foi possível conectar ao servidor. O backend está rodando?");
    console.error(erro);
  } finally {
    botao.disabled = false;
    botao.textContent = "Entrar";
  }
});

// PARTE - Crie sua conta de cliente
const formCadastro = document.getElementById("form-cadastro");

formCadastro.addEventListener("submit", async (e) => {
  e.preventDefault();

  const senha = document.getElementById("senha-cad").value;
  const confirmar = document.getElementById("confirmar").value;

  if (senha !== confirmar) {
    alert("As senhas não são iguais.");
    return;
  }

  const [primeiro, ...resto] = document.getElementById("nome").value.trim().split(/\s+/);

  const corpo = {
    username: document.getElementById("username-cad").value.trim(),
    email: document.getElementById("email-cad").value.trim(),
    telefone: document.getElementById("celular").value.replace(/\D/g, ""),
    first_name: primeiro || "",
    last_name: resto.join(" "),
    password: senha,
    password_confirm: confirmar,
  };

  const botao = formCadastro.querySelector("button[type=submit]");
  botao.disabled = true;

  try {
    Sessao.limpar();

    const { ok, dados } = await api("/auth/register", {
      method: "POST",
      body: corpo,
      auth: false,
    });

    if (!ok) {
      alert(mensagemDeErro(dados));
      return;
    }

    Sessao.salvar(dados);
    window.location.href = ROTAS_POR_PERFIL.cliente;
  } catch (erro) {
    alert("Não foi possível conectar ao servidor. O backend está rodando?");
    console.error(erro);
  } finally {
    botao.disabled = false;
  }
});
