# Plano do Projeto — Barbearia APP (Backend)

## 1. Visão geral

Backend de um sistema de agendamentos para **uma única barbearia**. O cliente consulta
profissionais e serviços, vê horários livres e reserva sem contato manual. O barbeiro consulta
sua agenda de trabalho. O administrador/proprietário gerencia a operação do estabelecimento.

O projeto será **somente backend**, com **API REST em Django REST Framework**, autenticação
**JWT**, integração com **MySQL** (infraestrutura fora do escopo de entrega) e ambiente
**Docker**. **FastAPI não será utilizado** e o frontend/SPA **não faz parte desta entrega**.

> **Nesta etapa será produzido somente o planejamento. Nenhum código será criado.**

---

## 2. Decisões já tomadas

| Tema | Decisão |
|---|---|
| Alcance | Uma barbearia |
| Entrega | Somente backend |
| Linguagem/framework | Python + Django |
| API | Django REST Framework (DRF) |
| Autenticação | JWT (access + refresh) |
| FastAPI | Fora do projeto |
| Frontend/SPA | Fora do escopo desta entrega |
| Banco de dados | MySQL (infraestrutura fora do escopo de entrega) |
| Perfis | Cliente, Barbeiro, Administrador/proprietário |
| Extras no MVP | Nenhum (sem pagamento online, sem notificações) |
| Infraestrutura | Docker |
| Idioma | Português (Brasil) |
| Fuso horário | `America/Sao_Paulo` |
| Publicação | Ainda não definida |
| Entrega atual | Somente ajustar este plano |

---

## 3. Decisões pendentes

| Decisão | Situação |
|---|---|
| Publicação | Ainda não definida (local, VPS ou plataforma gerenciada) |

Todas as decisões de arquitetura do backend estão fechadas. A publicação pode ficar para depois
sem bloquear o desenvolvimento.

A infraestrutura do banco também não faz parte da entrega: a aplicação consumirá uma instância
MySQL já existente, fornecida pelo ambiente/equipe responsável.

---

## 4. Módulos planejados

| Módulo | Funcionalidades planejadas |
|---|---|
| **Contas e perfis** | Cadastro, autenticação e controle de acesso conforme o perfil do usuário. |
| **Catálogo** | Consulta dos dados da barbearia, profissionais e serviços, incluindo preço e duração. |
| **Disponibilidade** | Visualização de datas e horários disponíveis para cada profissional. |
| **Agendamentos** | Seleção de serviço, profissional, data e horário; confirmação e acompanhamento da reserva. |
| **Agenda profissional** | Consulta de atendimentos do dia e da semana, com respectivos status. |
| **Histórico** | Consulta de agendamentos anteriores e de atendimentos realizados, conforme permissões. |

### 4.1 Perfis e necessidades

| Perfil | Necessidade principal |
|---|---|
| **Cliente** | Localizar um serviço e reservar um horário sem depender de contato manual. |
| **Barbeiro** | Consultar a agenda de trabalho e preparar os atendimentos. |
| **Administrador/proprietário** | Gerenciar a operação e acompanhar os agendamentos do estabelecimento. |

---

## 5. Banco de dados — MySQL (infraestrutura fora do escopo)

**Decisão:** MySQL como banco-alvo, com **infraestrutura fora do escopo de entrega**.

Fora do escopo de entrega:
- Provisionamento, instalação e configuração do servidor MySQL.
- Backup, restauração, alta disponibilidade e tuning de performance.
- Criação e administração de usuários/credenciais do banco.
- Escolha e contratação do serviço de hospedagem do banco.

Dentro do escopo do backend:
- Models, migrations e acesso via Django ORM.
- Configuração de conexão por variáveis de ambiente.
- Compatibilidade com MySQL (engine `InnoDB`, charset `utf8mb4`).
- Execução de migrations na instância fornecida, mediante permissão.

Premissas:
- Existirá uma instância MySQL disponível, com banco e usuário previamente criados.
- As credenciais e permissões serão fornecidas pelo responsável pelo banco.
- A versão do MySQL será definida pelo ambiente fornecido.

Configuração prevista:
- Variáveis de ambiente: `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`,
  `MYSQL_PORT` (ou `DATABASE_URL`).
