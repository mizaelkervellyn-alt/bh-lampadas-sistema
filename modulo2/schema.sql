-- BH Lampadas | Projeto Integrador TI I | MODELO PROPOSTO (nao sistema em producao)
-- SQLite 3.35+ | Banco academico; so inserir dados ficticios ate seguranca validada.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL, -- Nunca armazenar senha em texto simples.
    perfil TEXT NOT NULL CHECK (perfil IN ('administrador', 'operador', 'consulta')),
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_space TEXT UNIQUE,
    id_bling TEXT UNIQUE,
    tipo_pessoa TEXT NOT NULL CHECK (tipo_pessoa IN ('fisica', 'juridica', 'estrangeira')),
    nome TEXT NOT NULL,
    documento TEXT UNIQUE, -- Dado pessoal: requer politica de acesso e protecao.
    inscricao_estadual TEXT,
    email TEXT,
    telefone TEXT,
    cep TEXT,
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grupo_produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_space TEXT UNIQUE,
    nome TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_space TEXT UNIQUE,
    digito_space TEXT,
    id_bling TEXT UNIQUE,
    descricao TEXT NOT NULL,
    unidade TEXT NOT NULL DEFAULT 'UN',
    grupo_id INTEGER REFERENCES grupo_produto(id) ON DELETE SET NULL,
    quantidade_legacy INTEGER, -- NAO assumir que e saldo de estoque sem validar com a loja.
    preco_venda_centavos INTEGER CHECK (preco_venda_centavos IS NULL OR preco_venda_centavos >= 0),
    codigo_fornecedor_1 TEXT,
    codigo_fornecedor_2 TEXT,
    origem_space TEXT,
    codigo_tributario_space TEXT,
    aliquota_icms_space TEXT, -- Escala nao confirmada no registro 2,2 do layout.
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exportacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destino TEXT NOT NULL DEFAULT 'Bling',
    tipo TEXT NOT NULL CHECK (tipo IN ('clientes', 'produtos')),
    nome_arquivo TEXT NOT NULL,
    situacao TEXT NOT NULL DEFAULT 'gerado' CHECK (situacao IN ('gerado', 'validado', 'importado', 'falhou')),
    total_registros INTEGER NOT NULL DEFAULT 0 CHECK (total_registros >= 0),
    criado_por INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exportacao_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exportacao_id INTEGER NOT NULL REFERENCES exportacao(id) ON DELETE CASCADE,
    cliente_id INTEGER REFERENCES cliente(id) ON DELETE RESTRICT,
    produto_id INTEGER REFERENCES produto(id) ON DELETE RESTRICT,
    CHECK ((cliente_id IS NOT NULL AND produto_id IS NULL)
        OR (cliente_id IS NULL AND produto_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS ocorrencia_privacidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    descricao TEXT NOT NULL, -- Nao inserir CPF ou outros dados pessoais desnecessarios.
    providencia TEXT,
    situacao TEXT NOT NULL DEFAULT 'aberta' CHECK (situacao IN ('aberta', 'em_analise', 'concluida')),
    registrado_por INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    registrado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS log_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    tipo_acao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    registro_id INTEGER,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_cliente_nome ON cliente(nome);
CREATE INDEX IF NOT EXISTS ix_produto_descricao ON produto(descricao);
CREATE INDEX IF NOT EXISTS ix_produto_grupo ON produto(grupo_id);
CREATE INDEX IF NOT EXISTS ix_exportacao_itens ON exportacao_item(exportacao_id);
