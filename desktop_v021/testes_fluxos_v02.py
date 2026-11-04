# -*- coding: utf-8 -*-
"""Testes integrados v0.2. Apenas banco SQLite temporario, sem usar cadastros reais.
Rodar dentro da pasta do projeto: python -m pytest -q testes_fluxos_v02.py
"""
import os
import re
import sys
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'modulo2'))
# Import inicializado com dados isolados, nao o do usuario no Windows.
_import_dir = tempfile.TemporaryDirectory(prefix='bh_v02_import_')
os.environ['BH_DATA_DIR'] = _import_dir.name
os.environ['BH_RESOURCES_DIR'] = str(ROOT / 'modulo2')
from app_modulo2 import create_app  # noqa: E402


def token(html):
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


def logged_in(client):
    first=client.get('/',follow_redirects=True)
    auth={'csrf':token(first.text),'nome':'Teste Isolado','senha':'senha-teste-12345'}
    account=client.post('/configurar',data=auth,follow_redirects=True)
    login=client.post('/entrar',data={'csrf':token(account.text),'login':'admin','senha':'senha-teste-12345'},follow_redirects=True)
    assert login.status_code==200
    return token(login.text)


def add_client_product(client, csrf):
    c=client.post('/clientes/salvar',data={'csrf':csrf,'nome':'Cliente Teste','tipo_pessoa':'fisica','cidade':'BH','uf':'MG'},follow_redirects=True)
    assert 'Cliente Teste' in c.text
    p=client.post('/produtos/salvar',data={'csrf':csrf,'codigo_space':'P-001','descricao':'Lampada Ficticia','preco':'25,90','unidade':'UN','grupo':'LED'},follow_redirects=True)
    assert 'Lampada Ficticia' in p.text


def test_pedidos_com_impressao_txt_e_cobranca_automatica(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://testserver') as c:
        csrf=logged_in(c)
        add_client_product(c,csrf)
        p=c.post('/pedidos/salvar',data={'csrf':csrf,'cliente_id':'1','produto_1':'1','quantidade_1':'3', 'pagamento':'prazo','vencimento':'2020-01-01','observacao':'Documento ficticio'},follow_redirects=True)
        assert p.status_code==200 and 'R$ 77,70' in p.text, p.text[:400]
        assert 'Imprimir pedido' in p.text
        assert 'Lampada Ficticia' in c.get('/pedidos/1/imprimir').text
        assert 'window.print()' in c.get('/pedidos/1/imprimir').text
        txt=c.get('/pedidos/1/txt')
        assert txt.status_code == 200 and b'PEDIDO:' in txt.content and b'77,70' in txt.content
        assert b'\r\n' in txt.content
        finance=c.get('/financeiro')
        assert finance.status_code==200 and 'Vencida' in finance.text and '77,70' in finance.text
        assert 'Vencido' in c.get('/clientes').text
        assert c.get('/api/clientes').json()[0]['inadimplente']==1
        assert 'Clientes com contas vencidas' in c.get('/').text
        with sqlite3.connect(tmp_path/'cadastros.sqlite3') as d:
            assert d.execute('SELECT total_centavos FROM pedido').fetchone()[0] == 7770
            assert d.execute('SELECT valor_centavos FROM conta_receber').fetchone()[0]==7770
            assert d.execute('SELECT COUNT(*) FROM pedido_item').fetchone()[0]==1


def test_recebimento_parcial_e_quitacao(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://testserver') as c:
        csrf=logged_in(c);add_client_product(c,csrf)
        p=c.post('/financeiro/nova',data={'csrf':csrf,'cliente_id':'1','descricao':'Conta ficticia vencida','valor':'100,00','vencimento':'2001-01-01'},follow_redirects=True)
        assert p.status_code==200 and 'Vencida' in p.text
        paid=c.post('/financeiro/1/receber',data={'csrf':csrf,'valor':'25,50'},follow_redirects=True)
        assert 'R$ 74,50' in paid.text and 'Vencida' in paid.text
        over=c.post('/financeiro/1/receber',data={'csrf':csrf,'valor':'100,00'})
        assert over.status_code==422
        final=c.post('/financeiro/1/receber',data={'csrf':csrf,'valor':'74,50'},follow_redirects=True)
        assert 'Quitada' in final.text
        assert 'Vencido' not in c.get('/clientes').text
        assert c.get('/api/clientes').json()[0]['inadimplente']==0


def test_regras_e_acesso_nao_autorizado(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://testserver') as c:
        assert c.get('/pedidos').status_code in (401,307,303)
        assert c.get('/financeiro').status_code==401
        csrf=logged_in(c);add_client_product(c,csrf)
        assert c.post('/pedidos/salvar',data={'cliente_id':'1'}).status_code==403
        bad=c.post('/pedidos/salvar',data={'csrf':csrf,'cliente_id':'1','produto_1':'1','quantidade_1':'-5','pagamento':'avista'},follow_redirects=True)
        assert 'Quantidade inválida' in bad.text
        no_due=c.post('/pedidos/salvar',data={'csrf':csrf,'cliente_id':'1','produto_1':'1','quantidade_1':'1','pagamento':'prazo','vencimento':'2020-55-99'},follow_redirects=True)
        assert 'data válida' in no_due.text
        assert c.get('/pedidos/999').status_code==404
        assert c.post('/financeiro/nova',data={'csrf':csrf,'cliente_id':'1','descricao':'Teste','valor':'-5','vencimento':'2020-01-01'}).status_code==200
        with sqlite3.connect(tmp_path/'cadastros.sqlite3') as d:
            assert d.execute('SELECT COUNT(*) FROM pedido').fetchone()[0]==0
            assert d.execute('SELECT COUNT(*) FROM conta_receber').fetchone()[0]==0


def test_migracao_preserva_dados_e_backup(tmp_path):
    # Simula banco anterior com cadastro existente e sem as novas quatro tabelas.
    with sqlite3.connect(tmp_path/'cadastros.sqlite3') as con:
        con.executescript((ROOT/'modulo2/schema.sql').read_text(encoding='utf-8'))
        con.execute("INSERT INTO cliente(nome,tipo_pessoa) VALUES('Antigo Teste','fisica')")
    create_app(tmp_path)
    with sqlite3.connect(tmp_path/'cadastros.sqlite3') as con:
        assert con.execute('SELECT nome FROM cliente').fetchone()[0]=='Antigo Teste'
        assert all(con.execute("SELECT 1 FROM sqlite_master WHERE name=?",(table,)).fetchone() for table in ['pedido','pedido_item','conta_receber','recebimento'])
    backups=list((tmp_path/'backups').glob('antes_v02_*.sqlite3'))
    assert len(backups)==1
    with sqlite3.connect(backups[0]) as con:
        assert con.execute('SELECT nome FROM cliente').fetchone()[0]=='Antigo Teste'
        assert con.execute("SELECT 1 FROM sqlite_master WHERE name='pedido'").fetchone() is None
    create_app(tmp_path)
    assert len(list((tmp_path/'backups').glob('antes_v02_*.sqlite3')))==1
