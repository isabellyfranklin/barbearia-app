# Prumo — back-end Django REST

O back-end gerencia contas, catálogo, disponibilidade, agendamentos e agendas.
A API usa Django 5.2, Django REST Framework, JWT e MySQL 8.4 como alvo.
Para iniciar também a interface web, siga o [guia da raiz](../../README.md).

## Instalação local

Use Python 3.12 e um banco MySQL com InnoDB e `utf8mb4`. O
[guia do banco](../../database/README.md#preparar-o-banco-local) detalha a
criação do banco e do usuário. Execute os comandos a seguir nesta pasta, onde
está o `manage.py`.

**Linux e macOS**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

**Windows com PowerShell**

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

Em seguida, instale as dependências e gere uma chave para o `.env`.

```sh
python -m pip install -r requirements.txt
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Variáveis de ambiente

O Django carrega o `.env` desta pasta. Use o [arquivo de exemplo](.env.example)
e mantenha a configuração com credenciais reais fora do Git.

| Variável | Configuração |
| --- | --- |
| `SECRET_KEY` | Cole a chave aleatória gerada acima. |
| `DEBUG` | Use `True` localmente e `False` em produção. |
| `ALLOWED_HOSTS` | Nomes de host permitidos para a API, separados por vírgula, sem protocolo ou porta. Exemplo local `localhost,127.0.0.1`. |
| `MYSQL_DATABASE` | Nome do banco criado no MySQL. O exemplo usa `barbearia`. |
| `MYSQL_USER` e `MYSQL_PASSWORD` | Credenciais da conta MySQL com acesso ao banco. |
| `MYSQL_HOST` e `MYSQL_PORT` | Endereço e porta do MySQL. O exemplo local usa `127.0.0.1` e `3306`. |
| `CORS_ALLOWED_ORIGINS` | Origens permitidas para o front-end, separadas por vírgula. Inclua protocolo e porta quando aplicável, sem caminho. Exemplo `http://localhost:3000`. |
| `CORS_ALLOW_ALL_ORIGINS` | Mantenha `False` para usar a lista de origens configurada. |
| `CSRF_TRUSTED_ORIGINS` | Origens confiáveis para requisições sujeitas a CSRF, como as do Django Admin. Preencha quando a implantação exigir, com protocolo e porta quando aplicável. |

### Migrações e inicialização

```sh
python manage.py migrate
python manage.py runserver
```

Para explorar o fluxo em um banco novo de desenvolvimento, execute
`python manage.py seed_demo` depois de migrar. O comando popula a barbearia,
o catálogo, as contas e os horários semanais de demonstração. Restrinja seu uso
a bancos de desenvolvimento, pois as contas têm senhas públicas. Para criar uma
conta própria com acesso ao Django Admin, execute `python manage.py createsuperuser`.

## Endereços e contrato

| Endereço local | Uso |
| --- | --- |
| [Prontidão](http://localhost:8000/api/v1/health) | Retorna HTTP 200 quando a consulta ao banco funciona e HTTP 503 em caso de falha. |
| [Swagger](http://localhost:8000/api/v1/docs) | Interface interativa para explorar a API. |
| [OpenAPI](http://localhost:8000/api/v1/schema) | Especificação da API. Envie `Accept: application/json` para receber JSON. |
| [Django Admin](http://localhost:8000/admin/) | Backoffice Django. Os agendamentos são exibidos para consulta e suas alterações passam pela API. |

Use `/api/v1` como prefixo nas integrações e omita a barra final nas rotas REST.
O Django Admin usa barra final. Os aliases antigos em `/api/` são temporários.
Para autenticar uma requisição protegida, obtenha o token de acesso em
`POST /api/v1/auth/login` e envie o cabeçalho `Authorization: Bearer <access>`.
Os payloads, perfis permitidos e filtros estão no [contrato REST](../../docs/API.md).

## Testes e manutenção

Com o ambiente virtual ativo e as permissões do [banco de testes](../../database/README.md#preparar-o-banco-local)
configuradas, execute:

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
python -m ruff check .
```

Os testes cobrem autenticação e permissões, catálogo, disponibilidade e
agendamentos. Os cenários de concorrência usam conexões independentes no MySQL
para verificar o bloqueio em reservas simultâneas e em confirmação concorrente
com cancelamento. Execute esses cenários no MySQL para exercitar
`SELECT FOR UPDATE`.

Ao alterar o contrato da API, gere e valide a especificação versionada.

```sh
python manage.py spectacular --file ../../docs/openapi.yaml --validate --fail-on-warn
```

## Executar a API com Docker Compose

O Compose sobe a API na porta 8000. Prepare o banco MySQL externo antes de
subir o contêiner e configure um `MYSQL_HOST` acessível a partir dele.
No Docker Desktop, use `host.docker.internal` se o MySQL estiver no host.
Sirva o front-end em outro processo, conforme o guia da raiz.

```sh
docker compose up --build
```

O entrypoint aplica migrações e coleta arquivos estáticos. O Gunicorn atende
as requisições, e o WhiteNoise serve os arquivos do Admin e do Swagger.
Se a API falhar na inicialização, consulte `docker compose logs api` e confira
se o contêiner consegue alcançar o MySQL. O build ainda requer validação no
ambiente Docker da equipe.

Para publicar a API, use HTTPS, `DEBUG=False`, uma chave própria e listas
restritas de hosts e origens.

## Organização do código

| Pasta | Responsabilidade |
| --- | --- |
| [accounts](accounts/) | Cadastro, login, renovação de tokens, perfil e troca de senha. |
| [catalog](catalog/) | Dados da barbearia, profissionais e serviços. |
| [scheduling](scheduling/) | Blocos de disponibilidade, reservas, agendas e histórico. |
| [config](config/) | Configuração do Django, roteamento, prontidão e OpenAPI. |