- Driver: `mysqlclient` (recomendado) ou `PyMySQL` como alternativa pura Python.
- `USE_TZ=True`: datas armazenadas em UTC e convertidas para `America/Sao_Paulo` na API.
- Migrations gerenciadas pelo Django.
- SQLite não será utilizado.

Observação importante:
- O MySQL **não possui exclusion constraint**. A prevenção de sobreposição de horários será
  feita na camada de serviço com transação e bloqueio (`SELECT ... FOR UPDATE`), apoiada por
  índice composto em (`profissional`, `data_hora`) e testes automatizados.

---

## 6. Perfis e controle de acesso

| Ação | Visitante | Cliente | Barbeiro | Administrador/proprietário |
|---|---|---|---|---|
| Ver catálogo e disponibilidade | Sim | Sim | Sim | Sim |
| Cadastrar-se / autenticar-se | Sim | Sim | — | — |
| Agendar horário | Não | Sim | Não | Não |
| Ver e cancelar os próprios agendamentos | Não | Sim | Não | Não |
| Ver a agenda (dia/semana) | Não | Não | Sim (própria) | Sim (toda a barbearia) |
| Atualizar status dos atendimentos | Não | Não | Sim (próprios) | Sim (todos) |
| Gerenciar profissionais, serviços e disponibilidade | Não | Não | Não | Sim |
| Gerenciar os dados da barbearia | Não | Não | Não | Sim |
| Ver histórico geral | Não | Não | Não | Sim |

Regras de acesso:
- Todos os dados pertencem à única barbearia.
- Cliente só acessa os próprios agendamentos e o próprio histórico.
- Barbeiro só acessa a própria agenda e os próprios atendimentos.
- Administrador/proprietário gerencia a operação da barbearia.
- Permissões verificadas no backend; nenhum cliente da API é fonte de verdade.
- Django Admin restrito ao administrador/proprietário e staff autorizado.

---

## 7. Arquitetura

```
┌──────────────────────────────┐
│ Frontend/SPA (fora do escopo)│
└──────────────┬───────────────┘
               │ HTTP/JSON + JWT
┌──────────────▼───────────────┐
│ API REST — Django REST Framework │
│ serializers, viewsets, permissões │
│ autenticação JWT                  │
└──────────────┬───────────────┘
               │ Django ORM
┌──────────────▼───────────────┐        ┌──────────────────┐
│ Regras de domínio             │        │ Django Admin      │
│ accounts / catalog /          │◄───────│ backoffice        │
│ scheduling                    │        └──────────────────┘
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│ MySQL (externo)              │
└──────────────────────────────┘

Docker Compose: api (banco externo)
```

Responsabilidades:
- **Django**: models, migrations, regras de negócio, serviços de disponibilidade/agendamento,
  API REST e Admin.
- **DRF**: serializers, viewsets e permissões.
- **JWT**: autenticação stateless com access e refresh tokens.
- **MySQL (externo)**: persistência fornecida fora do escopo.
- **Docker**: ambiente reproduzível com o serviço `api`; o banco é externo.
- **Django Admin**: backoffice para o administrador/proprietário e staff.

O sistema atende **uma única barbearia**. Suporte a múltiplas barbearias ou unidades fica fora
do escopo desta entrega.

---

## 8. Escopo do MVP

### Dentro do escopo
- Cadastro e login de clientes.
- Criação de barbeiros e do administrador/proprietário.
- Configuração dos dados da barbearia.
- Catálogo de profissionais e serviços, com preço e duração.
- Disponibilidade semanal por profissional e horários livres por data.
- Agendamento com status `pendente`, `confirmado`, `concluido`, `cancelado`.
- Acompanhamento e cancelamento pelo cliente.
- Agenda do barbeiro por dia e por semana.
- Histórico conforme perfil.
- API REST cobrindo todos os módulos.
- Integração com uma instância MySQL existente (infraestrutura externa).
- Docker para a API.
- Testes automatizados das regras principais.

### Fora do escopo
- Frontend/SPA.
- FastAPI.
- Múltiplas barbearias ou unidades.
- Provisionamento, administração, backup e tuning do banco de dados.
- Pagamento online.
- Notificações por e-mail ou WhatsApp.
- App mobile nativo.
- Relatórios financeiros avançados.
- Fidelidade, cupons e promoções.
- Publicação em produção (a definir).

---

