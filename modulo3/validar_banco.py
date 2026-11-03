"""Validação acadêmica isolada do esquema SQLite (somente dados fictícios).
Execute com Python 3.8+ na pasta modulo3: python validar_banco.py
Não conecta ao banco de dados da empresa e não altera arquivos reais.
"""
import sqlite3
import tempfile
from pathlib import Path

SCHEMA = Path(__file__).resolve().parent.parent / 'modulo2' / 'schema.sql'


def verificar():
    if not SCHEMA.exists():
        raise FileNotFoundError('Coloque a pasta modulo3 ao lado de modulo2 no mesmo repositório. Faltando: ' + str(SCHEMA))
    with tempfile.TemporaryDirectory(prefix='bh_lampadas_mod3_') as pasta:
        db = Path(pasta) / 'teste.sqlite3'
        conexao = sqlite3.connect(str(db))
        conexao.execute('PRAGMA foreign_keys = ON;')
        conexao.executescript(SCHEMA.read_text(encoding='utf-8'))
        def ok(numero, mensagem):
            print('[OK {}] {}'.format(numero, mensagem))
        tabelas = {r[0] for r in conexao.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        esperadas = {'usuario','cliente','grupo_produto','produto','exportacao','exportacao_item','ocorrencia_privacidade','log_auditoria'}
        assert tabelas == esperadas, (tabelas, esperadas)
        ok(1, 'Oito tabelas criadas pelo schema.sql publicado')
        assert conexao.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert sum(len(list(conexao.execute('PRAGMA foreign_key_list({})'.format(t)))) for t in tabelas) == 7
        ok(2, 'Sete chaves estrangeiras e integridade referencial habilitada')
        conexao.execute("INSERT INTO grupo_produto (nome) VALUES ('Iluminação fictícia')")
        grupo_id = conexao.execute('SELECT id FROM grupo_produto').fetchone()[0]
        conexao.execute('INSERT INTO produto (codigo_space, descricao, grupo_id, preco_venda_centavos) VALUES (?, ?, ?, ?)', ('M3-DEMO-001', 'Lâmpada de demonstração', grupo_id, 2590))
        conexao.execute("INSERT INTO cliente (nome, tipo_pessoa, cidade, uf) VALUES ('Cliente fictício', 'fisica', 'Belo Horizonte', 'MG')")
        res = conexao.execute('SELECT p.descricao, g.nome FROM produto p JOIN grupo_produto g ON g.id=p.grupo_id WHERE p.codigo_space=?', ('M3-DEMO-001',)).fetchone()
        assert res == ('Lâmpada de demonstração', 'Iluminação fictícia')
        ok(3, 'INSERT + SELECT JOIN para produtos e grupos')
        conexao.execute('UPDATE produto SET preco_venda_centavos=? WHERE codigo_space=?', (2790,'M3-DEMO-001'))
        assert conexao.execute('SELECT preco_venda_centavos FROM produto WHERE codigo_space=?', ('M3-DEMO-001',)).fetchone()[0] == 2790
        ok(4, 'UPDATE recuperado em consulta SQL')
        def rejeita(sql, params):
            try:
                conexao.execute(sql,params)
            except sqlite3.IntegrityError:
                return True
            return False
        assert rejeita('INSERT INTO produto (codigo_space, descricao) VALUES (?, ?)', ('M3-DEMO-001','Duplicado'))
        ok(5, 'UNIQUE impede código de produto duplicado')
        assert rejeita('INSERT INTO produto (codigo_space, descricao, preco_venda_centavos) VALUES (?,?,?)', ('M3-NEG','Produto incorreto',-1))
        ok(6, 'CHECK impede preço negativo')
        assert rejeita('INSERT INTO produto (codigo_space, descricao, grupo_id) VALUES (?,?,?)', ('M3-FK','Grupo inexistente',999999))
        ok(7, 'FOREIGN KEY impede referência inexistente')
        conexao.execute('DELETE FROM produto WHERE codigo_space=?', ('M3-DEMO-001',))
        assert conexao.execute('SELECT COUNT(*) FROM produto WHERE codigo_space=?',('M3-DEMO-001',)).fetchone()[0] == 0
        ok(8, 'DELETE executado e exclusão confirmada')
        conexao.close()
    print('RESULTADO: 8 verificações concluídas; banco temporário descartado.')


if __name__ == '__main__':
    verificar()
