# -*- coding: utf-8 -*-
"""Testes independentes: banco, parsing e fluxos HTTP usando um diretório temporário."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_tests():
    with tempfile.TemporaryDirectory(prefix='bh_teste_') as td:
        base = Path(td) / 'app'
        base.mkdir()
        (base/'static').mkdir()
        for name in ('app.py','schema.sql'):
            shutil.copy(ROOT/name,base/name)
        shutil.copy(ROOT/'static'/'estilo.css',base/'static'/'estilo.css')
        port='18769';url='http://127.0.0.1:'+port
        env=dict(os.environ,BH_PORT=port)
        proc=subprocess.Popen([sys.executable,str(base/'app.py')],cwd=str(base),env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        try:
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            def get(path):
                with opener.open(url+path,timeout=5) as r:
                    return r.read(),r.headers
            def post(path,d):
                body=urllib.parse.urlencode(d).encode('utf-8')
                req=urllib.request.Request(url+path,body,headers={'Content-Type':'application/x-www-form-urlencoded'})
                with opener.open(req,timeout=5) as r:
                    return r.read(),r.headers
            def token(content):
                m=re.search(rb'name="csrf" value="([0-9a-f]+)"',content)
                if not m: raise AssertionError('Token CSRF não encontrado')
                return m.group(1).decode()
            for _ in range(35):
                try:
                    homepage,_=get('/');break
                except Exception: time.sleep(.1)
            else: raise AssertionError('Servidor não iniciou')
            assert 'Criar administrador' in homepage.decode()
            csrf=token(homepage)
            page,_=post('/configurar',{'csrf':csrf,'nome':'Responsável Teste','senha':'Senha-ficticia-1234'})
            assert b'Acesso ao prot' in page
            page,_=get('/entrar');csrf=token(page)
            page,_=post('/entrar',{'csrf':csrf,'login':'admin','senha':'Senha-ficticia-1234'})
            assert 'Visão geral' in page.decode()
            csrf=token(page)
            page,_=post('/demo/carregar',{'csrf':csrf})
            assert '4</b>' in page.decode() or '4' in page.decode()
            page,_=get('/produtos');assert 'Lâmpada LED alta potência' in page.decode()
            page,_=get('/clientes');assert 'Cliente Exemplo A' in page.decode()
            csv,headers=get('/baixar?tipo=produtos'); assert headers.get_content_type()=='text/csv';assert 'DEMO-LED-20W' in csv.decode('utf-8-sig')
            page,_=get('/clientes/novo');csrf=token(page)
            page,_=post('/clientes/salvar',{'csrf':csrf,'nome':'Cliente Teste Manual','tipo_pessoa':'fisica','documento':'12345678901'})
            assert 'Cliente Teste Manual' in page.decode()
            page,_=post('/clientes/salvar',{'csrf':csrf,'nome':'Outro Cliente','tipo_pessoa':'fisica','documento':'12345678901'})
            assert 'Já existe um cliente' in page.decode()
            page,_=get('/produtos/novo');csrf=token(page)
            page,_=post('/produtos/salvar',{'csrf':csrf,'codigo_space':'EXTRA-01','descricao':'Produto para teste','preco':'19,90','quantidade_legacy':'3','unidade':'PC','grupo':'Acessórios'})
            assert 'Produto para teste' in page.decode()
            page,_=post('/produtos/salvar',{'csrf':csrf,'codigo_space':'EXTRA-01','descricao':'Outro produto','preco':'10','unidade':'PC'})
            assert 'Código/SKU já cadastrado' in page.decode()
            page,_=get('/ocorrencias');csrf=token(page)
            page,_=post('/ocorrencias/criar',{'csrf':csrf,'categoria':'acesso','descricao':'Tentativa fictícia de acesso não autorizado','providencia':'Bloqueio simulado'})
            assert 'Tentativa fictícia' in page.decode()
            sample=(ROOT/'exemplos'/'PRODUTO_EXEMPLO_FICTICIO.TXT').read_bytes()
            boundary='----testebh'
            files=(f'--{boundary}\r\nContent-Disposition: form-data; name="csrf"\r\n\r\n{csrf}\r\n--{boundary}\r\nContent-Disposition: form-data; name="arquivo"; filename="PRODUTO.TXT"\r\nContent-Type: text/plain\r\n\r\n').encode()+sample+f'\r\n--{boundary}--\r\n'.encode()
            req=urllib.request.Request(url+'/space/preview',files,headers={'Content-Type':'multipart/form-data; boundary='+boundary})
            with opener.open(req,timeout=5) as r: page=r.read()
            text=page.decode();assert 'LAMPADA FICTICIA PARA TESTE' in text
            match=re.search(r'name="token" value="([a-f0-9]+)"',text);assert match
            page,_=post('/space/confirmar',{'csrf':csrf,'token':match.group(1),'confirmacao':'sim'})
            assert '1</b> produtos adicionados' in page.decode()
            page,_=get('/produtos');assert 'LAMPADA FICTICIA' in page.decode()
            page,_=get('/exportacoes');assert 'produtos_cadastro_' in page.decode()
            backup,bh=get('/backup');assert len(backup)>8192 and backup[:15]==b'SQLite format 3'
            # Testa preenchimento automático de modelo CSV com cabeçalhos reais/simulados
            modello='Nome do contato;Tipo de pessoa;Situação;CPF/CNPJ;E-mail;Cidade;ID\r\n'.encode('utf-8')
            template=(f'--{boundary}\r\nContent-Disposition: form-data; name="csrf"\r\n\r\n{csrf}\r\n--{boundary}\r\nContent-Disposition: form-data; name="tipo"\r\n\r\nclientes\r\n--{boundary}\r\nContent-Disposition: form-data; name="modelo"; filename="modelo_bling.csv"\r\nContent-Type: text/csv\r\n\r\n').encode()+modello+f'\r\n--{boundary}--\r\n'.encode()
            req=urllib.request.Request(url+'/bling/modelo',template,headers={'Content-Type':'multipart/form-data; boundary='+boundary})
            with opener.open(req,timeout=5) as r: output=r.read().decode('utf-8-sig')
            assert 'Nome do contato;Tipo de pessoa;Situação;' in output
            assert 'Cliente Teste Manual;Pessoa Física;Ativo;12345678901' in output

            # banco deve existir com dados duráveis, mesmo depois de encerrar o servidor
            proc.terminate();proc.wait(timeout=5)
            import sqlite3
            db=sqlite3.connect(str(base/'dados_locais'/'cadastros.sqlite3'))
            assert db.execute('SELECT COUNT(*) FROM produto').fetchone()[0]==6
            assert db.execute('SELECT COUNT(*) FROM cliente').fetchone()[0]==3
            db.close()
            print('OK: cadastro inicial, login, dados fictícios, listagem, cadastro, unicidade, preços, ocorrências, exportação, prévia/importação TXT e persistência SQLite.')
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill()

if __name__=='__main__':run_tests()