## 9. Stack prevista

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Framework | Django 5.x |
| API REST | Django REST Framework |
| Autenticação | JWT com `djangorestframework-simplejwt` (access + refresh + blacklist) |
| Banco | MySQL externo (driver `mysqlclient` ou `PyMySQL`) |
| CORS | `django-cors-headers` para o frontend futuro |
| Ambiente | Docker + Docker Compose |
| Testes | pytest + pytest-django |
| Qualidade | ruff |
| Idioma/fuso | pt-BR, `America/Sao_Paulo` |

---

## 10. Estrutura de pastas prevista

```
Barbearia APP/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── config/                     # projeto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                   # Contas e perfis
│   ├── models.py               # Usuario(AbstractUser) + perfil
│   ├── admin.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py
│   └── tests/
├── catalog/                    # Catálogo
│   ├── models.py               # Barbearia, Profissional, Servico
│   ├── admin.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
├── scheduling/                 # Disponibilidade, Agendamentos, Agenda, Histórico
│   ├── models.py               # Disponibilidade, Agendamento
│   ├── services.py             # slots e conflitos
│   ├── admin.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── management/commands/seed_demo.py
│   └── tests/
├── Dockerfile
├── docker-compose.yml
├── README.md
└── PLANO.md
```

---

## 11. Modelo de dados (MVP)

```
Barbearia (registro único)             # catalog
  proprietario  -> FK Usuario (perfil administrador)
  nome, descricao, endereco, cidade, telefone, email

Usuario(AbstractUser)                 # accounts
  perfil        -> cliente | barbeiro | administrador
  telefone
  is_staff/is_superuser (Admin)

Profissional                          # catalog
  usuario       -> FK Usuario (perfil barbeiro)
  especialidades, bio, ativo
  (1 profissional por usuário)

Servico                               # catalog
  nome, descricao, duracao_minutos, preco, ativo

Disponibilidade                       # scheduling
  profissional  -> FK Profissional
  dia_semana    -> 0..6
  hora_inicio, hora_fim
  (vários blocos por dia permitidos)

Agendamento                           # scheduling
  cliente       -> FK Usuario (perfil cliente)
  profissional  -> FK Profissional
  servico       -> FK Servico
  data_hora     -> datetime (timezone tratado na aplicação: America/Sao_Paulo)
  duracao_minutos (copiada do serviço)
  preco         (copiada do serviço)
  status        -> pendente | confirmado | concluido | cancelado
  observacoes
  criado_em / atualizado_em
```

Índices e constraints previstos:
- `Barbearia` com apenas um registro (singleton).
- `Usuario.telefone` único.
- Índices em `profissional_id`, `cliente_id`, `data_hora` e `status`.
- Índice composto em (`profissional`, `data_hora`) para consultas de agenda e conflito.
- MySQL não possui exclusion constraint: a sobreposição de horários é impedida por
  transação com bloqueio (`SELECT ... FOR UPDATE`) em `scheduling/services.py`.
- Testes automatizados cobrindo concorrência e conflito de horários.

Regras de negócio:
- Horário deve estar dentro de um bloco de `Disponibilidade` do profissional.
- Não pode haver dois agendamentos ativos (`pendente`/`confirmado`) sobrepostos para o mesmo
  profissional.
- `data_hora` não pode estar no passado.
- A duração do serviço ocupa o slot; o próximo horário só libera após o término.
- Ao cancelar, o horário volta a ficar disponível.
- Preço e duração são copiados no agendamento para preservar o histórico.
- Cliente só acessa os próprios agendamentos.
- Barbeiro só acessa a própria agenda.
- Administrador/proprietário gerencia a operação da barbearia.

---

## 12. API REST prevista

### Autenticação (JWT)
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/auth/register` | Cadastro de cliente |
| POST | `/api/auth/login` | Login e emissão de access + refresh tokens |
| POST | `/api/auth/refresh` | Renovação do access token |
| POST | `/api/auth/logout` | Invalidação do refresh token (blacklist) |
| GET | `/api/me` | Dados do usuário autenticado |
| PATCH | `/api/me` | Atualizar perfil |

### Barbearia
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/barbershop` | Dados públicos da barbearia |
| PATCH | `/api/admin/barbershop` | Atualizar dados da barbearia (administrador) |

