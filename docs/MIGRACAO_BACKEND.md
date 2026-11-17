# Consolidação do back-end — segunda entrega

Fonte funcional: Modelo_Segunda_Entrega_PI_Barbearia, consultado em 17/11/2026.
[Documento](https://docs.google.com/document/d/1LFH7a7eXbECiNHs7S6ayrPSsuixISlHhTu54f3ZxAEw/edit).
O usuário confirmou seguir seu MVP. Informações de status dos PRs/testes no documento
podem estar desatualizadas; a referência usada aqui é o escopo funcional.

## Decisão

Servidor único: Django REST Framework + ORM Django + MySQL.
FastAPI já era REST; a mudança consolida framework, persistência, regras e contratos.
O diretório Projeto Barbearia Backend foi retirado; o código é recuperável no Git.
CODIGO_COMPLETO.md era uma cópia agregada e desatualizada; os módulos Python e o
OpenAPI são as fontes de verdade.

## Regras preservadas/alinhadas

| Regra | Implementação |
|---|---|
| Autenticação, hash e escopo por perfil | accounts; SimpleJWT/hash Django |
| Catálogo e desativação preservando histórico | catalog |
| Expediente semanal e duração | scheduling.services |
| Futuro e ausência de sobreposição | transação e lock do profissional no MySQL |
| Persistência UTC e interpretação local | USE_TZ; America/Sao_Paulo |
| Estados finais não reabrem | transições sob lock do agendamento |
| Um serviço por reserva | FK servico; preço e duração copiados |
| Cancelamento | cliente somente antes do início (RF11) |
| Confirmação | administrador/barbeiro responsável, sem pagamento |
| Histórico por perfil | filtros e escopo no servidor |
| Dados da barbearia | registro único |

O lock em memória do FastAPI foi substituído pelo lock no banco, válido entre
conexões/workers. Os testes MySQL continuam na suíte.

## Extras fora do MVP

Não portados: múltiplas barbearias/onboarding de proprietário; pagamentos/estornos
e confirmação por pagamento; relatórios financeiros; vínculo profissional–serviço;
bloqueios pontuais time-off; NO_SHOW; reserva administrativa em nome do cliente;
gestão do expediente pelo próprio barbeiro; antecedência mínima configurável.
O documento restringe gestão do expediente ao administrador e reservas ao cliente.
Essas diferenças são decisões de escopo, não funcionalidades concluídas.

## Rastreabilidade

| Requisito | Contrato/módulo | Evidência automatizada |
|---|---|---|
| RF01 | auth/register | cadastro sem escalada |
| RF02 | auth/*, me, me/password | JWT, logout e troca de senha |
| RF03 | barbershop, admin/barbershop | singleton e edição |
| RF04 | professionals | catálogo ativo/privacidade |
| RF05 | services, admin/services | catálogo/desativação/permissões |
| RF06 | admin/professionals | criação/desativação/reativação |
| RF07 | admin/availability | blocos e expediente |
| RF08 | professionals/{id}/availability | slots/duração diária e por período |
| RF09 | appointments POST | pendência e snapshots |
| RF10 | scheduling.services | conflitos e concorrência MySQL |
| RF11 | appointments/{id}/cancel | antes/no instante/depois do início |
| RF12 | me/agenda e me/agenda/week | agenda por perfil |
| RF13 | me/agenda/{id}/status | confirmação autorizada/transições |
| RF14 | me/history | cliente e filtros |
| RF15 | me/history/professional | isolamento profissional |
| RF16 | admin/appointments | filtros administrativos |
| RF17 | admin/history | histórico administrativo |
| RNF02 | permissions/JWT/settings | acesso, senha e logout |
| RNF03 | transações/MySQL | três cenários concorrentes |

Testes em accounts/tests, catalog/tests e scheduling/tests.
RNF01 e RNF04 dependem da interface e ficam para etapa futura.
Nenhum arquivo de frontend/ é alterado.

## Compatibilidade e dados

Contrato oficial /api/v1, com os campos em português já usados pelo Django.
Aliases preliminares /api continuam temporariamente, fora do OpenAPI;
não são aliases de FastAPI.
Tokens JWT/bancos SQLAlchemy antigos não são compatíveis com SimpleJWT/ORM Django.
Não há importação automática de dados: se houver dados reais no legado,
planeje e teste uma migração separada antes de mudar o servidor.

As migrations existentes não foram reescritas. Não use --fake nem schema.sql para
substituí-las. Nenhum deploy, push ou edição do Google Docs faz parte deste commit local.
