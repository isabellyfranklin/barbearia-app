# Prumo — back-end Django REST

Servidor Django do Prumo. A API REST atende o front-end de cadastro, reservas,
agenda do barbeiro e administração. Consulte o [contrato da API](../../docs/API.md).

## Instalação

Python 3.12 e MySQL (8.4 como alvo do grupo), com InnoDB e utf8mb4.

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
~~~

Configure MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST e MYSQL_PORT.
Gere SECRET_KEY aleatória com django.core.management.utils.get_random_secret_key.
DEBUG=True é somente para desenvolvimento. Antes de publicar, use DEBUG=False,
SECRET_KEY própria, HTTPS e ALLOWED_HOSTS/CORS_ALLOWED_ORIGINS restritos.
CORS_ALLOWED_ORIGINS recebe as origens do front-end, sem caminhos.

~~~powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
~~~

O comando opcional python manage.py seed_demo popula dados fictícios.
Não execute seed_demo em produção: suas credenciais de demonstração são públicas.

## Endereços

- Prefixo da API JSON: /api/v1
- Swagger local: /api/v1/docs
- OpenAPI: /api/v1/schema (Accept: application/json para JSON)
- Prontidão: /api/v1/health (200 ou 503)
- Backoffice: /admin/

Rotas REST sem barra final. O Admin segue a convenção Django com barra final.
Os aliases preliminares /api/ permanecem temporariamente disponíveis;
o front-end usa /api/v1. Não há compatibilidade com rotas FastAPI.

## Testes e contrato

Use MySQL de desenvolvimento e um usuário que possa criar/remover o banco de teste.

~~~powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
python -m ruff check .
python manage.py spectacular --file ../../docs/openapi.yaml --validate --fail-on-warn
~~~

A suíte inclui conexões independentes em MySQL para validar reservas simultâneas
e confirmação versus cancelamento. Esses casos são ignorados em SQLite,
que não comprova SELECT FOR UPDATE.

## Docker

~~~powershell
docker compose up --build
~~~

O Compose sobe apenas a API; MySQL é externo. Em Docker Desktop, use
MYSQL_HOST=host.docker.internal para um servidor no host, quando apropriado.
O entrypoint aplica migrations e collectstatic. Gunicorn atende a API e
WhiteNoise serve os estáticos do Admin e Swagger, sem depender de CDN.
O build Docker precisa ser validado no ambiente da equipe.

## Organização

accounts: contas/JWT/perfil/senha; catalog: barbearia/profissionais/serviços;
scheduling: disponibilidade/reservas/agendas/histórico; config: configuração/contrato.
Agendamentos no Django Admin são somente para consulta; alterações passam pela API.
Os models e as migrations existentes não foram reescritos.
