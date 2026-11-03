-- Checkout 3: exemplos SQL relacionados ao banco da BH Lâmpadas.
-- Executar SOMENTE em uma cópia de teste, com dados fictícios.
-- Banco acadêmico: esquema em ../modulo2/schema.sql
PRAGMA foreign_keys = ON;

-- Consulta de produtos e respectivos grupos (JOIN):
SELECT p.codigo_space, p.descricao, g.nome AS grupo,
       p.preco_venda_centavos
FROM produto AS p
LEFT JOIN grupo_produto AS g ON g.id = p.grupo_id
WHERE p.ativo = 1
ORDER BY p.descricao;

-- Clientes ativos organizados por nome:
SELECT id, nome, cidade, uf
FROM cliente
WHERE ativo = 1
ORDER BY nome;

-- Produtos sem preço definido ou com preço zerado:
SELECT codigo_space, descricao, preco_venda_centavos
FROM produto
WHERE ativo = 1 AND (preco_venda_centavos IS NULL OR preco_venda_centavos = 0);

-- Histórico de alterações cadastrais (se houver registros):
SELECT l.criado_em, l.tipo_acao, l.entidade, l.registro_id,
       u.nome AS usuario
FROM log_auditoria AS l
LEFT JOIN usuario AS u ON u.id = l.usuario_id
ORDER BY l.criado_em DESC;

-- Exemplo protegido contra modificação definitiva: em banco TESTE, os dados
-- fictícios são incluídos, alterados e removidos; ROLLBACK desfaz as mudanças.
BEGIN TRANSACTION;
INSERT INTO grupo_produto(nome) VALUES ('Grupo fictício - Módulo 3');
INSERT INTO produto(codigo_space, descricao, unidade, preco_venda_centavos)
VALUES ('M3-SQL-DEMO', 'Produto de demonstração', 'UN', 1590);
UPDATE produto SET preco_venda_centavos = 1690
WHERE codigo_space = 'M3-SQL-DEMO';
DELETE FROM produto WHERE codigo_space = 'M3-SQL-DEMO';
ROLLBACK;
