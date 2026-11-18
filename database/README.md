# Banco de Dados — Prumo

## 1. Visão geral

O banco de dados do sistema **Prumo** foi desenvolvido para armazenar e organizar as informações necessárias ao gerenciamento de uma única barbearia e ao processo de agendamento de serviços.

O sistema utiliza o **MySQL 8.4** como Sistema Gerenciador de Banco de Dados (SGBD), integrado ao backend desenvolvido em **Django**.

O banco utilizado no ambiente de desenvolvimento é denominado `barbearia`.

## 2. Objetivo do banco de dados

O banco de dados tem como objetivo armazenar informações relacionadas a:

- usuários do sistema;
- dados da única barbearia;
- profissionais;
- serviços oferecidos;
- disponibilidade dos profissionais;
- agendamentos realizados pelos clientes.

A estrutura foi organizada de forma relacional, utilizando chaves primárias e chaves estrangeiras para manter a integridade dos dados.

## 3. Principais tabelas

### 3.1 `accounts_usuario`

Armazena os usuários do sistema e informações utilizadas para autenticação e controle de acesso.

Principais campos:

- `id`: identificador único do usuário;
- `username`: nome de usuário;
- `email`: endereço de e-mail;
- `perfil`: perfil de acesso do usuário;
- `telefone`: telefone do usuário;
- `is_active`: indica se o usuário está ativo;
- `is_staff`: indica se o usuário possui acesso administrativo;
- `is_superuser`: indica se o usuário possui privilégios de superusuário.

### 3.2 `catalog_barbearia`

Armazena as informações da única barbearia atendida pelo MVP. O modelo Django utiliza o registro de chave primária 1; essa regra é aplicada pela aplicação, não por uma restrição adicional neste SQL.

Principais campos:

- `id`: identificador único da barbearia;
- `nome`: nome da barbearia;
- `descricao`: descrição;
- `endereco`: endereço;
- `cidade`: cidade;
- `telefone`: telefone;
- `email`: endereço de e-mail;
- `atualizado_em`: data e hora da última atualização;
- `proprietario_id`: referência ao usuário proprietário.

### 3.3 `catalog_profissional`

Armazena os profissionais cadastrados no sistema.

Principais campos:

- `id`: identificador único do profissional;
- `especialidades`: especialidades do profissional;
- `bio`: informações sobre o profissional;
- `ativo`: indica se o profissional está ativo;
- `criado_em`: data e hora de criação;
- `usuario_id`: referência ao usuário associado ao profissional.

### 3.4 `catalog_servico`

Armazena os serviços disponibilizados pela barbearia.

Principais campos:

- `id`: identificador único do serviço;
- `nome`: nome do serviço;
- `descricao`: descrição;
- `duracao_minutos`: duração prevista do serviço;
- `preco`: valor do serviço;
- `ativo`: indica se o serviço está disponível;
- `criado_em`: data e hora de criação.

### 3.5 `scheduling_disponibilidade`

Armazena os horários de disponibilidade dos profissionais.

Principais campos:

- `id`: identificador único da disponibilidade;
- `dia_semana`: dia da semana;
- `hora_inicio`: horário inicial;
- `hora_fim`: horário final;
- `ativo`: indica se a disponibilidade está ativa;
- `criado_em`: data e hora de criação;
- `profissional_id`: referência ao profissional.

### 3.6 `scheduling_agendamento`

Armazena os agendamentos realizados no sistema.

Principais campos:

- `id`: identificador único do agendamento;
- `data_hora`: data e hora do agendamento;
- `duracao_minutos`: duração do serviço;
- `preco`: valor do agendamento;
- `status`: situação atual do agendamento;
- `observacoes`: observações relacionadas ao agendamento;
- `criado_em`: data e hora de criação;
- `atualizado_em`: data e hora da última atualização;
- `cliente_id`: referência ao cliente;
- `profissional_id`: referência ao profissional;
- `servico_id`: referência ao serviço.

## 4. Relacionamentos principais

Os principais relacionamentos entre as tabelas do sistema são:

- `catalog_barbearia.proprietario_id` → `accounts_usuario.id`
- `catalog_profissional.usuario_id` → `accounts_usuario.id`
- `scheduling_disponibilidade.profissional_id` → `catalog_profissional.id`
- `scheduling_agendamento.cliente_id` → `accounts_usuario.id`
- `scheduling_agendamento.profissional_id` → `catalog_profissional.id`
- `scheduling_agendamento.servico_id` → `catalog_servico.id`

Esses relacionamentos permitem associar usuários, profissionais, serviços, horários disponíveis e agendamentos.

## 5. Integridade dos dados

A estrutura utiliza:

- chaves primárias para identificação dos registros;
- chaves estrangeiras para relacionamentos entre tabelas;
- campos únicos para evitar duplicidade em determinados dados;
- tipos de dados adequados às informações armazenadas;
- regras de integridade referencial definidas pelo banco de dados.

As chaves estrangeiras deste recorte SQL utilizam o comportamento restritivo padrão do MySQL (`NO ACTION`/`RESTRICT`). No Django, `on_delete` também define comportamento na camada ORM: por exemplo, `SET_NULL` para o proprietário, `CASCADE` para o usuário do profissional e `PROTECT` para os vínculos do agendamento. Essas opções do ORM não devem ser interpretadas como cláusulas `ON DELETE` idênticas no SQL.

