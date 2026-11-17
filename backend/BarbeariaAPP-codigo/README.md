# Barbearia APP — Backend

Backend de um sistema de agendamentos para **uma única barbearia**. A API REST permite que
clientes consultem serviços e horários livres e reservem atendimentos, que barbeiros
acompanhem sua agenda e que o administrador/proprietário gerencie a operação.

Este repositório contém **somente o backend**. Frontend/SPA, pagamentos, notificações e
aplicativo mobile estão fora do escopo.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Framework | Django 5.1–5.2 |
| API | Django REST Framework |
| Autenticação | JWT (`djangorestframework-simplejwt`, access + refresh + blacklist) |
| Banco de dados | MySQL 8+ (instância externa) |
| Driver MySQL | PyMySQL (instalado como `MySQLdb`) |
| Ambiente | Docker + Docker Compose |
| Testes | pytest + pytest-django |
| Lint | ruff |
| Idioma / fuso | pt-BR / `America/Sao_Paulo` |

---

## Estrutura

```
.
├── manage.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── pyproject.toml
├── config/                     # configuração do projeto
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                   # usuários, perfis, JWT
│   ├── models.py               # Usuario(AbstractUser) + perfil
│   ├── managers.py
│   ├── permissions.py          # IsCliente, IsBarbeiro, IsAdministrador
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
├── catalog/                    # barbearia, profissionais e serviços
│   ├── models.py               # Barbearia (singleton), Profissional, Servico
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
├── scheduling/                 # disponibilidade, agendamentos, agenda, histórico
│   ├── models.py               # Disponibilidade, Agendamento
│   ├── services.py             # slots, conflitos e transições de status
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── management/commands/seed_demo.py
│   └── tests/
├── PLANO.md
└── README.md
```

---

## Pré-requisitos

- Python 3.10+ (para execução local)
- Docker e Docker Compose (opcional)
- Uma instância **MySQL 8+** já existente, com banco e usuário criados

> A infraestrutura do banco (provisionamento, backup, tuning, credenciais) **não faz parte
> desta entrega**. A aplicação apenas se conecta à instância fornecida.

---

## Configuração

Copie o arquivo de exemplo e ajuste os valores:

```bash
copy .env.example .env
```

Variáveis disponíveis:

| Variável | Descrição | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave secreta do Django | valor inseguro de desenvolvimento |
| `DEBUG` | Modo de depuração | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos (separados por vírgula) | `localhost,127.0.0.1` |
| `MYSQL_DATABASE` | Nome do banco | `barbearia` |
| `MYSQL_USER` | Usuário do banco | `barbearia` |
| `MYSQL_PASSWORD` | Senha do banco | — |
| `MYSQL_HOST` | Host do MySQL | `127.0.0.1` |
| `MYSQL_PORT` | Porta do MySQL | `3306` |
| `CORS_ALLOWED_ORIGINS` | Origens permitidas para o frontend futuro | `http://localhost:3000` |
| `CORS_ALLOW_ALL_ORIGINS` | Liberar qualquer origem (não recomendado em produção) | `False` |
| `CSRF_TRUSTED_ORIGINS` | Origens confiáveis para CSRF | vazio |

O banco deve usar `InnoDB` e `utf8mb4`. As migrations são aplicadas pela própria aplicação.

---

## Rodando com Docker

O `docker compose` sobe **apenas o serviço `api`**; o MySQL é externo.

```bash
# 1. Configure o .env com a instância MySQL existente
# 2. Suba a API (as migrations são aplicadas automaticamente na inicialização)
docker compose up --build

# 3. (Opcional) crie o administrador
docker compose run --rm api python manage.py createsuperuser

# 4. (Opcional) carregue os dados de demonstração
docker compose run --rm api python manage.py seed_demo
```

Acessos:

- API: `http://localhost:8000/api`
- Django Admin: `http://localhost:8000/admin/`

---

## Rodando localmente

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/macOS

python -m pip install -r requirements.txt
copy .env.example .env             # configure a conexão MySQL

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

---

## Dados de demonstração (`seed_demo`)

O comando é idempotente e cria:

| Usuário | Senha | Perfil |
|---|---|---|
| `admin` | `admin123` | Administrador/proprietário |
| `joao` | `barbeiro123` | Barbeiro |
| `carlos` | `barbeiro123` | Barbeiro |
| `cliente` | `cliente123` | Cliente |

Também cria a barbearia, serviços (corte, barba, combo e sobrancelha) e a disponibilidade
semanal dos profissionais (segunda a sábado, com intervalo de almoço).

> Troque essas credenciais antes de qualquer uso real.

---

## Autenticação

A API usa JWT no cabeçalho `Authorization: Bearer <access>`.

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/auth/register` | Cadastro de cliente (retorna tokens) |
| POST | `/api/auth/login` | Login (retorna access, refresh e usuário) |
| POST | `/api/auth/refresh` | Renova o access token |
| POST | `/api/auth/logout` | Invalida o refresh token (blacklist) |
| GET/PATCH | `/api/me` | Consulta/atualiza o próprio perfil |

Exemplo:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"cliente\", \"password\": \"cliente123\"}"
```

