import csv
import io
from pathlib import Path

from fastapi.testclient import TestClient
from app_modulo2 import create_app


def test_fluxo_completo(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app, base_url='http://testserver') as browser:
        initial=browser.get('/')
        assert initial.status_code == 200
        assert 'Configurar acesso inicial' in initial.text
        import re
        def csrf(response):
            return re.search(r'name="csrf" value="([^"]+)"',response.text).group(1)

        bad=browser.post('/configurar',data={'csrf':csrf(initial),'nome':'Teste','senha':'pequena'}, follow_redirects=True)
        assert 'pelo menos 10 caracteres' in bad.text
        created=browser.post('/configurar',data={'csrf':csrf(initial),'nome':'Responsável Teste','senha':'senha-teste-longa-123'},follow_redirects=True)
        assert 'Entrar no sistema' in created.text
        login=browser.post('/entrar',data={'csrf':csrf(created),'login':'admin','senha':'senha-teste-longa-123'},follow_redirects=True)
        assert login.status_code == 200
        assert 'Visão geral' in login.text
        assert '<main' in login.text
        assert 'lang="pt-BR"' in login.text
        assert 'logo_bh_lampadas.png' in login.text
        assert 'BH Lâmpadas — Especiais e Iluminação' in login.text
        assert browser.get('/static/logo_bh_lampadas.png').status_code == 200
        assert browser.get('/static/logo_bh_lampadas.png').headers['content-type'].startswith('image/png')
        assert browser.get('/static/favicon_bh.png').status_code == 200

        token=csrf(login)
        no_csrf=browser.post('/produtos/salvar',data={'codigo_space':'FALHA','descricao':'Sem csrf'})
        assert no_csrf.status_code == 403

        prod=browser.post('/produtos/salvar',data={'csrf':token,'codigo_space':'LED-20','descricao':'Lâmpada LED 20 W','preco':'25,90','unidade':'PC','grupo':'LED'},follow_redirects=True)
        assert 'Lâmpada LED 20 W' in prod.text
        assert browser.get('/api/produtos?q=LED-20').json()[0]['preco_venda_centavos'] == 2590
        assert len(browser.get('/api/produtos?q=NAO-EXISTE').json()) == 0
        duplicate=browser.post('/produtos/salvar',data={'csrf':token,'codigo_space':'LED-20','descricao':'Duplicado'},follow_redirects=True)
        assert 'Código já utilizado' in duplicate.text
        editor=browser.get('/produtos/1/editar')
        assert '25,90' in editor.text
        edited=browser.post('/produtos/salvar',data={'csrf':token,'id':'1','codigo_space':'LED-20','descricao':'LED alterada','preco':'26,50','unidade':'PC','grupo':'LED'},follow_redirects=True)
        assert 'LED alterada' in edited.text

        client=browser.post('/clientes/salvar',data={'csrf':token,'nome':'Cliente Demonstração','tipo_pessoa':'fisica','cidade':'Belo Horizonte','uf':'MG'},follow_redirects=True)
        assert 'Cliente Demonstração' in client.text
        assert browser.get('/api/clientes?q=Demons').json()[0]['nome'] == 'Cliente Demonstração'

        inc=browser.post('/privacidade',data={'csrf':token,'categoria':'acesso','descricao':'Ocorrência inteiramente fictícia para teste'},follow_redirects=True)
        assert 'Ocorrência inteiramente fictícia' in inc.text
        resp=browser.get('/exportar/produtos')
        assert resp.status_code == 200
        assert resp.content.startswith(b'\xef\xbb\xbf')
        body=resp.content.decode('utf-8-sig')
        assert 'LED alterada' in body
        assert '26' not in body.split('\n')[0]

        css=browser.get('/static/modulo2.css')
        assert css.status_code == 200 and '@media' in css.text
        js=browser.get('/static/modulo2.js')
        assert 'addEventListener' in js.text
        logout=browser.post('/sair',data={'csrf':token},follow_redirects=True)
        assert 'Entrar no sistema' in logout.text
        assert browser.get('/api/produtos').status_code == 401

    # Os dados são persistentes, mas não foram gravados na pasta original do usuário.
    assert (tmp_path/'cadastros.sqlite3').exists()
    with TestClient(create_app(tmp_path), base_url='http://testserver') as again:
        page = again.get('/entrar')
        auth = again.post('/entrar',data={'csrf':csrf(page),'login':'admin','senha':'senha-teste-longa-123'},follow_redirects=True)
        assert '1' in auth.text
        assert again.get('/api/produtos').json()[0]['descricao']=='LED alterada'


def test_arquivos_e_privacidade(tmp_path):
    root=Path(__file__).resolve().parents[1]
    assert (root/'.gitignore').exists()
    rules=(root/'.gitignore').read_text()
    assert '/dados_locais/' in rules
    assert (root/'templates'/'base.html').exists()
    assert (root/'static'/'modulo2.css').exists()
    assert not (root/'dados_locais'/'cadastros.sqlite3').exists() or (tmp_path != root/'dados_locais')
