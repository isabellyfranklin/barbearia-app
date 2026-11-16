-- ============================================================
-- Banco de Dados: Prumo
-- Sistema de Gestão e Agendamento para Barbearias
-- ============================================================
--
-- Este arquivo documenta a estrutura principal do banco de dados.
-- Não contém senhas, dados pessoais ou dados reais de usuários.
--
-- Banco utilizado: MySQL 8.4
-- Charset: utf8mb4
-- Collation: utf8mb4_unicode_ci
--
-- As migrations do Django permanecem como referência principal
-- para a criação e atualização do banco no backend.
-- ============================================================


-- ============================================================
-- TABELA: accounts_usuario
-- Usuários do sistema
-- ============================================================

CREATE TABLE accounts_usuario (
    id BIGINT NOT NULL AUTO_INCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME(6) NULL,
    is_superuser TINYINT(1) NOT NULL,
    username VARCHAR(150) NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff TINYINT(1) NOT NULL,
    is_active TINYINT(1) NOT NULL,
    date_joined DATETIME(6) NOT NULL,
    perfil VARCHAR(20) NOT NULL,
    telefone VARCHAR(20) NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uk_usuario_username (username),
    UNIQUE KEY uk_usuario_telefone (telefone)
);


-- ============================================================
-- TABELA: catalog_barbearia
-- Dados da barbearia
-- ============================================================

CREATE TABLE catalog_barbearia (
    id BIGINT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    descricao LONGTEXT NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(254) NOT NULL,
    atualizado_em DATETIME(6) NOT NULL,
    proprietario_id BIGINT NULL,

    PRIMARY KEY (id),

    CONSTRAINT fk_barbearia_proprietario
        FOREIGN KEY (proprietario_id)
        REFERENCES accounts_usuario (id)
);


-- ============================================================
-- TABELA: catalog_profissional
-- Profissionais que realizam os serviços
-- ============================================================

CREATE TABLE catalog_profissional (
    id BIGINT NOT NULL AUTO_INCREMENT,
    especialidades VARCHAR(255) NOT NULL,
    bio LONGTEXT NOT NULL,
    ativo TINYINT(1) NOT NULL,
    criado_em DATETIME(6) NOT NULL,
    usuario_id BIGINT NOT NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uk_profissional_usuario (usuario_id),

    CONSTRAINT fk_profissional_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES accounts_usuario (id)
);


-- ============================================================
-- TABELA: catalog_servico
-- Serviços oferecidos pela barbearia
-- ============================================================

CREATE TABLE catalog_servico (
    id BIGINT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(120) NOT NULL,
    descricao LONGTEXT NOT NULL,
    duracao_minutos INT UNSIGNED NOT NULL,
    preco DECIMAL(8,2) NOT NULL,
    ativo TINYINT(1) NOT NULL,
    criado_em DATETIME(6) NOT NULL,

    PRIMARY KEY (id)
);


-- ============================================================
-- TABELA: scheduling_disponibilidade
-- Horários de disponibilidade dos profissionais
-- ============================================================

CREATE TABLE scheduling_disponibilidade (
    id BIGINT NOT NULL AUTO_INCREMENT,
    dia_semana SMALLINT UNSIGNED NOT NULL,
    hora_inicio TIME(6) NOT NULL,
    hora_fim TIME(6) NOT NULL,
    ativo TINYINT(1) NOT NULL,
    criado_em DATETIME(6) NOT NULL,
    profissional_id BIGINT NOT NULL,

    PRIMARY KEY (id),

    CONSTRAINT fk_disponibilidade_profissional
        FOREIGN KEY (profissional_id)
        REFERENCES catalog_profissional (id)
);


-- ============================================================
-- TABELA: scheduling_agendamento
-- Agendamentos realizados pelos clientes
-- ============================================================

CREATE TABLE scheduling_agendamento (
    id BIGINT NOT NULL AUTO_INCREMENT,
    data_hora DATETIME(6) NOT NULL,
    duracao_minutos INT UNSIGNED NOT NULL,
    preco DECIMAL(8,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    observacoes LONGTEXT NOT NULL,
    criado_em DATETIME(6) NOT NULL,
    atualizado_em DATETIME(6) NOT NULL,
    cliente_id BIGINT NOT NULL,
    profissional_id BIGINT NOT NULL,
    servico_id BIGINT NOT NULL,

    PRIMARY KEY (id),

    CONSTRAINT fk_agendamento_cliente
        FOREIGN KEY (cliente_id)
        REFERENCES accounts_usuario (id),

    CONSTRAINT fk_agendamento_profissional
        FOREIGN KEY (profissional_id)
        REFERENCES catalog_profissional (id),

    CONSTRAINT fk_agendamento_servico
        FOREIGN KEY (servico_id)
        REFERENCES catalog_servico (id)
);


-- ============================================================
-- FIM DO SCHEMA PRINCIPAL DO PRUMO
-- ============================================================