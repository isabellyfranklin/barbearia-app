# Prumo — agendamento de uma barbearia

Projeto Integrador IV — Senac EAD, 2026.

O back-end oficial é **Django REST Framework + MySQL**, em
[backend/BarbeariaAPP-codigo](backend/BarbeariaAPP-codigo/README.md).
O MVP atende uma única barbearia, com perfis cliente, barbeiro e administrador.
O front-end em HTML/CSS/JavaScript permanece um protótipo independente.
Esta etapa prepara o servidor; não conecta nem modifica a interface.

## Executar

Requer Python 3.12 e MySQL com banco/usuário criados.
MySQL 8.4 é o alvo do grupo; a validação local utiliza MySQL 8.0.46.

~~~powershell
cd backend/BarbeariaAPP-codigo
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Configure o .env antes de continuar.
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
~~~

- API: http://localhost:8000/api/v1/
- Swagger: http://localhost:8000/api/v1/docs
- OpenAPI: http://localhost:8000/api/v1/schema
- Prontidão: http://localhost:8000/api/v1/health
- Django Admin: http://localhost:8000/admin/

## MVP

Um serviço por reserva; situação inicial pendente; confirmação pelo administrador
ou barbeiro responsável; cliente cancela somente antes do início; preço e duração
preservados no histórico; bloqueio transacional no MySQL para impedir sobreposições.
Serviços e profissionais são desativados, preservando o histórico.

Pagamentos, múltiplas barbearias e relatórios financeiros estão fora desta entrega.
O FastAPI foi retirado; seu código permanece recuperável no histórico do Git.
Não execute Uvicorn nem crie tabelas manualmente pelo SQL documental.

## Documentação

- [Contrato REST e exemplos](docs/API.md)
- [Migração e rastreabilidade](docs/MIGRACAO_BACKEND.md)
- [OpenAPI gerado](docs/openapi.yaml)
- [Banco de dados](database/README.md)
- [Modelo da segunda entrega](https://docs.google.com/document/d/1LFH7a7eXbECiNHs7S6ayrPSsuixISlHhTu54f3ZxAEw/edit)

Esta consolidação ocorre em feature/backend; publicação e merge são etapas separadas.
Não versione .env, credenciais ou dumps com dados pessoais.
