let barbearias = [];

const lista = document.getElementById("lista");
const busca = document.getElementById("busca");

const moeda = (v) => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const esc = (t) =>
  String(t ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );

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
          <h2>${esc(b.nome)}</h2>
          <span class="endereco">${esc([b.endereco, b.cidade].filter(Boolean).join(" · "))}</span>
          ${b.precoMinimo !== null ? `<span class="preco">Serviços a partir de ${moeda(b.precoMinimo)}</span>` : ""}
          <a class="btn-agendar" href="agendamento.html">Agendar</a>
        </div>
      </article>`
    )
    .join("");
}

async function carregar() {
  lista.innerHTML = '<p class="vazio">Carregando...</p>';

  try {
    const [barbearia, servicos] = await Promise.all([
      api("/barbershop", { auth: false }),
      api("/services", { auth: false }),
    ]);

    if (!barbearia.ok || !barbearia.dados) {
      barbearias = [];
    } else {
      const precos = servicos.ok ? servicos.dados.map((s) => Number(s.preco)) : [];
      barbearias = [
        { ...barbearia.dados, precoMinimo: precos.length ? Math.min(...precos) : null },
      ];
    }
    mostrar(barbearias);
  } catch (erro) {
    console.error(erro);
    lista.innerHTML = '<p class="vazio">Não foi possível conectar ao servidor.</p>';
  }
}

// Filtra enquanto a pessoa digita
busca.addEventListener("input", () => {
  const termo = busca.value.toLowerCase();
  mostrar(
    barbearias.filter((b) =>
      [b.nome, b.endereco, b.cidade].some((campo) => (campo || "").toLowerCase().includes(termo))
    )
  );
});

document.querySelector(".sair").addEventListener("click", sair);

carregar();
