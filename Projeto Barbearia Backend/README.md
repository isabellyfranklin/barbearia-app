# Barbearia API — Backend de Agendamento

Backend em **Python** para a plataforma web responsiva descrita na 1ª entrega do Projeto Integrador (SENAC). O sistema permite que clientes consultem o catálogo de barbearias e horários livres, façam agendamentos com pagamento, acompanhem o status e consultem o histórico. Barbeiros visualizam a própria agenda e o proprietário gerencia serviços, profissionais, expedientes e relatórios.

## Tecnologias

| Camada | Tecnologia |
| --- | --- |
| Linguagem | Python 3.10+ |
| Framework web | FastAPI |
| Banco de dados | SQLite (padrão) ou PostgreSQL via `DATABASE_URL` |
| ORM | SQLAlchemy 2.0 |
| Autenticação | JWT (PyJWT) + hash de senha com scrypt |
| Validação | Pydantic v2 |
| Testes | Pytest + TestClient |
| Documentação | OpenAPI/Swagger em `/docs` |

## Estrutura do projeto

```
app/
  main.py                 # criacao da API, CORS, registro dos routers
  config.py               # configuracoes (.env)
  database.py             # engine, sessao e Base do SQLAlchemy
  models.py               # entidades do banco
  schemas.py              # contratos de entrada/saida (Pydantic)
  enums.py                # papeis, status de agendamento e pagamento
  security.py             # hash de senha e JWT
  deps.py                 # autenticacao e regras de acesso
  utils.py                # conversao de datas/fusos horarios
  seed.py                 # dados de demonstracao
  services/
    availability.py       # calculo de horarios livres e validacao de conflitos
    appointments.py       # criacao, cancelamento, status e pagamento
    reports.py            # agregacoes dos relatorios
  routers/
    auth.py               # cadastro, login, perfil e onboarding da barbearia
    barbershops.py        # catalogo e gestao de barbearias
    services.py           # catalogo e gestao de servicos
    barbers.py            # barbeiros, expediente e bloqueios de agenda
    availability.py       # consulta de horarios disponiveis
    appointments.py       # agendamentos, historico e pagamentos
    reports.py            # relatorios gerenciais
tests/                    # testes automatizados dos fluxos principais
```

## Como executar

### 1. Instalar o Python

No Windows, se o comando `python` nao existir:

```powershell
winget install -e --id Python.Python.3.12
```

Feche e abra o terminal novamente.

### 2. Criar o ambiente virtual e instalar dependencias

```powershell
cd "C:\Users\cleba\OneDrive\Documentos\Projeto Padrão"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Se a ativacao for bloqueada pelo PowerShell, execute uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 3. Configurar o ambiente

```powershell
Copy-Item .env.example .env
```

Ajuste `JWT_SECRET` se desejar. O SQLite (`barbearia.db`) e criado automaticamente.

### 4. Popular dados de demonstracao (opcional)

```powershell
python -m app.seed
```

Contas criadas (senha `senha123` para todas):

| Perfil | E-mail |
| --- | --- |
| Administrador / proprietario | `carlos@barbearia.com` |
| Barbeiro | `joao@barbearia.com` |
| Barbeiro | `rafael@barbearia.com` |
| Cliente | `lucas@cliente.com` |

### 5. Iniciar a API

```powershell
uvicorn app.main:app --reload
```

- API: http://localhost:8000/api/v1
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Fluxo rapido (PowerShell)

```powershell
# Login do cliente
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/login `
  -ContentType 'application/json' `
  -Body '{"email":"lucas@cliente.com","password":"senha123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# Catalogo
Invoke-RestMethod http://localhost:8000/api/v1/barbershops
Invoke-RestMethod http://localhost:8000/api/v1/barbershops/1

# Horarios livres (data local de Sao Paulo)
Invoke-RestMethod "http://localhost:8000/api/v1/barbershops/1/availability?service_id=1&date=2026-11-16"

