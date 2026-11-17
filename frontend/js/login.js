const botoes = document.querySelectorAll(".opcao");
const form = document.getElementById("form-login");

let perfil = "cliente"; // equivale ao useState("cliente")

const rotas = {
  cliente: "pages/home.html",
  barbeiro: "pages/agenda.html",
  admin: "pages/admin.html",
};

// Ao clicar em um botão do seletor
botoes.forEach((botao) => {
  botao.addEventListener("click", () => {
    perfil = botao.dataset.perfil;

    // tira o destaque de todos e coloca só no clicado
    botoes.forEach((b) => b.classList.remove("ativo"));
    botao.classList.add("ativo");
  });
});

// Ao enviar o formulário
form.addEventListener("submit", (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  // troca isso por um fetch para a API de login
  window.location.href = rotas[perfil];
});

// PARTE - Crie sua conta de cliente
const formCadastro = document.getElementById("form-cadastro");

formCadastro.addEventListener("submit", (e) => {
  e.preventDefault();

  const senha = document.getElementById("senha-cad").value;
  const confirmar = document.getElementById("confirmar").value;

  if (senha !== confirmar) {
    alert("As senhas não são iguais.");
    return;
  }

  // TODO: enviar os dados para a API de cadastro do backend
  console.log("Cadastro válido!");
});