// Dados fictícios. Depois vêm da API: fetch(`${API_URL}/barbearias`)
const barbearias = [
  { id: 1, nome: "Barba & Cia", bairro: "Capão Redondo", nota: 4.8, preco: 45 },
  { id: 2, nome: "Navalha de Ouro", bairro: "Campo Limpo", nota: 4.6, preco: 50 },
  { id: 3, nome: "Corte Nobre", bairro: "Santo Amaro", nota: 4.9, preco: 60 },
  { id: 4, nome: "Old School Barber", bairro: "Pinheiros", nota: 4.7, preco: 70 },
  { id: 5, nome: "Alfaiate da Barba", bairro: "Butantã", nota: 4.5, preco: 40 },
  { id: 6, nome: "Estilo Prumo", bairro: "Vila Mariana", nota: 4.8, preco: 55 },
];

const lista = document.getElementById("lista");
const busca = document.getElementById("busca");

function mostrar(itens) {
  if (itens.length === 0) {
    lista.innerHTML = '<p class="vazio">Nenhuma barbearia encontrada.</p>';
    return;
  }

  lista.innerHTML = itens
    .map(
      (b) => `
      <article class="card-barbearia">
        <div class="card-foto"></div>
        <div class="card-corpo">
          <h2>${b.nome}</h2>
          <span class="endereco">${b.bairro}</span>
          <span class="nota">★ ${b.nota.toFixed(1)}</span>
          <span class="preco">Cortes a partir de R$ ${b.preco}</span>
          <a class="btn-agendar" href="agendamento.html?id=${b.id}">Agendar</a>
        </div>
      </article>`
    )
    .join("");
}

// Filtra enquanto a pessoa digita
busca.addEventListener("input", () => {
  const termo = busca.value.toLowerCase();
  mostrar(
    barbearias.filter(
      (b) => b.nome.toLowerCase().includes(termo) || b.bairro.toLowerCase().includes(termo)
    )
  );
});

mostrar(barbearias);