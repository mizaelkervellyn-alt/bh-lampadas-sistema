# -*- coding: utf-8 -*-
"""BH Lâmpadas — evolução acadêmica para o módulo 2 (FastAPI + HTML/CSS).

Aplicação SOMENTE local. Não há integração fiscal nem homologação para dados reais.
Mantenha o protótipo original independente; esta versão usa outra porta (8766).
"""
import csv
import io
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import hashlib
import hmac

ROOT = Path(__file__).resolve().parent


def generate_password_hash(pw, method=None):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt, 260_000)
    return salt.hex() + ':' + digest.hex()


def check_password_hash(stored, pw):
    try:
        salt, expected = stored.split(':',1)
        computed=hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), bytes.fromhex(salt), 260_000)
        return hmac.compare_digest(expected, computed.hex())
    except (ValueError, AttributeError):
        return False


def create_app(data_dir=None):
    data_dir = Path(data_dir or os.environ.get('BH_DATA_DIR') or ROOT / 'dados_locais')
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / 'cadastros.sqlite3'
    # Chave própria; jamais distribuir nem publicar esse arquivo.
    secret_path = data_dir / '.segredo_sessao_modulo2'
    if not secret_path.exists():
        secret_path.write_bytes(secrets.token_bytes(48))
    session_key = secret_path.read_bytes().hex()

    app = FastAPI(title='BH Lâmpadas – Projeto Integrador II', docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])
    app.add_middleware(SessionMiddleware, secret_key=session_key, same_site='strict', https_only=False, max_age=8*3600)
    app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
    templates = Jinja2Templates(directory=ROOT / 'templates')

    @contextmanager
    def db():
        con = sqlite3.connect(db_path, timeout=15)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    with db() as con:
        con.executescript((ROOT / 'schema.sql').read_text(encoding='utf-8'))

    @app.middleware('http')
    async def no_cache(req, call_next):
        res = await call_next(req)
        if not req.url.path.startswith('/static/'):
            res.headers['Cache-Control'] = 'no-store'
        res.headers['X-Content-Type-Options'] = 'nosniff'
        res.headers['X-Frame-Options'] = 'DENY'
        res.headers['Referrer-Policy'] = 'no-referrer'
        return res

    def rows(sql, args=()):
        with db() as con:
            return [dict(x) for x in con.execute(sql, args).fetchall()]

    def single(sql, args=()):
        rs = rows(sql, args)
        return rs[0] if rs else None

    def is_configured():
        return single('SELECT id FROM usuario LIMIT 1') is not None

    def current_user(req):
        ident = req.session.get('uid')
        if not ident:
            return None
        return single('SELECT id, nome, login, perfil FROM usuario WHERE id=? AND ativo=1', (ident,))

    def csrf(req):
        if not req.session.get('csrf'):
            req.session['csrf'] = secrets.token_urlsafe(24)
        return req.session['csrf']

    def view(req, template, *, title, **data):
        return templates.TemplateResponse(req, template, {
            'title': title, 'user': current_user(req), 'csrf': csrf(req),
            'message': req.query_params.get('ok'), **data,
        })

    async def form(req, *, protected=True):
        raw = await req.body()
        if len(raw) > 128_000:
            raise HTTPException(413, 'Formulário muito grande')
        data = {k: v[0] for k, v in parse_qs(raw.decode('utf-8'), keep_blank_values=True).items()}
        if protected and not secrets.compare_digest(data.get('csrf', ''), csrf(req)):
            raise HTTPException(403, 'Formulário expirado; atualize a página.')
        return data

    def require(req):
        u = current_user(req)
        if not u:
            raise HTTPException(status_code=401, detail='Entre no sistema para continuar.')
        return u

    def go(where):
        return RedirectResponse(where, status_code=303)

    @app.get('/', response_class=HTMLResponse)
    def dashboard(req: Request):
        if not is_configured():
            return go('/configurar')
        if not current_user(req):
            return go('/entrar')
        stats = {
            'clientes': single('SELECT COUNT(*) n FROM cliente WHERE ativo=1')['n'],
            'produtos': single('SELECT COUNT(*) n FROM produto WHERE ativo=1')['n'],
            'sem_preco': single('SELECT COUNT(*) n FROM produto WHERE ativo=1 AND (preco_venda_centavos IS NULL OR preco_venda_centavos=0)')['n'],
            'ocorrencias': single("SELECT COUNT(*) n FROM ocorrencia_privacidade WHERE situacao!='concluida'")['n'],
        }
        return view(req, 'painel.html', title='Visão geral', stats=stats)

    @app.get('/configurar', response_class=HTMLResponse)
    def setup(req: Request):
        if is_configured():
            return go('/entrar')
        return view(req, 'acesso.html', title='Primeiro acesso', setup=True)

    @app.post('/configurar')
    async def setup_post(req: Request):
        if is_configured():
            raise HTTPException(403, 'Conta inicial já criada.')
        d = await form(req)
        name = d.get('nome', '').strip()[:80]
        pw = d.get('senha', '')
        if len(name) < 2 or len(pw) < 10:
            return view(req, 'acesso.html', title='Primeiro acesso', setup=True, error='Informe nome e senha com pelo menos 10 caracteres.')
        with db() as con:
            con.execute('INSERT INTO usuario(nome, login, senha_hash, perfil) VALUES(?,?,?,?)', (name, 'admin', generate_password_hash(pw, method='pbkdf2:sha256:260000'), 'administrador'))
        return go('/entrar?ok=Conta%20criada.%20Entre%20com%20seus%20dados.')

    @app.get('/entrar', response_class=HTMLResponse)
    def login(req: Request):
        if not is_configured():
            return go('/configurar')
        return view(req, 'acesso.html', title='Entrar', setup=False)

    @app.post('/entrar')
    async def login_post(req: Request):
        d = await form(req)
        person = single('SELECT * FROM usuario WHERE login=? AND ativo=1', (d.get('login', '').strip()[:50],))
        if not person or not check_password_hash(person['senha_hash'], d.get('senha', '')):
            return view(req, 'acesso.html', title='Entrar', setup=False, error='Usuário ou senha incorretos.')
        req.session.clear()
        req.session['uid'] = person['id']
        csrf(req)
        return go('/')

    @app.post('/sair')
    async def logout(req: Request):
        await form(req)
        req.session.clear()
        return go('/entrar')

    def products(q=''):
        q = q.strip()[:100]
        term = '%' + q + '%'
        return rows('''SELECT p.id, p.codigo_space, p.descricao, p.unidade, p.preco_venda_centavos, p.ativo,
                      COALESCE(g.nome,'') grupo FROM produto p
                      LEFT JOIN grupo_produto g ON g.id=p.grupo_id
                      WHERE p.ativo=1 AND (p.codigo_space LIKE ? OR p.descricao LIKE ? OR g.nome LIKE ?)
                      ORDER BY p.descricao LIMIT 300''', (term, term, term))

    def clients(q=''):
        q = q.strip()[:100]
        term = '%' + q + '%'
        return rows('''SELECT id,nome,tipo_pessoa,documento,cidade,uf FROM cliente
                      WHERE ativo=1 AND (nome LIKE ? OR COALESCE(codigo_space,'') LIKE ?)
                      ORDER BY nome LIMIT 300''', (term, term))

    @app.get('/produtos', response_class=HTMLResponse)
    def product_list(req: Request, q: str=''):
        require(req)
        return view(req, 'produtos.html', title='Produtos', items=products(q), q=q)

    @app.get('/api/produtos')
    def product_api(req: Request, q: str=''):
        require(req)
        return JSONResponse(products(q))

    @app.get('/produtos/novo', response_class=HTMLResponse)
    def product_new(req: Request):
        require(req)
        return view(req, 'produto_form.html', title='Novo produto', item={}, grupos=rows('SELECT * FROM grupo_produto ORDER BY nome'))

    @app.get('/produtos/{product_id}/editar', response_class=HTMLResponse)
    def product_edit(req: Request, product_id: int):
        require(req)
        p = single('SELECT * FROM produto WHERE id=?', (product_id,))
        if not p:
            raise HTTPException(404, 'Produto não encontrado.')
        p['grupo'] = (single('SELECT nome FROM grupo_produto WHERE id=?', (p['grupo_id'],)) or {}).get('nome', '') if p.get('grupo_id') else ''
        p['preco'] = (f"{p['preco_venda_centavos']/100:.2f}".replace('.',',') if p['preco_venda_centavos'] is not None else '')
        return view(req, 'produto_form.html', title='Editar produto', item=p, grupos=rows('SELECT * FROM grupo_produto ORDER BY nome'))

    @app.post('/produtos/salvar')
    async def product_save(req: Request):
        u = require(req)
        d = await form(req)
        ident = d.get('id', '').strip()
        code = d.get('codigo_space', '').strip()[:60]
        desc = d.get('descricao', '').strip()[:240]
        unit = d.get('unidade', 'UN').strip()[:10] or 'UN'
        raw = d.get('preco', '').replace('R$', '').strip().replace('.', '').replace(',', '.')
        if not code or len(desc) < 2:
            return view(req, 'produto_form.html', title='Produto', item=d, grupos=rows('SELECT * FROM grupo_produto ORDER BY nome'), error='Informe código e descrição.')
        try:
            from decimal import Decimal, ROUND_HALF_UP
            cents = int((Decimal(raw) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) if raw else None
            if cents is not None and cents < 0:
                raise ValueError()
        except Exception:
            return view(req, 'produto_form.html', title='Produto', item=d, grupos=rows('SELECT * FROM grupo_produto ORDER BY nome'), error='Preço inválido.')
        group_name = d.get('grupo', '').strip()[:80]
        try:
            with db() as con:
                group_id = None
                if group_name:
                    gr = con.execute('SELECT id FROM grupo_produto WHERE nome=?', (group_name,)).fetchone()
                    group_id = gr['id'] if gr else con.execute('INSERT INTO grupo_produto(nome) VALUES(?)', (group_name,)).lastrowid
                if ident:
                    exists = con.execute('SELECT id FROM produto WHERE id=?',(int(ident),)).fetchone()
                    if not exists: raise ValueError('Produto inexistente')
                    con.execute('UPDATE produto SET codigo_space=?, descricao=?, unidade=?, preco_venda_centavos=?, grupo_id=?, atualizado_em=CURRENT_TIMESTAMP WHERE id=?', (code,desc,unit,cents,group_id,int(ident)))
                    record_id = int(ident)
                else:
                    record_id = con.execute('INSERT INTO produto(codigo_space,descricao,unidade,preco_venda_centavos,grupo_id) VALUES (?,?,?,?,?)', (code,desc,unit,cents,group_id)).lastrowid
                con.execute('INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,?,?,?)', (u['id'], 'editar' if ident else 'criar', 'produto', record_id))
        except (sqlite3.IntegrityError, ValueError):
            return view(req, 'produto_form.html', title='Produto', item=d, grupos=rows('SELECT * FROM grupo_produto ORDER BY nome'), error='Código já utilizado ou produto inválido.')
        return go('/produtos?ok=Produto%20salvo%20com%20sucesso')

    @app.get('/clientes', response_class=HTMLResponse)
    def client_list(req: Request, q: str=''):
        require(req)
        return view(req, 'clientes.html', title='Clientes', items=clients(q), q=q)

    @app.get('/api/clientes')
    def client_api(req: Request, q: str=''):
        require(req)
        return JSONResponse(clients(q))

    @app.get('/clientes/novo', response_class=HTMLResponse)
    def client_new(req: Request):
        require(req)
        return view(req, 'cliente_form.html', title='Novo cliente', item={})

    @app.get('/clientes/{client_id}/editar', response_class=HTMLResponse)
    def client_edit(req: Request, client_id: int):
        require(req)
        person = single('SELECT * FROM cliente WHERE id=?', (client_id,))
        if not person:
            raise HTTPException(404, 'Cliente não encontrado.')
        return view(req, 'cliente_form.html', title='Editar cliente', item=person)

    @app.post('/clientes/salvar')
    async def client_save(req: Request):
        u = require(req)
        d = await form(req)
        ident = d.get('id', '').strip()
        name = d.get('nome', '').strip()[:150]
        typ = d.get('tipo_pessoa', 'fisica')
        doc = re.sub(r'\D','',d.get('documento','')) or None
        email = d.get('email','').strip()[:150] or None
        tel = d.get('telefone','').strip()[:40] or None
        city = d.get('cidade','').strip()[:100] or None
        uf = d.get('uf','').strip().upper()[:2] or None
        if len(name)<2 or typ not in ('fisica','juridica','estrangeira') or (doc and len(doc) not in (11,14)):
            return view(req,'cliente_form.html',title='Cliente',item=d,error='Confira nome, tipo de pessoa e CPF/CNPJ (11 ou 14 dígitos).')
        try:
            with db() as con:
                if ident:
                    record_id=int(ident)
                    con.execute('UPDATE cliente SET nome=?,tipo_pessoa=?,documento=?,email=?,telefone=?,cidade=?,uf=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?',(name,typ,doc,email,tel,city,uf,record_id))
                else:
                    record_id=con.execute('INSERT INTO cliente(nome,tipo_pessoa,documento,email,telefone,cidade,uf) VALUES (?,?,?,?,?,?,?)',(name,typ,doc,email,tel,city,uf)).lastrowid
                con.execute('INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,?,?,?)',(u['id'],'editar' if ident else 'criar','cliente',record_id))
        except (sqlite3.IntegrityError, ValueError):
            return view(req,'cliente_form.html',title='Cliente',item=d,error='Já existe um cliente com esse documento ou os dados são inválidos.')
        return go('/clientes?ok=Cliente%20salvo%20com%20sucesso')

    @app.get('/exportar/{kind}')
    def export(req: Request, kind: str):
        require(req)
        if kind not in ('produtos','clientes'):
            raise HTTPException(404,'Tipo de exportação desconhecido.')
        buf=io.StringIO()
        writer=csv.writer(buf,delimiter=';')
        if kind=='produtos':
            writer.writerow(['codigo','descricao','grupo','unidade','preco_centavos'])
            for p in products():
                writer.writerow([p['codigo_space'],p['descricao'],p['grupo'],p['unidade'],p['preco_venda_centavos'] if p['preco_venda_centavos'] is not None else ''])
        else:
            writer.writerow(['nome','tipo_pessoa','documento','cidade','uf'])
            for c in clients():
                writer.writerow([c['nome'],c['tipo_pessoa'],c['documento'] or '',c['cidade'] or '',c['uf'] or ''])
        data=('\ufeff'+buf.getvalue()).encode('utf-8')
        return Response(data, media_type='text/csv; charset=utf-8', headers={'Content-Disposition':f'attachment; filename="bh_{kind}_teste.csv"'})

    @app.get('/privacidade', response_class=HTMLResponse)
    def privacy(req: Request):
        require(req)
        items=rows('SELECT id,categoria,descricao,situacao,registrado_em FROM ocorrencia_privacidade ORDER BY id DESC LIMIT 30')
        return view(req,'privacidade.html',title='Privacidade',items=items)

    @app.post('/privacidade')
    async def privacy_post(req: Request):
        u=require(req)
        d=await form(req)
        cat=d.get('categoria','').strip()[:70]
        desc=d.get('descricao','').strip()[:500]
        if not cat or len(desc)<5:
            items=rows('SELECT id,categoria,descricao,situacao,registrado_em FROM ocorrencia_privacidade ORDER BY id DESC LIMIT 30')
            return view(req,'privacidade.html',title='Privacidade',items=items,error='Informe categoria e descrição fictícia.')
        with db() as con:
            con.execute('INSERT INTO ocorrencia_privacidade(categoria,descricao,registrado_por) VALUES(?,?,?)',(cat,desc,u['id']))
        return go('/privacidade?ok=Ocorrencia%20registrada')

    @app.exception_handler(HTTPException)
    async def friendly_error(req, error):
        return templates.TemplateResponse(req,'erro.html',{'title':'Aviso','message':error.detail,'user':current_user(req),'csrf':csrf(req)},status_code=error.status_code)

    return app

app = create_app()

if __name__=='__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=int(os.getenv('BH_PORT','8766')))
