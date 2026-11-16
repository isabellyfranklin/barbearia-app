# Banco de Dados — Prumo

## 1. Visão geral

O banco de dados do sistema **Prumo** foi desenvolvido para armazenar e organizar as informações necessárias ao gerenciamento de barbearias e ao processo de agendamento de serviços.

O sistema utiliza o **MySQL 8.4** como Sistema Gerenciador de Banco de Dados (SGBD), integrado ao backend desenvolvido em **Django**.

O banco utilizado no ambiente de desenvolvimento é denominado `barbearia`.

## 2. Objetivo do banco de dados

O banco de dados tem como objetivo armazenar informações relacionadas a:

- usuários do sistema;
- barbearias;
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

Armazena as informações das barbearias cadastradas no sistema.

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

As relações existentes no banco utilizam as regras `NO ACTION` para exclusão e atualização de registros relacionados.

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

## 9. Observação

As migrations do Django são a referência utilizada pelo backend para criação e atualização da estrutura do banco de dados. A pasta `database` contém a documentação e os artefatos relacionados ao banco de dados do projeto.