# Agendamento (use um inicio retornado pela consulta acima)
$body = @{
  barbershop_id = 1
  service_id = 1
  barber_id = 1
  start_at = "2026-11-16T12:00:00Z"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/appointments `
  -Headers $headers -ContentType 'application/json' -Body $body

# Pagamento (confirma o agendamento)
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/appointments/1/payment `
  -Headers $headers -ContentType 'application/json' -Body '{"method":"PIX"}'
```

## Endpoints principais

Todas as rotas (exceto login, cadastro e catalogo publico) usam `Authorization: Bearer <token>`.

### Autenticacao

| Metodo | Rota | Descricao |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Cadastro de cliente |
| POST | `/api/v1/auth/register/barbershop` | Cria proprietario + barbearia |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| GET | `/api/v1/auth/me` | Perfil autenticado |
| PATCH | `/api/v1/auth/me` | Atualiza nome, telefone ou senha |

### Barbearias e servicos

| Metodo | Rota | Quem pode |
| --- | --- | --- |
| GET | `/api/v1/barbershops` | Publico (busca por `search` e `city`) |
| GET | `/api/v1/barbershops/{id}` | Publico (inclui servicos e barbeiros) |
| GET | `/api/v1/barbershops/mine` | Admin/barbeiro autenticado |
| POST | `/api/v1/barbershops` | Administrador |
| PATCH | `/api/v1/barbershops/{id}` | Proprietario |
| GET | `/api/v1/barbershops/{id}/services` | Publico |
| POST | `/api/v1/barbershops/{id}/services` | Proprietario |
| PATCH/DELETE | `/api/v1/services/{id}` | Proprietario |

### Barbeiros e agenda

| Metodo | Rota | Quem pode |
| --- | --- | --- |
| GET | `/api/v1/barbershops/{id}/barbers` | Publico |
| POST | `/api/v1/barbershops/{id}/barbers` | Proprietario (cria login do barbeiro) |
| GET | `/api/v1/barbers/me` | Barbeiro |
| PATCH | `/api/v1/barbers/{id}` | Proprietario ou o proprio barbeiro |
| PUT | `/api/v1/barbers/{id}/services` | Proprietario |
| GET/POST | `/api/v1/barbers/{id}/working-hours` | Leitura publica; escrita dono/barbeiro |
| PATCH/DELETE | `/api/v1/working-hours/{id}` | Dono/barbeiro |
| GET/POST | `/api/v1/barbers/{id}/time-off` | Dono/barbeiro |
| DELETE | `/api/v1/time-off/{id}` | Dono/barbeiro |

### Disponibilidade e agendamentos

| Metodo | Rota | Descricao |
| --- | --- | --- |
| GET | `/api/v1/barbershops/{id}/availability?service_id=1&date=2026-11-16&barber_id=1` | Horarios livres por barbeiro |
| POST | `/api/v1/appointments` | Cria agendamento (cliente ou admin com `client_id`) |
| GET | `/api/v1/appointments` | Lista com escopo por perfil e filtros |
| GET | `/api/v1/appointments/history` | Historico de atendimentos |
| GET | `/api/v1/appointments/{id}` | Detalhe |
| PATCH | `/api/v1/appointments/{id}/status` | Barbeiro/admin alteram status |
| POST | `/api/v1/appointments/{id}/cancel` | Cliente, barbeiro ou admin |
| POST | `/api/v1/appointments/{id}/payment` | Registra pagamento (`PIX`, `CREDIT_CARD`, `DEBIT_CARD`, `CASH`) |

### Relatorios (proprietario)

```
GET /api/v1/barbershops/{id}/reports/summary?start_date=2026-11-01&end_date=2026-11-30
```

Retorna faturamento pago e pendente, ticket medio, contagem por status, servicos mais vendidos, desempenho por barbeiro e evolucao diaria. Periodo maximo de 366 dias.

## Regras de negocio implementadas

- **Conflito de agenda**: um barbeiro nao pode ter dois agendamentos sobrepostos (`PENDING` ou `CONFIRMED`). A criacao revalida o horario dentro de um lock por barbeiro e usa restricao unica no banco.
- **Disponibilidade**: calculada a partir do expediente semanal do barbeiro, duracao do servico, bloqueios (`time-off`), agendamentos ativos, antecedencia minima e fuso horario da barbearia.
- **Fuso horario**: instantes sao gravados em UTC e devolvidos em ISO 8601 com `Z`; horarios sem fuso na entrada sao interpretados no fuso da barbearia.
- **Pagamento**: ao pagar, o agendamento pendente passa para `CONFIRMED`; cancelamento de agendamento pago gera estorno (`REFUNDED`).
- **Transicoes de status**: `PENDING -> CONFIRMED/CANCELED/NO_SHOW`, `CONFIRMED -> COMPLETED/CANCELED/NO_SHOW`. Estados finais nao voltam atras.
- **Permissoes**: cliente so acessa os proprios dados; barbeiro acessa apenas a propria agenda; administrador acessa apenas as barbearias que possui.
- **Soft delete** de servicos (`DELETE` apenas desativa), preservando o historico.

## Testes

```powershell
pytest
```

Os testes cobrem cadastro/login, onboarding, disponibilidade, conflito de horarios, pagamento, cancelamento com estorno, permissoes por perfil, bloqueios de agenda, expediente e relatorios.

## Notas para producao

- Troque `JWT_SECRET` por um valor aleatorio longo e mantenha `SEED_ON_STARTUP=false`.
- Restrinja `CORS_ORIGINS` ao dominio do front-end.
- Use PostgreSQL e um servico de e-mail/notificacao para lembretes.
- O lock de agendamento e local ao processo; com varios workers, use `SELECT ... FOR UPDATE` ou uma constraint de exclusao no banco.
- Sirva a API atras de HTTPS e configure backup do banco.
