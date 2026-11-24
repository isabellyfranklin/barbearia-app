# Prumo — agendamento para barbearia

Projeto Integrador IV do Senac EAD, 2026. O Prumo reúne as reservas de uma
barbearia em uma interface web integrada a uma API Django REST e a um banco MySQL.

| Perfil | O que pode fazer |
| --- | --- |
| Cliente | Criar uma conta, consultar serviços e horários livres e reservar um atendimento. |
| Barbeiro | Consultar a agenda do dia ou da semana e atualizar o status dos seus atendimentos. |
| Administrador | Acompanhar agendamentos e faturamento, atualizar os dados da barbearia e gerenciar serviços, profissionais e horários de trabalho. |

As reservas começam como pendentes. A API impede sobreposições para o mesmo
profissional e preserva o preço e a duração contratados. O faturamento do painel
considera os atendimentos concluídos. O MVP atende uma barbearia.

## Demonstração do Projeto Integrador IV

O vídeo da segunda entrega (2 min 18 s) mostra o fluxo de reserva do cliente,
a agenda do barbeiro e a consulta no painel administrativo.

- [Assistir à demonstração no YouTube](https://youtu.be/BhizxM86HcI)
- [Consultar o relatório revisado da segunda entrega (PDF)](https://drive.google.com/file/d/15WlE3Lg6GRsZNU949bXXKXKWg6LY65oQ/view)

## Como as partes se conectam

O navegador carrega as páginas estáticas e envia requisições JSON para a API
em `/api/v1`. O Django autentica os usuários com JWT, aplica as permissões de
cada perfil e consulta o MySQL. O front-end pode ser servido diretamente por um
servidor HTTP, sem etapa de compilação.

## Executar localmente

Você precisa de Python 3.12, MySQL com InnoDB e de um banco vazio com um usuário
que possa executar as migrações. O projeto tem MySQL 8.4 como alvo.

### 1. Preparar o banco MySQL

Com o MySQL em execução, crie o banco e configure um usuário para a aplicação.
O [guia do banco](database/README.md#preparar-o-banco-local) contém os comandos
SQL para uma instalação local. Use os mesmos dados de conexão no `.env` do
back-end.

### 2. Preparar o back-end

Na raiz do repositório, crie o ambiente virtual e copie a configuração de exemplo.

**Linux e macOS**

```bash
cd backend/BarbeariaAPP-codigo
python3.12 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

**Windows com PowerShell**

```powershell
cd backend/BarbeariaAPP-codigo
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

No `.env`, configure `SECRET_KEY` e as variáveis `MYSQL_*` para o seu banco.
O [guia do back-end](backend/BarbeariaAPP-codigo/README.md#variáveis-de-ambiente) descreve
cada variável. Na pasta do back-end, instale as dependências, aplique as
migrações e inicie a API.

```sh
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo  # Opcional, para dados de demonstração
python manage.py runserver
```

O comando `seed_demo` é opcional e se destina a um banco de desenvolvimento. Ele
cria usuários de demonstração, serviços e horários. Em um banco novo, use as
seguintes contas na tela de login.

| Perfil | Usuário | Senha de demonstração |
| --- | --- | --- |
| Cliente | `cliente` | `cliente123` |
| Barbeiro | `joao` ou `carlos` | `barbeiro123` |
| Administrador | `admin` | `admin123` |

### 3. Servir o front-end

Em outro terminal, a partir da raiz do repositório, execute:

```sh
python3 -m http.server 3000 --bind 127.0.0.1
```

No Windows, use `python` no lugar de `python3`. Abra [a aplicação](http://localhost:3000)
e use uma das contas de demonstração ou cadastre um cliente.

| Endereço local | Uso |
| --- | --- |
| [Swagger](http://localhost:8000/api/v1/docs) | Explorar e testar os endpoints |
| [OpenAPI](http://localhost:8000/api/v1/schema) | Consultar o contrato da API |
| [Prontidão](http://localhost:8000/api/v1/health) | Verificar a conexão da API ao banco |
| [Django Admin](http://localhost:8000/admin/) | Acessar o administrativo do Django |

## Experimentar o fluxo de agendamento

1. Entre como `cliente` e escolha um serviço, um profissional e um horário futuro.
   Os horários de demonstração vão de segunda a sábado.
2. Saia e entre como o barbeiro que você escolheu. Abra a agenda na data da
   reserva e clique em **Confirmar** no atendimento pendente.
3. Com a mesma conta, clique em **Finalizar** no atendimento confirmado.
4. Entre como `admin` no front-end e consulte o agendamento e o faturamento no
   período que contém a data da reserva.

## Configurar a URL da API

Quando a página é aberta em `localhost`, `127.0.0.1` ou `[::1]`, o front-end usa `http://localhost:8000/api/v1`. Em outros
hosts, o padrão é `/api/v1` na mesma origem do front-end. Para servir a API em outra
origem, preencha o atributo `content` da meta tag `api-url` em
`index.html` (na raiz) e nos HTMLs em `frontend/pages/` com a URL base da API,
incluindo `/api/v1`. Adicione a origem do front-end a `CORS_ALLOWED_ORIGINS` no
`.env` do Django. Mantenha o `.env` e as credenciais reais fora do Git.

## Testar

Na pasta do back-end, com o ambiente virtual ativo, execute:

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
```

A suíte precisa de um usuário MySQL com permissão para criar e remover o banco
de testes. Ela verifica autenticação, catálogo, disponibilidade e concorrência
entre reservas.

Na revalidação de 23/11/2026, a suíte passou com **70 de 70 testes** no MySQL
8.4.13. A matriz de aceitação registrou **24 de 26 casos aprovados (92,31%)**.
A auditoria completa de acessibilidade (TC-24) segue em verificação, e o teste
com Docker (TC-26) está bloqueado no ambiente de revalidação.
Consulte o [índice de evidências](docs/evidencias/LEIA_ME.html) e o
[registro da execução local](docs/evidencias/09_Consolidacao/Prumo_Revalidacao_Local_2026-11-23.txt).

## Problemas comuns na instalação

| Sintoma | O que conferir |
| --- | --- |
| Erro de conexão ao rodar `migrate` | Confira se o MySQL está em execução e se o host e a porta do `.env` correspondem ao servidor. |
| `Access denied` do MySQL | Confira usuário, senha e permissões do banco. |
| Erro de CORS no navegador | Abra o front-end em `http://localhost:3000` ou inclua a origem exata usada no navegador em `CORS_ALLOWED_ORIGINS`. `localhost` e `127.0.0.1` são origens diferentes. |
| Sem horários para reservar | Confira se o serviço e o profissional estão ativos e se há um bloco que comporte o serviço na data escolhida. |

## Estrutura e documentação

- [Front-end](frontend/) em HTML, CSS e JavaScript, com o acesso à API em `js/api.js`.
- [Back-end](backend/BarbeariaAPP-codigo/README.md) em Django REST Framework, dividido em contas, catálogo e agendamento.
- [Banco de dados](database/README.md) com o esquema de referência. As migrações do Django aplicam o esquema usado pela aplicação.
- [Contrato REST](docs/API.md) e [especificação OpenAPI](docs/openapi.yaml).
- [Diagrama da arquitetura](docs/arquitetura_barbearia.png).