```json
{
  "refresh": "...",
  "access": "...",
  "user": {"id": 4, "username": "cliente", "perfil": "cliente", "...": "..."}
}
```

---

## Endpoints

Os endpoints **não usam barra final**.

### Barbearia e catálogo

| Método | Endpoint | Acesso |
|---|---|---|
| GET | `/api/barbershop` | Público |
| PATCH | `/api/admin/barbershop` | Administrador |
| GET | `/api/professionals` | Público |
| GET | `/api/professionals/{id}` | Público |
| GET | `/api/services` | Público |
| GET | `/api/services/{id}` | Público |
| GET/POST | `/api/admin/professionals` | Administrador |
| GET/PATCH/DELETE | `/api/admin/professionals/{id}` | Administrador |
| GET/POST | `/api/admin/services` | Administrador |
| GET/PATCH/DELETE | `/api/admin/services/{id}` | Administrador |

### Disponibilidade

| Método | Endpoint | Acesso |
|---|---|---|
| GET | `/api/professionals/{id}/availability?date=AAAA-MM-DD[&service=ID]` | Público |
| GET | `/api/professionals/{id}/availability?from=AAAA-MM-DD&to=AAAA-MM-DD` | Público |
| GET/POST | `/api/admin/availability` | Administrador |
| GET/PATCH/DELETE | `/api/admin/availability/{id}` | Administrador |

### Agendamentos

| Método | Endpoint | Acesso |
|---|---|---|
| POST | `/api/appointments` | Cliente |
| GET | `/api/appointments` | Cliente (próprios) |
| GET | `/api/appointments/{id}` | Cliente/barbeiro/admin conforme vínculo |
| PATCH | `/api/appointments/{id}/cancel` | Cliente (próprios) |
| GET | `/api/admin/appointments` | Administrador |
| GET | `/api/admin/history` | Administrador |

### Agenda e histórico

| Método | Endpoint | Acesso |
|---|---|---|
| GET | `/api/me/agenda?date=AAAA-MM-DD` | Barbeiro (própria) / Administrador (toda) |
| GET | `/api/me/agenda/week?date=AAAA-MM-DD` | Barbeiro / Administrador |
| PATCH | `/api/me/agenda/{id}/status` | Barbeiro (próprios) / Administrador |
| GET | `/api/me/history` | Cliente (próprio) |
| GET | `/api/me/history/professional` | Barbeiro (próprio) |

Filtros disponíveis em listagens de agendamentos/histórico: `status`, `from`, `to`
(datas no formato `AAAA-MM-DD`).

Exemplo de criação de agendamento:

```bash
curl -X POST http://localhost:8000/api/appointments \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d "{\"profissional\": 1, \"servico\": 1, \"data_hora\": \"2026-11-16T10:00:00-03:00\"}"
```

---

## Regras de negócio

- **Perfis:** `cliente`, `barbeiro`, `administrador`. O superusuário do Django é tratado
  como administrador.
- **Uma barbearia:** `Barbearia` é um registro único (pk=1), sem isolamento multi-tenant.
- **Preço e duração** são copiados do serviço no momento da reserva, preservando o histórico.
- **Status:** `pendente → confirmado → concluido` ou `pendente/confirmado → cancelado`.
  Transições inválidas retornam `400`.
- **Horário válido:** precisa estar dentro de um bloco de `Disponibilidade` do profissional,
  no futuro e sem sobreposição com outro agendamento ativo.
- **Slots:** gerados a cada 30 minutos; a duração do serviço ocupa o intervalo e o horário
  só é liberado após o término.
- **Conflitos:** o MySQL não possui exclusion constraint. A criação do agendamento usa
  `transaction.atomic()` + `SELECT ... FOR UPDATE` no profissional, com índice composto em
  `(profissional, data_hora)`.
- **Cancelamento** libera o horário para novas reservas.
- **Fuso horário:** datas são armazenadas em UTC e expostas em `America/Sao_Paulo`.

---

## Testes

Os testes usam pytest + pytest-django e exigem um MySQL acessível, pois é o banco-alvo do
projeto.

```bash
python -m pytest
```

Cobertura principal:

- cadastro, login, refresh/logout e permissões;
- catálogo público e administração;
- geração de slots e duração do serviço;
- conflito de horário, data passada e disponibilidade;
- cancelamento e transições de status;
- acesso do cliente, do barbeiro e do administrador.

Para rodar sem MySQL (apenas validação local), crie um módulo de settings temporário com
SQLite e execute `python -m pytest --ds=config.settings_test`. Esse módulo **não faz parte
da entrega**.

---

## Qualidade

```bash
python -m ruff check .
```

Configuração em `pyproject.toml` (linha de 100 caracteres, regras `E`, `F`, `I`, `B`).

---

## Segurança e produção

- Defina `SECRET_KEY` forte e `DEBUG=False`.
- Restrinja `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS`.
- Use HTTPS e mantenha o `.env` fora do versionamento.
- O access token dura 30 minutos; o refresh, 1 dia, com rotação e blacklist.
- O Django Admin deve ficar restrito ao administrador/proprietário e staff autorizado.
