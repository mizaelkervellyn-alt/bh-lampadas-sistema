-- Extensão acadêmica v0.2: pedidos e contas a receber.
-- Aplicada em um banco local existente SEM eliminar as tabelas anteriores.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
    observacao TEXT NOT NULL DEFAULT '',
    total_centavos INTEGER NOT NULL CHECK (total_centavos > 0),
    pagamento TEXT NOT NULL CHECK (pagamento IN ('avista','prazo')),
    criado_por INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedido_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedido(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produto(id) ON DELETE RESTRICT,
    codigo_produto TEXT NOT NULL,
    descricao_produto TEXT NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade BETWEEN 1 AND 9999),
    valor_unitario_centavos INTEGER NOT NULL CHECK (valor_unitario_centavos > 0)
);
CREATE TABLE IF NOT EXISTS conta_receber (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE RESTRICT,
    pedido_id INTEGER UNIQUE REFERENCES pedido(id) ON DELETE RESTRICT,
    descricao TEXT NOT NULL,
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    vencimento TEXT NOT NULL,
    criado_por INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS recebimento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conta_id INTEGER NOT NULL REFERENCES conta_receber(id) ON DELETE RESTRICT,
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    registrado_por INTEGER REFERENCES usuario(id) ON DELETE SET NULL,
    recebido_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_pedido_cliente ON pedido(cliente_id);
CREATE INDEX IF NOT EXISTS ix_pedido_item_pedido ON pedido_item(pedido_id);
CREATE INDEX IF NOT EXISTS ix_conta_cliente_vencimento ON conta_receber(cliente_id,vencimento);
CREATE INDEX IF NOT EXISTS ix_recebimento_conta ON recebimento(conta_id);
