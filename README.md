# 💈 Sistema de Agendamento para Barbearias

> Plataforma web responsiva para agendamento de serviços em barbearias, conectando clientes, barbeiros e proprietários em um fluxo simples e rápido.

Projeto Integrador desenvolvido para a disciplina **Desenvolvimento de Sistemas Orientado a Dispositivos Móveis e Baseados na Web**, do curso de **Tecnologia em Análise e Desenvolvimento de Sistemas (EAD)** do **Senac**.

---

## 📌 Sobre o projeto

O processo tradicional de agendamento em barbearias costuma depender de ligações e mensagens de texto. Isso gera demora nas respostas, interrupções durante os atendimentos, dificuldade para consultar horários disponíveis e conflitos na agenda, com sobreposição de horários e perda de produtividade.

Este sistema resolve o problema permitindo que o cliente consulte serviços, escolha o profissional e agende o horário sozinho, a qualquer hora do dia. O barbeiro acompanha a agenda direto pelo dispositivo, sem interromper o atendimento.

## 🎯 Público-alvo

- **Clientes:** frequentadores de barbearias que buscam praticidade, agilidade e autonomia para agendar.
- **Barbeiros e proprietários:** profissionais autônomos e donos de barbearias que precisam acompanhar agenda, serviços e atendimentos de forma simples.

## ✨ Funcionalidades previstas

- **Cadastro e login:** autenticação individualizada para administrador/proprietário, clientes e barbeiros.
- **Catálogo de barbearias:** lista de barbearias cadastradas e seus serviços (corte, barba, selagem etc.) com preços e durações.
- **Agendamento de horários:** seleção de serviço, profissional, data e horário, com confirmação do agendamento.
- **Agenda do barbeiro:** painel com os agendamentos do dia e da semana (realizados, confirmados, finalizados e cancelados).
- **Histórico de atendimentos:** o cliente consulta seus agendamentos anteriores e o estabelecimento consulta os atendimentos realizados.

## 🧭 Jornada principal do usuário

1. **Home / Catálogo:** o cliente acessa o sistema (celular ou computador), faz login ou cadastro e navega pelas barbearias.
2. **Agendamento:** escolhe o serviço, o profissional, a data e o horário disponíveis.
3. **Checkout / Confirmação:** revisa o resumo e valida o agendamento e o pagamento.
4. **Meus agendamentos:** recebe a confirmação e acompanha o status e o histórico.

## 👥 Personas

| Persona | Perfil | Principal necessidade |
|---|---|---|
| **Lucas Pereira Ramos**, 40 anos, Gestor de TI | Rotina corrida, nível tecnológico alto | Agendar o barbeiro de forma ágil e sem burocracia |
| **Carlos Felipino da Silva**, 50 anos, Proprietário de barbearia | Nível tecnológico médio | Otimizar tempo, agenda, relatórios e processos |

## 🏗️ Tipo de solução

**Web responsiva:** uma única aplicação que funciona bem em smartphones, tablets, notebooks e desktops. Isso evita desenvolver e manter um app mobile nativo e um software desktop separados para administrador e barbeiros.

## 🛠️ Tecnologias

<!-- Preencha com as tecnologias que o grupo definir -->

| Camada | Tecnologia |
|---|---|
| Front-end | _HTML,CSS, JavaScript_ |
| Back-end | _a definir_ |
| Banco de dados | _a definir_ |
| Prototipação | _a definir_ |

## 🚀 Como executar

> Esta seção será atualizada conforme o desenvolvimento avançar.

```bash
# Clone o repositório
git clone https://github.com/<usuario>/<nome-do-repositorio>.git

# Acesse a pasta do projeto
cd <nome-do-repositorio>

# Instale as dependências
npm install

# Inicie o projeto
npm run dev
```

## 📂 Estrutura do repositório

```
barbearia/
├── frontend/      #  (HTML, CSS, JS)
├── backend/       # API do pessoal do back
├── database/      # scripts SQL, modelagem, diagramas
├── docs/          # documentos das entregas, personas, jornada
├── .gitignore
└── README.md
```

## 📅 Status do projeto

- [x] 1ª entrega: Fundamentação estratégica e conceitual (problema, público-alvo, stakeholders, personas e jornada do usuário)
- [ ] Prototipação das telas
- [ ] Desenvolvimento da aplicação
- [ ] Testes
- [ ] Entrega final

## 👨‍💻 Equipe

| Integrante |
|---|
| Cleber Henrique Azevedo Martins |
| Isabelly Franklin Silva |
| Izabela Rodrigues Costa |
| Kayky Raphael Tavares Macena |
| Raissa Anne Ribeiro |
| Ruan Alexander Rodrigues Joaquim |

**Professor orientador:** Anderson Cleyton

## 📄 Licença

Projeto desenvolvido para fins acadêmicos.