## 6. Integração com o Django

A estrutura do banco é gerenciada pelo Django por meio das **migrations** existentes nas aplicações do backend.

As principais migrations relacionadas ao domínio do sistema estão localizadas em:

```text
backend/BarbeariaAPP-codigo/accounts/migrations/
backend/BarbeariaAPP-codigo/catalog/migrations/
backend/BarbeariaAPP-codigo/scheduling/migrations/
```

As migrations permitem criar e atualizar a estrutura do banco de dados de forma controlada durante o desenvolvimento.

## 7. Segurança

Informações sensíveis, como senhas, tokens e credenciais de acesso ao banco de dados, não devem ser armazenadas neste documento nem versionadas no GitHub.

As configurações de ambiente são mantidas em arquivo `.env`, que está configurado no `.gitignore` do projeto.

## 8. Ambiente de desenvolvimento

**SGBD:** MySQL 8.4  
**Banco de dados:** `barbearia`  
**Backend:** Django  
**Charset:** UTF-8 (`utf8mb4`)  
**Collation:** `utf8mb4_unicode_ci`

### Preparar o banco local

Com o MySQL em execução, conecte-se com uma conta autorizada a criar bancos e
usuários. Para uma instalação nova com o Django executado no mesmo computador,
use o exemplo abaixo. Substitua `senha-local-aleatoria` por uma senha própria.

```sql
CREATE DATABASE barbearia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'barbearia'@'localhost' IDENTIFIED BY 'senha-local-aleatoria';
GRANT ALL PRIVILEGES ON barbearia.* TO 'barbearia'@'localhost';
```

Preencha `MYSQL_DATABASE=barbearia`, `MYSQL_USER=barbearia` e
`MYSQL_PASSWORD` no `.env` do back-end. Para o Django em Docker, ajuste o host
da conexão e conceda acesso à conta MySQL a partir da origem efetiva da conexão.

A suíte do Django usa por padrão o nome `test_barbearia` quando
`MYSQL_DATABASE=barbearia`. Para executar os testes com a mesma conta local,
conceda acesso também a esse banco. O Django cria e remove o banco durante a
execução da suíte.

```sql
GRANT ALL PRIVILEGES ON `test\_barbearia`.* TO 'barbearia'@'localhost';
```

## 9. Criar ou atualizar o esquema

Na raiz do repositório, com o ambiente virtual ativo e o `.env` configurado,
execute:

```bash
cd backend/BarbeariaAPP-codigo
python manage.py migrate
python manage.py showmigrations
```

As migrações criam as tabelas de domínio e as tabelas internas de autenticação,
grupos, permissões, sessões, administração, JWT e histórico de migrações.
`showmigrations` lista as migrações aplicadas.

## 10. Escopo do schema documental

O [schema.sql](schema.sql) serve como referência para as seis tabelas de domínio
descritas neste documento. Para instalação e atualização, aplique as migrações
diretamente sobre o banco da aplicação. Para recuperação de dados, use o backup
do banco correspondente. O recorte SQL contém apenas definições de tabelas.

## 11. Índices e restrições das migrations

O recorte inclui as restrições explícitas de `scheduling/migrations/0001_initial.py`:

- `disp_hora_fim_maior`: término da disponibilidade posterior ao início.
- `disp_unica`: sem blocos exatamente duplicados para o mesmo profissional e dia.
- `agend_duracao_positiva`: duração do agendamento maior que zero.
- `agend_preco_nao_negativo`: preço do agendamento maior ou igual a zero.

O SQL também inclui as verificações de não negatividade geradas pelo Django para os campos inteiros positivos de duração e dia da semana.

Índices compostos e de consulta:

- `disp_prof_dia_idx`: profissional e dia da semana.
- `agend_prof_data_idx`: profissional e data/hora.
- `agend_cliente_data_idx`: cliente e data/hora.
- `agend_status_idx`: status.

A unicidade de um bloco não impede sobreposição entre blocos diferentes.
Conflitos de reservas, transições de status, cancelamento antes do atendimento e
permissões por perfil são validados no backend. A prevenção de reservas simultâneas
usa transação e bloqueio do profissional; não há uma restrição SQL de exclusão de intervalos.

Um agendamento referencia exatamente um serviço. Pagamento on-line e atendimento
a múltiplas barbearias permanecem fora do MVP.

## 12. Atualização deste documento

Quando os models ou as migrations mudarem, revisar este recorte e compará-lo com
um banco temporário criado por `migrate`. Nomes de índices e chaves estrangeiras
gerados automaticamente pelo Django podem diferir dos nomes documentais, sem
alterar as colunas ou os relacionamentos representados.

O ambiente-alvo documentado pelo grupo é MySQL 8.4. A validação local anterior do
backend utilizou MySQL 8.0.46; isso não equivale a executar a mesma suíte no 8.4.


Validação deste recorte: as seis tabelas foram comparadas no MySQL 8.0.46 com um banco temporário criado pelas migrations, conferindo colunas, tipos, nulabilidade, valores padrão, chaves estrangeiras, unicidade, índices nomeados e restrições CHECK. A comparação passou.