### Catálogo
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/professionals` | Listar profissionais ativos |
| GET | `/api/professionals/{id}` | Perfil do profissional |
| GET | `/api/services` | Listar serviços com preço e duração |
| GET | `/api/services/{id}` | Detalhe do serviço |

### Disponibilidade
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/professionals/{id}/availability?date=AAAA-MM-DD` | Horários livres na data |
| GET | `/api/professionals/{id}/availability?from=...&to=...` | Dias com vaga no período |

### Agendamentos
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/appointments` | Criar agendamento |
| GET | `/api/appointments` | Meus agendamentos (cliente) |
| GET | `/api/appointments/{id}` | Detalhe da reserva |
| PATCH | `/api/appointments/{id}/cancel` | Cancelar reserva |

### Agenda profissional
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/me/agenda?date=AAAA-MM-DD` | Atendimentos do dia |
| GET | `/api/me/agenda/week?date=AAAA-MM-DD` | Atendimentos da semana |
| PATCH | `/api/me/agenda/{id}/status` | Confirmar/concluir/cancelar |

### Histórico
| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/me/history` | Histórico do cliente |
| GET | `/api/me/history/professional` | Atendimentos realizados (barbeiro) |
| GET | `/api/admin/history` | Histórico geral (administrador) |

### Administração
| Método | Endpoint | Descrição |
|---|---|---|
| GET/POST | `/api/admin/professionals` | Gerenciar profissionais |
| GET/PATCH/DELETE | `/api/admin/professionals/{id}` | Detalhar/editar/desativar profissional |
| GET/POST | `/api/admin/services` | Gerenciar serviços |
| GET/PATCH/DELETE | `/api/admin/services/{id}` | Detalhar/editar/desativar serviço |
| GET/PUT | `/api/admin/availability` | Gerenciar disponibilidade |
| GET | `/api/admin/appointments` | Acompanhar todos os agendamentos |

### Backoffice
| Recurso | Descrição |
|---|---|
| `/admin/` | Django Admin (administrador/proprietário e staff) |

---

## 13. Etapas de implementação

### Fase 0 — Fundação
- [ ] Criar repositório e `.gitignore`.
- [ ] Configurar Django, locale `pt-br` e timezone `America/Sao_Paulo`.
- [ ] Configurar conexão com MySQL existente e driver (`mysqlclient` ou `PyMySQL`).
- [ ] Configurar DRF, SimpleJWT e CORS.
- [ ] Criar `Dockerfile` e `docker-compose.yml` (`api`; banco externo).
- [ ] Criar `.env.example`.

**Entrega:** ambiente reproduzível via Docker com a API conectada ao MySQL fornecido e DRF configurado.

### Fase 1 — Contas e perfis
- [ ] Criar `accounts` com `Usuario(AbstractUser)` e campo `perfil`
  (`cliente`, `barbeiro`, `administrador`).
- [ ] Configurar `AUTH_USER_MODEL` antes da primeira migration.
- [ ] Implementar cadastro, login, refresh, logout e `/api/me` com JWT.
- [ ] Implementar permissões por perfil e por objeto.
- [ ] Configurar criação do administrador/proprietário.
- [ ] Criar testes de cadastro, login, tokens e permissões.

**Entrega:** autenticação JWT funcionando e rotas protegidas por perfil.

### Fase 2 — Catálogo
- [ ] Criar `Barbearia` (registro único), `Profissional` e `Servico`.
- [ ] Registrar no Admin com busca e filtros.
- [ ] Implementar endpoints de dados da barbearia, profissionais e serviços.
- [ ] Exibir preço e duração dos serviços.
- [ ] Implementar edição dos dados da barbearia pelo administrador.
- [ ] Criar `seed_demo` com a barbearia, profissionais e serviços de exemplo.
- [ ] Testes de catálogo e permissões.

**Entrega:** catálogo da barbearia disponível na API.

### Fase 3 — Disponibilidade
- [ ] Criar `Disponibilidade`.
- [ ] Implementar geração de slots em `scheduling/services.py`.
- [ ] Considerar duração do serviço, agendamentos existentes e horários passados.
- [ ] Implementar endpoints de disponibilidade por data e período.
- [ ] Testes de geração de slots.

**Entrega:** horários livres calculados corretamente.

### Fase 4 — Agendamentos
- [ ] Criar `Agendamento` com status e cópia de preço/duração.
- [ ] Implementar criação de agendamento com validação transacional.
- [ ] Implementar listagem, detalhe e cancelamento.
- [ ] Restringir acesso aos próprios agendamentos.
- [ ] Testes de conflito, data passada e cancelamento.

**Entrega:** cliente reserva e acompanha pela API.

### Fase 5 — Agenda profissional
- [ ] Implementar visão de dia e semana.
- [ ] Exibir cliente, serviço, horário e status.
- [ ] Implementar atualização de status.
- [ ] Restringir à própria agenda (barbeiro) ou a toda a agenda (administrador).
- [ ] Testes de acesso e transição de status.

**Entrega:** barbeiro opera sua agenda.

### Fase 6 — Histórico
- [ ] Histórico do cliente.
- [ ] Histórico do barbeiro.
- [ ] Histórico geral para o administrador.
- [ ] Filtros por período e status.
- [ ] Testes de permissão.

**Entrega:** histórico disponível conforme perfil.

### Fase 7 — Qualidade e documentação
- [ ] Testes de integração dos fluxos principais.
- [ ] Lint com ruff.
- [ ] README com instalação, Docker, variáveis de ambiente e uso da API.
- [ ] Revisão de segurança (JWT, permissões, segredos, CORS, DEBUG).
- [ ] Checklist de aceite do MVP.

**Entrega:** backend documentado e testado.

---

## 14. Como rodar (previsto)

```bash
# Com Docker
docker compose up --build

