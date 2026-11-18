# Contrato REST v1 — Prumo

Base: /api/v1. JSON. Rotas sem barra final. [OpenAPI gerado](openapi.yaml).
Swagger: /api/v1/docs. O front-end usa estes contratos para autenticação,
catálogo, agendamentos, agenda do barbeiro e painel administrativo.

## Convenções

IDs inteiros positivos. Preços são strings decimais, como "50.00".
Filtros de data usam YYYY-MM-DD. Datetimes usam ISO 8601; envie offset explícito,
por exemplo 2026-12-01T10:00:00-03:00. Persistência UTC e saída America/Sao_Paulo;
entradas sem offset seguem o fuso do Django.

from/to são inclusivos. A consulta de disponibilidade limita a diferença entre
datas a 60 dias. Não existe janela máxima de reserva de 30 dias.
Listagens retornam arrays, sem paginação nesta versão.
A agenda semanal retorna from, to e appointments.

Autenticação: Authorization: Bearer <access>.
Respostas: 200 consulta/atualização, 201 criação, 204 sem corpo, 400 validação,
401 autenticação, 403 permissão, 404 inexistente/fora do escopo, 405 método inválido.
Erros seguem o DRF: {"campo":["mensagem"]} ou {"detail":"mensagem"};
erros JWT também podem incluir code. Não trate 400 como reserva confirmada.

DELETE em serviços/profissionais desativa; em disponibilidade remove o bloco semanal.
Agendamentos não são excluídos. CORS é configurável por ambiente.
A API usa JWT, sem cookies de sessão ou CSRF token para requisições REST.

## Autenticação

| Método | Caminho relativo | Acesso / entrada |
|---|---|---|
| POST | /auth/register | Público; username, telefone, password, password_confirm; nome/e-mail opcionais |
| POST | /auth/login | Público; username, password |
| POST | /auth/refresh | Público; refresh |
| POST | /auth/logout | Autenticado; refresh do mesmo usuário |
| GET/PATCH | /me | Próprio perfil; username/perfil somente leitura |
| POST | /me/password | current_password, new_password, new_password_confirm |

Cadastro/login retornam user, access, refresh. Cadastro sempre cria cliente.
Refresh tem rotação: guarde o novo refresh e descarte o antigo.
Logout invalida o refresh informado; access já emitido pode continuar válido até
expirar (30 minutos). Troca de senha revoga access anteriores e todos os refresh
conhecidos do usuário; faça login novamente. Refresh expira em um dia.
Senhas são validadas pelo Django e armazenadas com hash. Contas inativas não autenticam.

O front-end compartilha uma renovação entre as requisições simultâneas da
mesma página. Ao selecionar **Sair**, tenta revogar o refresh atual na API
antes de limpar a sessão local. Se o access expirou, a interface renova os
tokens e tenta revogar o novo refresh.

## Catálogo e administração

| Método | Caminho relativo | Acesso |
|---|---|---|
| GET | /barbershop | Público; registro único |
| PATCH | /admin/barbershop | Administrador |
| GET | /professionals | Público; profissionais e contas ativos |
| GET | /professionals/{id} | Público; sem dados de login/contato da conta |
| GET | /services | Público; ativos |
| GET | /services/{id} | Público |
| GET/POST | /admin/professionals | Administrador |
| GET/PUT/PATCH/DELETE | /admin/professionals/{id} | Administrador |
| GET/POST | /admin/services | Administrador |
| GET/PUT/PATCH/DELETE | /admin/services/{id} | Administrador |
| GET/POST | /admin/availability | Administrador; filtro professional |
| GET/PUT/PATCH/DELETE | /admin/availability/{id} | Administrador |

Profissional: username, password, telefone; email, first_name, last_name,
especialidades, bio e ativo opcionais. Reativar o profissional reativa a conta.
Serviço: nome, descricao, duracao_minutos (mínimo 5), preco (não negativo), ativo.
Disponibilidade: profissional, dia_semana (0=segunda a 6=domingo), hora_inicio,
hora_fim, ativo. Término posterior ao início. Intervalos são blocos separados.

## Reservas e agendas

| Método | Caminho relativo | Acesso / filtros |
|---|---|---|
| GET | /professionals/{id}/availability | Público; service e date OU service, from, to |
| POST | /appointments | Cliente; profissional, servico, data_hora, observacoes opcional |
| GET | /appointments | Cliente; próprias reservas; status, from, to |
| GET | /appointments/{id} | Cliente dono, barbeiro responsável ou administrador |
| PATCH | /appointments/{id}/cancel | Cliente dono antes do início ou administrador; sem corpo |
| GET | /me/agenda | Barbeiro (própria)/administrador (geral); date, padrão hoje |
| GET | /me/agenda/week | Mesmos perfis; date; semana de segunda a domingo |
| PATCH | /me/agenda/{id}/status | Barbeiro responsável/administrador; {"status":"..."} |
| GET | /me/history | Cliente; status, from, to |
| GET | /me/history/professional | Barbeiro; status, from, to |
| GET | /admin/appointments | Administrador; professional, date, status, from, to |
| GET | /admin/history | Administrador; status, from, to |

service é obrigatório na v1, inclusive por período. A consulta diária retorna
date, duration_minutes e slots; por período retorna from, to, duration_minutes e
days (cada dia com date e slots). Uma reserva referencia exatamente um serviço.
Profissionais ativos atendem os serviços ativos do catálogo; não há vínculo
individual profissional–serviço no MVP.

Transições: pendente → confirmado/cancelado; confirmado → concluido/cancelado.
Estados concluido e cancelado são finais. Repetir o status atual é idempotente;
cancelamento pelo cliente continua sujeito ao limite de horário.
O cliente não confirma nem conclui. Não existe pagamento.

A lista de slots é uma fotografia: o POST revalida expediente, futuro e conflitos
sob transação. Preço e duração são copiados para preservar o histórico.

## Exemplo

1. POST /api/v1/auth/login com {"username":"cliente","password":"..."}.
2. Consulte /api/v1/services e /api/v1/professionals.
3. Consulte /api/v1/professionals/1/availability?service=1&date=2026-12-01.
4. Use um slot retornado no POST /api/v1/appointments, com JWT:

~~~json
{"profissional":1,"servico":1,"data_hora":"2026-12-01T10:00:00-03:00","observacoes":"Primeira visita"}
~~~

IDs/datas são ilustrativos: consulte os valores reais. O barbeiro ou administrador
confirma pela operação /me/agenda/{id}/status.

## Operação

GET /health retorna 200 {"status":"ok","database":"ok"} ou
503 {"status":"unavailable","database":"unavailable"}, sem detalhes da conexão.
Schema e Swagger são públicos. Use HTTPS e configurações de produção antes de publicar.
