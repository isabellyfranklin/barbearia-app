# Validação do backend MVP

Validação local em 17/11/2026, Python 3.12.14, Django 5.2.19 e MySQL 8.0.46 (InnoDB), em banco temporário isolado.

- Suíte completa: 69 testes aprovados em 85,41 segundos, incluindo concorrência, permissões, JWT, disponibilidade, reservas e histórico.
- Django check: sem problemas.
- makemigrations --check --dry-run: nenhuma alteração de modelos pendente.
- OpenAPI: gerado e validado com spectacular --validate --fail-on-warn, sem avisos.
- Ruff: todos os checks aprovados.
- collectstatic: concluído. Os avisos de diretório staticfiles ausente durante a suíte ocorreram antes desta coleta.
- Migrações aplicadas ao banco temporário.
- Servidor HTTP local: health, services, schema, docs e bundle JavaScript do Swagger responderam HTTP 200.
- git diff --check: aprovado; nenhum arquivo do frontend alterado.

O Docker não foi executado neste ambiente. A validação do banco utilizou MySQL 8.0.46, não a imagem MySQL 8.4 do Compose.

O teste HTTP verificou a aplicação Django local; publicação, infraestrutura de produção e integração com frontend permanecem fora desta entrega.