# Backend local (alternativa)
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # configurar conexão com MySQL existente
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

O `docker compose` sobe apenas a API. A instância MySQL deve ser fornecida externamente e
configurada no `.env`.

Acessos previstos:
- API: `http://localhost:8000/api`
- Admin: `http://localhost:8000/admin/`

---

## 15. Critérios de aceite do MVP

**Contas e perfis**
1. Cliente consegue se cadastrar, entrar e sair.
2. Login retorna access e refresh tokens; refresh renova o acesso.
3. Cada perfil acessa apenas o que lhe é permitido.
4. Cliente não acessa agendamento de outro cliente.

**Catálogo**
5. É possível listar profissionais e serviços ativos.
6. Preço e duração aparecem em cada serviço.
7. Administrador consegue editar os dados da barbearia, profissionais e serviços.
8. Visitante e cliente conseguem consultar os dados públicos da barbearia.

**Disponibilidade**
9. Horários exibidos respeitam a disponibilidade semanal do profissional.
10. Horários ocupados e passados não aparecem.

**Agendamentos**
11. Fluxo de agendamento gera status `pendente`.
12. Sistema bloqueia conflito de horário e data no passado.
13. Cliente acompanha e cancela a própria reserva; horário é liberado.

**Agenda profissional**
14. Barbeiro vê atendimentos do dia e da semana com status.
15. Barbeiro confirma/conclui os próprios atendimentos.

**Histórico**
16. Cliente vê apenas o próprio histórico.
17. Barbeiro vê os próprios atendimentos.
18. Administrador vê o histórico geral da barbearia.

**Global**
19. API cobrindo todos os módulos.
20. Testes automatizados passam.
21. API sobe com Docker e conecta ao MySQL fornecido, executando migrations.

---

## 16. Riscos e decisões

| Risco / decisão | Mitigação |
|---|---|
| Conflito de horários | Transação com lock (`SELECT ... FOR UPDATE`) + índice composto + testes; MySQL não possui exclusion constraint |
| Segurança dos tokens JWT | Access token curto, refresh com blacklist e rotação |
| Dependência de MySQL externo | Credenciais, disponibilidade e permissões acordadas com o responsável pelo banco; migrations testadas no ambiente fornecido |
| Backup e performance do banco fora do escopo | Responsabilidade do provedor do banco; registrar como dependência externa |
| Fuso horário | Datetimes armazenados em UTC e convertidos para `America/Sao_Paulo` na API |
| Serviço mudar de preço e alterar histórico | Copiar preço/duração no agendamento |
| Escopo crescer | MVP limitado aos 6 módulos e sem extras |
| Necessidade futura de múltiplas unidades | Modelo atual é de uma barbearia; migração futura exigirá análise |
| Segredos no Git | `.env` fora do versionamento + `.env.example` |
| Publicação indefinida | Docker mantém o ambiente portável |

---

## 17. Próximos passos

1. Definir **onde publicar** (pode ficar para depois).
2. Iniciar a **Fase 0**: fundação do projeto, integração com MySQL externo, DRF, JWT e Docker.
