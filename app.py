# -*- coding: utf-8 -*-
"""BH Lâmpadas | protótipo acadêmico offline (Python padrão + SQLite).
Executa SOMENTE em 127.0.0.1:8765; não publicar na Internet ou usar como ERP fiscal.
"""
import base64
import csv
import hashlib
import hmac
import html
import io
import json
import os
import re
import secrets
import sqlite3
import sys
import unicodedata
import uuid
import webbrowser
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlsplit

ROOT = Path(__file__).resolve().parent
INSTANCE = ROOT / 'dados_locais'
INSTANCE.mkdir(exist_ok=True)
DB = INSTANCE / 'cadastros.sqlite3'
KEY_FILE = INSTANCE / '.segredo_sessao'
if not KEY_FILE.exists():
    KEY_FILE.write_bytes(secrets.token_bytes(48))
    try: os.chmod(KEY_FILE, 0o600)
    except OSError: pass
KEY = KEY_FILE.read_bytes()
HOST, PORT = '127.0.0.1', int(os.environ.get('BH_PORT', '8765'))

@contextmanager
def db():
    conn = sqlite3.connect(str(DB), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

with db() as c:
    c.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'))
    c.executescript('''
        CREATE TABLE IF NOT EXISTS import_stage (
            token TEXT PRIMARY KEY, dados TEXT NOT NULL, criado_em TEXT NOT NULL
        );
    ''')

def fetch(sql, args=(), one=False):
    with db() as c:
        rows = c.execute(sql, args)
        if one:
            item = rows.fetchone()
            return dict(item) if item else None
        return [dict(r) for r in rows.fetchall()]

def execute(sql, args=()):
    with db() as c:
        cur = c.execute(sql, args)
        return cur.lastrowid

def E(v): return html.escape(str('' if v is None else v), quote=True)
def money(v): return (f'{int(v)/100:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')) if v is not None else '—'
def parse_money(v):
    v = str(v or '').strip().replace('R$', '').replace(' ', '')
    if not v: return None
    if ',' in v: v = v.replace('.', '').replace(',', '.')
    try: return int((Decimal(v) * 100).quantize(Decimal('1')))
    except (InvalidOperation, ValueError): raise ValueError('Preço inválido. Exemplo: 25,90')

def b64(s): return base64.urlsafe_b64encode(s).decode().rstrip('=')
def ub64(s): return base64.urlsafe_b64decode(s + '='*((-len(s))%4))
def sign(obj):
    body = b64(json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode())
    mac = hmac.new(KEY, body.encode(), hashlib.sha256).hexdigest()
    return body + '.' + mac

def verify(token):
    try:
        body, mac = token.split('.', 1)
        if not hmac.compare_digest(mac,hmac.new(KEY,body.encode(),hashlib.sha256).hexdigest()): return None
        data = json.loads(ub64(body))
        if data.get('exp',0) < datetime.now(timezone.utc).timestamp(): return None
        return data
    except (ValueError, UnicodeError, KeyError): return None

def csrf_for(token): return hmac.new(KEY, ('csrf:'+token).encode(),hashlib.sha256).hexdigest()
def hash_pwd(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260_000)
    return salt.hex()+':'+digest.hex()
def verify_pwd(password, stored):
    try:
        salt,expect=stored.split(':')
        return hmac.compare_digest(hash_pwd(password,bytes.fromhex(salt)).split(':')[1],expect)
    except (ValueError, AttributeError): return False

def utc(): return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def clean(v, limit=255): return str(v or '').strip()[:limit]
def digits(v): return re.sub(r'\D','',str(v or ''))
def icon(s): return '<span aria-hidden="true">'+s+'</span>'

def form_field(name,label,value='',kind='text',required=False, hint='',options=None):
    base=f'<label for="{E(name)}">{E(label)}</label>'
    if options:
        opts=''.join(f'<option value="{E(key)}" {"selected" if str(value)==str(key) else ""}>{E(val)}</option>' for key,val in options)
        control=f'<select id="{E(name)}" name="{E(name)}" {"required" if required else ""}>{opts}</select>'
    elif kind=='textarea': control=f'<textarea id="{E(name)}" name="{E(name)}" rows="3">{E(value)}</textarea>'
    else: control=f'<input id="{E(name)}" type="{E(kind)}" name="{E(name)}" value="{E(value)}" {"required" if required else ""} maxlength="255">'
    return f'<div class="field">{base}{control}{f"<small>{E(hint)}</small>" if hint else ""}</div>'

def warning(message): return f'<div class="notice warning">{E(message)}</div>'
def note(message): return f'<div class="notice">{message}</div>'

CSSURL = '/static/estilo.css'

class Handler(BaseHTTPRequestHandler):
    server_version='BH-Lampadas/1.0'
    def log_message(self, fmt,*args):
        print('[acesso]', self.address_string(), fmt%args)

    def send_bytes(self, data, mime='text/html; charset=utf-8', status=200, filename=None, cookie=None):
        self.send_response(status)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
        if cookie: self.send_header('Set-Cookie',cookie)
        if filename: self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(filename))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, url, cookie=None):
        self.send_response(303)
        self.send_header('Location',url)
        self.send_header('Cache-Control','no-store')
        if cookie: self.send_header('Set-Cookie',cookie)
        self.send_header('Content-Length','0')
        self.end_headers()

    def get_token(self):
        jar=cookies.SimpleCookie()
        try: jar.load(self.headers.get('Cookie',''))
        except cookies.CookieError: pass
        tok=jar.get('bh_session')
        token=tok.value if tok else ''
        info=verify(token) if token else None
        if info: return token,info,None
        token=sign({'guest':True,'exp':int((datetime.now(timezone.utc)+timedelta(hours=2)).timestamp()),'nonce':secrets.token_hex(8)})
        return token,verify(token),f'bh_session={token}; HttpOnly; SameSite=Strict; Path=/'

    def layout(self, title, content, account=None, notice_msg='', cookie=None, nav_active=''):
        menu=[('/', 'Painel','painel'),('/clientes','Clientes','clientes'),('/produtos','Produtos','produtos'),('/ocorrencias','Ética digital','ocorrencias'),('/exportacoes','Exportações','exportacoes'),('/space','Arquivo Space','space')]
        nav=''.join(f'<a class="nav-link {"active" if nav_active==k else ""}" href="{path}">{E(label)}</a>' for path,label,k in menu)
        if not account: nav=''
        top=f'''<header class="topbar"><div class="brand"><span class="brand-mark">BL</span><div><b>BH Lâmpadas</b><small>Gestão de cadastros · UFMS</small></div></div><div class="top-right"><span class="chip">PROTÓTIPO LOCAL</span>{f'<span class="username">{E(account["nome"])}</span><form method="post" action="/sair"><input type="hidden" name="csrf" value="{E(self.csrf)}"><button class="textbtn">Sair</button></form>' if account else ''}</div></header>'''
        banner=note('Ambiente acadêmico local: sem emissão de nota fiscal e sem sincronização automática com o Bling. Use dados fictícios na apresentação.') if account else ''
        msg=f'<div class="notice success">{E(notice_msg)}</div>' if notice_msg else ''
        page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(title)} · BH Lâmpadas</title><link rel="stylesheet" href="{CSSURL}"></head><body>{top}<div class="layout"><aside class="sidebar"><div class="side-label">MENU PRINCIPAL</div>{nav}<div class="side-note">Projeto Integrador de TI I<br>UFMS · 2026.2</div></aside><main class="main"><div class="pagehead"><div><p class="eyebrow">BH LÂMPADAS / {E(title).upper()}</p><h1>{E(title)}</h1></div></div>{banner}{msg}{content}<footer>Protótipo de demonstração · Banco de dados local · Não substitui o Space nem o Bling</footer></main></div></body></html>'''
        self.send_bytes(page.encode(),cookie=cookie)

    def user(self):
        token, data, new_cookie=self.get_token()
        self.token, self.csrf, self.new_cookie=token,csrf_for(token),new_cookie
        account=fetch('SELECT id,nome,login FROM usuario WHERE id=? AND ativo=1',(data.get('uid'),),True) if data and data.get('uid') else None
        return account

    def require(self):
        account=self.user()
        if not fetch('SELECT id FROM usuario LIMIT 1',one=True):
            self.redirect('/configurar', self.new_cookie)
            return None
        if not account:
            self.redirect('/entrar', self.new_cookie)
            return None
        return account

    def do_GET(self):
        path=urlsplit(self.path).path
        qs=parse_qs(urlsplit(self.path).query)
        msg={'cliente':'Cliente salvo com sucesso.','produto':'Produto salvo com sucesso.','incidente':'Ocorrência registrada.','ativado':'Situação atualizada.','importado':'Produtos de teste importados; confira os preços e dados antes de utilizar.','demo':'Exemplos fictícios adicionados (registros já existentes foram preservados).','erro':''}.get(qs.get('ok',[''])[0],'')
        if path=='/static/estilo.css':
            self.send_bytes((ROOT/'static'/'estilo.css').read_bytes(),'text/css; charset=utf-8');return
        if not fetch('SELECT id FROM usuario LIMIT 1',one=True):
            self.user()
            self.layout('Primeiro acesso',self.setup_form(),None,cookie=self.new_cookie); return
        if path=='/entrar':
            self.user(); self.layout('Entrar',self.login_form(),None,cookie=self.new_cookie);return
        account=self.require()
        if not account: return
        try:
            if path=='/': self.layout('Visão geral',self.dashboard(),account,msg,nav_active='painel')
            elif path=='/clientes': self.layout('Clientes',self.list_customers(qs),account,msg,nav_active='clientes')
            elif path in ('/clientes/novo',) or re.fullmatch(r'/clientes/\d+/editar',path):
                cid=int(path.split('/')[2]) if '/editar' in path else None
                record=fetch('SELECT * FROM cliente WHERE id=?',(cid,),True) if cid else {}
                if cid and not record: raise ValueError('Cliente não encontrado.')
                self.layout('Editar cliente' if cid else 'Novo cliente',self.customer_form(record),account,nav_active='clientes')
            elif path=='/produtos': self.layout('Produtos',self.list_products(qs),account,msg,nav_active='produtos')
            elif path=='/produtos/novo' or re.fullmatch(r'/produtos/\d+/editar',path):
                pid=int(path.split('/')[2]) if '/editar' in path else None
                record=fetch('SELECT * FROM produto WHERE id=?',(pid,),True) if pid else {}
                if pid and not record: raise ValueError('Produto não encontrado.')
                self.layout('Editar produto' if pid else 'Novo produto',self.product_form(record),account,nav_active='produtos')
            elif path=='/ocorrencias': self.layout('Ocorrências de privacidade',self.incidents_page(),account,msg,nav_active='ocorrencias')
            elif path=='/exportacoes': self.layout('Exportações',self.exports_page(),account,nav_active='exportacoes')
            elif path=='/space': self.layout('Arquivo Space',self.space_page(),account,nav_active='space')
            elif path=='/baixar': self.export_csv(account,qs)
            elif path=='/backup': self.backup_sqlite(account)
            else: self.layout('Página não encontrada',note('Confira o endereço e tente novamente.'),account)
        except (ValueError,sqlite3.IntegrityError) as exc:
            self.layout('Verifique os dados',warning(str(exc))+'<a class="btn" href="/">Voltar</a>',account)

    def read_form(self):
        content_type=self.headers.get('Content-Type','')
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: length=0
        if length<0 or length>4*1024*1024: raise ValueError('Envio acima de 4 MB.')
        body=self.rfile.read(length)
        if 'multipart/form-data' in content_type:
            from email.parser import BytesParser
            from email import policy
            envelope=(f'Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n').encode('utf-8')
            message=BytesParser(policy=policy.default).parsebytes(envelope+body)
            fields={}
            if not message.is_multipart(): raise ValueError('Upload multipart inválido.')
            for part in message.iter_parts():
                name=part.get_param('name',header='content-disposition')
                if not name: continue
                payload=part.get_payload(decode=True) or b''
                if part.get_filename() is not None: fields[name]=payload
                else: fields[name]=payload.decode('utf-8',errors='replace')
            return fields
        return {k:vals[0] for k,vals in parse_qs(body.decode('utf-8'),keep_blank_values=True).items()}

    def do_POST(self):
        account=self.user()
        path=urlsplit(self.path).path
        try:
            data=self.read_form()
            if not hmac.compare_digest(str(data.get('csrf','')),self.csrf): raise ValueError('Sessão expirada ou formulário inválido. Recarregue a página.')
            if not fetch('SELECT id FROM usuario LIMIT 1',one=True):
                if path!='/configurar': raise ValueError('Crie o acesso inicial primeiro.')
                name=clean(data.get('nome'),80);pwd=str(data.get('senha',''))
                if len(name)<2 or len(pwd)<10: raise ValueError('Informe o nome e uma senha com pelo menos 10 caracteres.')
                with db() as c: c.execute("INSERT INTO usuario(nome,login,senha_hash,perfil) VALUES(?,?,?,'administrador')",(name,'admin',hash_pwd(pwd)))
                self.redirect('/entrar');return
            if path=='/entrar':
                record=fetch('SELECT * FROM usuario WHERE login=? AND ativo=1',(clean(data.get('login'),50),),True)
                if not record or not verify_pwd(str(data.get('senha','')),record['senha_hash']):
                    self.layout('Entrar',warning('Usuário ou senha incorretos.')+self.login_form(),None,cookie=self.new_cookie);return
                token=sign({'uid':record['id'],'exp':int((datetime.now(timezone.utc)+timedelta(hours=12)).timestamp()),'nonce':secrets.token_hex(12)})
                self.redirect('/',f'bh_session={token}; HttpOnly; SameSite=Strict; Path=/');return
            if not account:
                self.redirect('/entrar',self.new_cookie);return
            if path=='/sair': self.redirect('/entrar','bh_session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/');return
            if path=='/demo/carregar': self.seed_demo(account);return
            if path=='/clientes/salvar': self.save_customer(data,account);return
            if path=='/produtos/salvar': self.save_product(data,account);return
            if path=='/alternar': self.toggle(data,account);return
            if path=='/ocorrencias/criar': self.save_incident(data,account);return
            if path=='/ocorrencias/situacao': self.incident_status(data,account);return
            if path=='/bling/modelo': self.export_bling_template(data,account);return
            if path=='/space/preview': self.stage_space(data,account);return
            if path=='/space/confirmar': self.confirm_space(data,account);return
            self.layout('Página não encontrada',warning('Ação não encontrada.'),account)
        except (ValueError,sqlite3.IntegrityError) as exc:
            self.layout('Verifique os dados',warning(str(exc))+f'<p><a class="btn secondary" href="/">Voltar ao painel</a></p>',account)

    def setup_form(self):
        return f'''<section class="card auth"><h2>Criar administrador</h2><p>Esta etapa é exibida apenas no primeiro acesso. Nenhuma conta ou senha padrão foi criada.</p><form action="/configurar" method="post"><input type="hidden" name="csrf" value="{self.csrf}">{form_field('nome','Seu nome',required=True)}{form_field('senha','Crie uma senha (mín. 10 caracteres)',kind='password',required=True)}<button class="btn">Criar acesso</button></form></section>'''
    def login_form(self):
        return f'''<section class="card auth"><h2>Acesso ao protótipo</h2><p>Seus cadastros ficam salvos apenas neste computador.</p><form action="/entrar" method="post"><input type="hidden" name="csrf" value="{self.csrf}">{form_field('login','Usuário',value='admin',required=True)}{form_field('senha','Senha',kind='password',required=True)}<button class="btn">Entrar</button></form></section>'''
    def dashboard(self):
        nc=fetch('SELECT COUNT(*) n FROM cliente WHERE ativo=1',one=True)['n']; np=fetch('SELECT COUNT(*) n FROM produto WHERE ativo=1',one=True)['n']
        zero=fetch('SELECT COUNT(*) n FROM produto WHERE ativo=1 AND (preco_venda_centavos IS NULL OR preco_venda_centavos=0)',one=True)['n']
        no_doc=fetch("SELECT COUNT(*) n FROM cliente WHERE ativo=1 AND (documento IS NULL OR documento='')",one=True)['n']
        incidents=fetch("SELECT COUNT(*) n FROM ocorrencia_privacidade WHERE situacao!='concluida'",one=True)['n']
        stats=[('Clientes ativos',nc,'/clientes'),('Produtos ativos',np,'/produtos'),('Preços não informados',zero,'/produtos?filtro=sem_preco'),('Ocorrências abertas',incidents,'/ocorrencias')]
        cards=''.join(f'<a class="metric" href="{url}"><span>{E(name)}</span><b>{int(count)}</b><small>Ver registros →</small></a>' for name,count,url in stats)
        return f'''<section class="metrics">{cards}</section><section class="split"><div class="card"><h2>Ações rápidas</h2><p>Inicie um cadastro ou prepare arquivos para avaliação.</p><div class="buttons"><a class="btn" href="/clientes/novo">+ Cadastrar cliente</a><a class="btn secondary" href="/produtos/novo">+ Cadastrar produto</a><a class="btn secondary" href="/space">Testar PRODUTO.TXT</a><form method="post" action="/demo/carregar" class="inline"><input type="hidden" name="csrf" value="{self.csrf}"><button class="btn secondary">Inserir exemplos fictícios</button></form></div></div><div class="card"><h2>Qualidade dos dados</h2><p><strong>{int(zero)}</strong> produtos sem preço preenchido ou com preço igual a zero.</p><p><strong>{int(no_doc)}</strong> clientes sem CPF/CNPJ — podem ser consumidores finais; confira a necessidade fiscal antes da exportação.</p><p class="fine">Quantidade do Space é mantida como referência, não como estoque confirmado.</p></div></section><section class="card"><h2>Fluxo proposto</h2><div class="steps"><span>1. Cadastro local</span><span>→</span><span>2. Revisão</span><span>→</span><span>3. CSV</span><span>→</span><span>4. Teste no Bling</span></div><p class="fine">Nada é enviado automaticamente a sistemas externos.</p></section>'''

    def seed_demo(self,a):
        """Inclui somente demonstrações, sem apagar registros anteriores."""
        with db() as c:
            examples=[('DEMO-LED-20W','Lâmpada LED alta potência 20W 6500K','Iluminação LED',1300),('DEMO-LED-30W','Lâmpada LED alta potência 30W 3000K','Iluminação LED',2000),('DEMO-LED-50W','Lâmpada LED alta potência 50W 6500K','Iluminação LED',2500),('DEMO-SEM-PRECO','Lâmpada exemplo com preço pendente','Iluminação LED',None)]
            group=c.execute("SELECT id FROM grupo_produto WHERE nome='Iluminação LED'").fetchone()
            gid=group['id'] if group else c.execute("INSERT INTO grupo_produto(nome) VALUES('Iluminação LED')").lastrowid
            for code,desc,grp,price in examples:
                c.execute('INSERT OR IGNORE INTO produto(codigo_space,descricao,grupo_id,unidade,preco_venda_centavos) VALUES(?,?,?,?,?)',(code,desc,gid,'PC',price))
            for name in ('Cliente Exemplo A (fictício)','Cliente Exemplo B (fictício)'):
                if not c.execute('SELECT id FROM cliente WHERE nome=?',(name,)).fetchone():
                    c.execute("INSERT INTO cliente(nome,tipo_pessoa,cidade,uf) VALUES(?,'fisica','Belo Horizonte','MG')",(name,))
            c.execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade) VALUES(?,'carregar_demonstracao','ambiente')",(a['id'],))
        self.redirect('/?ok=demo')

    def list_customers(self,qs):
        term=clean(qs.get('q',[''])[0],100); show_all=qs.get('todos',[''])[0]=='1'
        where='' if show_all else 'WHERE ativo=1'
        if term: where+=(' AND ' if where else 'WHERE ')+"(nome LIKE ? OR documento LIKE ? OR codigo_space LIKE ?)"
        args=['%'+term+'%']*3 if term else []
        rows=fetch(f'SELECT * FROM cliente {where} ORDER BY nome LIMIT 500',args)
        content=''.join(f'''<tr><td><b>{E(r['nome'])}</b><small>{'Pessoa física' if r['tipo_pessoa']=='fisica' else 'Pessoa jurídica' if r['tipo_pessoa']=='juridica' else 'Estrangeiro'}</small></td><td>{E(r['documento'] or 'Não informado')}</td><td>{E(r['cidade'] or '—')}/{E(r['uf'] or '—')}</td><td><span class="pill {'muted' if not r['ativo'] else ''}">{'Ativo' if r['ativo'] else 'Arquivado'}</span></td><td><a href="/clientes/{r['id']}/editar">Editar</a></td></tr>''' for r in rows)
        return f'''<section class="card"><div class="toolbar"><form method="get" action="/clientes" class="search"><input name="q" value="{E(term)}" placeholder="Nome, documento ou código Space"><button class="btn secondary">Pesquisar</button></form><a class="btn" href="/clientes/novo">+ Novo cliente</a></div><p class="fine"><a href="/clientes?todos=1">Mostrar também arquivados</a> · {len(rows)} resultados (até 500)</p><div class="tablewrap"><table><thead><tr><th>Cliente</th><th>Documento</th><th>Cidade/UF</th><th>Situação</th><th>Ações</th></tr></thead><tbody>{content or '<tr><td colspan="5">Nenhum cliente encontrado.</td></tr>'}</tbody></table></div></section>'''

    def customer_form(self,r):
        r=r or {}; v=lambda key:r.get(key) or ''
        fields=form_field('codigo_space','Código antigo (Space)',v('codigo_space'),hint='Opcional: preserva vínculo com o cadastro anterior.')+form_field('tipo_pessoa','Tipo de pessoa',v('tipo_pessoa') or 'fisica',options=[('fisica','Pessoa Física'),('juridica','Pessoa Jurídica'),('estrangeira','Estrangeiro')])+form_field('nome','Nome / razão social',v('nome'),required=True)+form_field('documento','CPF / CNPJ',v('documento'),hint='Opcional neste protótipo; não insira dados reais na apresentação.')+form_field('email','E-mail',v('email'),kind='email')+form_field('telefone','Telefone',v('telefone'))+form_field('cep','CEP',v('cep'))+form_field('logradouro','Logradouro',v('logradouro'))+form_field('numero','Número',v('numero'))+form_field('complemento','Complemento',v('complemento'))+form_field('bairro','Bairro',v('bairro'))+form_field('cidade','Cidade',v('cidade'))+form_field('uf','UF',v('uf'))+form_field('inscricao_estadual','Inscrição estadual',v('inscricao_estadual'))
        toggle=f'''<form method="post" action="/alternar" class="inline"><input type="hidden" name="csrf" value="{self.csrf}"><input type="hidden" name="entidade" value="cliente"><input type="hidden" name="id" value="{r['id']}"><button class="btn {'secondary' if not r['ativo'] else 'danger'}">{'Reativar' if not r['ativo'] else 'Arquivar cliente'}</button></form>''' if r.get('id') else ''
        return f'''<section class="card"><p class="fine">Campos mínimos para a proposta acadêmica. Dados fiscais dependem dos requisitos da conta Bling.</p><form method="post" action="/clientes/salvar"><input type="hidden" name="csrf" value="{self.csrf}"><input type="hidden" name="id" value="{r.get('id','')}"><div class="formgrid">{fields}</div><div class="buttons"><button class="btn">Salvar cliente</button><a class="btn secondary" href="/clientes">Cancelar</a></div></form>{toggle}</section>'''

    def save_customer(self,d,a):
        cid=clean(d.get('id'),15);name=clean(d.get('nome'),150)
        if len(name)<2: raise ValueError('Informe um nome com pelo menos 2 caracteres.')
        typ=clean(d.get('tipo_pessoa'))
        if typ not in ('fisica','juridica','estrangeira'): raise ValueError('Tipo de pessoa inválido.')
        doc=digits(d.get('documento')) or None
        if doc and len(doc) not in (11,14): raise ValueError('CPF/CNPJ deve ter 11 ou 14 dígitos. Validação fiscal completa não está implementada.')
        fields=['codigo_space','tipo_pessoa','nome','documento','inscricao_estadual','email','telefone','cep','logradouro','numero','complemento','bairro','cidade','uf']
        values={'codigo_space':clean(d.get('codigo_space'),40) or None,'tipo_pessoa':typ,'nome':name,'documento':doc}
        for k in fields[4:]: values[k]=clean(d.get(k),150) or None
        cols=', '.join(fields)
        with db() as c:
            try:
                if cid:
                    if not c.execute('SELECT id FROM cliente WHERE id=?',(cid,)).fetchone(): raise ValueError('Cliente inexistente.')
                    c.execute(f'UPDATE cliente SET {", ".join(k+"=?" for k in fields)},atualizado_em=CURRENT_TIMESTAMP WHERE id=?',(*[values[k] for k in fields],cid));idv=int(cid)
                else:
                    cur=c.execute(f'INSERT INTO cliente({cols}) VALUES({",".join("?" for k in fields)})',[values[k] for k in fields]);idv=cur.lastrowid
                c.execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,?,?,?)",(a['id'],'editar' if cid else 'criar','cliente',idv))
            except sqlite3.IntegrityError: raise ValueError('Já existe um cliente com esse CPF/CNPJ ou código Space.')
        self.redirect('/clientes?ok=cliente')

    def list_products(self,qs):
        term=clean(qs.get('q',[''])[0],100);fil=qs.get('filtro',[''])[0]; show_all=qs.get('todos',[''])[0]=='1'
        parts=[] if show_all else ['p.ativo=1'];args=[]
        if term: parts.append('(p.descricao LIKE ? OR p.codigo_space LIKE ? OR g.nome LIKE ?)');args=['%'+term+'%']*3
        if fil=='sem_preco': parts.append('(p.preco_venda_centavos IS NULL OR p.preco_venda_centavos=0)')
        where='WHERE '+' AND '.join(parts) if parts else ''
        rows=fetch(f'SELECT p.*,g.nome grupo FROM produto p LEFT JOIN grupo_produto g ON g.id=p.grupo_id {where} ORDER BY p.descricao LIMIT 500',args)
        content=''.join(f'''<tr><td><b>{E(r['descricao'])}</b><small>{E(r['codigo_space'] or 'Sem código')}</small></td><td>{E(r['grupo'] or '—')}</td><td>{E(r['unidade'])}</td><td>{money(r['preco_venda_centavos'])}</td><td>{'<span class="pill warn">Revisar</span>' if r['preco_venda_centavos'] in (0,None) else '<span class="pill">OK</span>'}</td><td><a href="/produtos/{r['id']}/editar">Editar</a></td></tr>''' for r in rows)
        return f'''<section class="card"><div class="toolbar"><form class="search" action="/produtos" method="get"><input name="q" value="{E(term)}" placeholder="Buscar por código, descrição ou grupo"><button class="btn secondary">Pesquisar</button></form><a class="btn" href="/produtos/novo">+ Novo produto</a></div><p class="fine"><a href="/produtos?filtro=sem_preco">Mostrar apenas preços pendentes</a> · <a href="/produtos?todos=1">Mostrar arquivados</a> · {len(rows)} resultados (até 500)</p><div class="tablewrap"><table><thead><tr><th>Produto / código</th><th>Grupo</th><th>Unidade</th><th>Preço (R$)</th><th>Alerta</th><th>Ações</th></tr></thead><tbody>{content or '<tr><td colspan="6">Nenhum produto encontrado.</td></tr>'}</tbody></table></div></section>'''

    def product_form(self,r):
        r=r or {};v=lambda k:r.get(k) if r.get(k) is not None else ''
        group=fetch('SELECT nome FROM grupo_produto WHERE id=?',(v('grupo_id'),),True) if v('grupo_id') else None
        fields=form_field('codigo_space','Código / SKU',v('codigo_space'),required=True)+form_field('descricao','Descrição do produto',v('descricao'),required=True)+form_field('grupo','Grupo / categoria',group['nome'] if group else '')+form_field('unidade','Unidade de medida',v('unidade') or 'PC')+form_field('preco','Preço de venda (R$)',money(v('preco_venda_centavos')) if v('preco_venda_centavos')!='' else '',hint='Se não houver preço no TXT, deixe em branco até conferir.')+form_field('quantidade_legacy','Quantidade informada no Space (referência)',v('quantidade_legacy'),kind='number',hint='Não presumir que seja o estoque atual.')+form_field('digito_space','Dígito Space',v('digito_space'))+form_field('origem_space','Origem do Space',v('origem_space'))+form_field('codigo_tributario_space','Código tributário original',v('codigo_tributario_space'))+form_field('aliquota_icms_space','Alíquota ICMS original (texto)',v('aliquota_icms_space'))
        toggle=f'''<form action="/alternar" method="post"><input type="hidden" name="csrf" value="{self.csrf}"><input type="hidden" name="entidade" value="produto"><input type="hidden" name="id" value="{r['id']}"><button class="btn {'secondary' if not r['ativo'] else 'danger'}">{'Reativar' if not r['ativo'] else 'Arquivar produto'}</button></form>''' if r.get('id') else ''
        return f'''<section class="card"><p class="fine">Cadastro de produtos: preço e quantidade são tratados separadamente. Dados tributários importados não são validados para emissão de NF-e.</p><form action="/produtos/salvar" method="post"><input type="hidden" name="csrf" value="{self.csrf}"><input type="hidden" name="id" value="{r.get('id','')}"><div class="formgrid">{fields}</div><div class="buttons"><button class="btn">Salvar produto</button><a class="btn secondary" href="/produtos">Cancelar</a></div></form>{toggle}</section>'''

    def save_product(self,d,a):
        pid=clean(d.get('id'),15);code=clean(d.get('codigo_space'),60);desc=clean(d.get('descricao'),240)
        if not code or len(desc)<2: raise ValueError('Código e descrição são obrigatórios.')
        preco=parse_money(d.get('preco'))
        if preco is not None and preco<0: raise ValueError('Preço não pode ser negativo.')
        quantity=clean(d.get('quantidade_legacy'))
        if quantity and (not quantity.isdigit() or int(quantity)>9999999): raise ValueError('A quantidade de referência deve ser inteira e não negativa.')
        gname=clean(d.get('grupo'),80)
        with db() as c:
            gid=None
            if gname:
                group=c.execute('SELECT id FROM grupo_produto WHERE nome=? COLLATE NOCASE',(gname,)).fetchone()
                gid=group['id'] if group else c.execute('INSERT INTO grupo_produto(nome) VALUES(?)',(gname,)).lastrowid
            vals=(code,clean(d.get('digito_space'),2) or None,desc,clean(d.get('unidade'),6) or 'PC',gid,int(quantity) if quantity else None,preco,clean(d.get('origem_space'),5) or None,clean(d.get('codigo_tributario_space'),6) or None,clean(d.get('aliquota_icms_space'),12) or None)
            try:
                if pid:
                    if not c.execute('SELECT id FROM produto WHERE id=?',(pid,)).fetchone(): raise ValueError('Produto inexistente.')
                    c.execute('''UPDATE produto SET codigo_space=?,digito_space=?,descricao=?,unidade=?,grupo_id=?,quantidade_legacy=?,preco_venda_centavos=?,origem_space=?,codigo_tributario_space=?,aliquota_icms_space=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?''',(*vals,pid)); idv=int(pid)
                else:
                    idv=c.execute('''INSERT INTO produto(codigo_space,digito_space,descricao,unidade,grupo_id,quantidade_legacy,preco_venda_centavos,origem_space,codigo_tributario_space,aliquota_icms_space) VALUES(?,?,?,?,?,?,?,?,?,?)''',vals).lastrowid
                c.execute('INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,?,?,?)',(a['id'],'editar' if pid else 'criar','produto',idv))
            except sqlite3.IntegrityError: raise ValueError('Código/SKU já cadastrado. Use a edição em vez de criar outro produto.')
        self.redirect('/produtos?ok=produto')

    def toggle(self,d,a):
        entity=clean(d.get('entidade'))
        if entity not in ('cliente','produto'): raise ValueError('Tipo inválido.')
        rid=int(d.get('id','0'));record=fetch(f'SELECT id,ativo FROM {entity} WHERE id=?',(rid,),True)
        if not record: raise ValueError('Registro inexistente.')
        execute(f'UPDATE {entity} SET ativo=?,atualizado_em=CURRENT_TIMESTAMP WHERE id=?',(0 if record['ativo'] else 1,rid))
        execute('INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,?,?,?)',(a['id'],'arquivar' if record['ativo'] else 'reativar',entity,rid))
        self.redirect(('/clientes' if entity=='cliente' else '/produtos')+'?ok=ativado')

    def incidents_page(self):
        data=fetch('SELECT * FROM ocorrencia_privacidade ORDER BY registrado_em DESC LIMIT 100')
        entries=''.join(f'''<div class="incident"><div><b>{E(r['categoria'])}</b> <span class="pill">{E(r['situacao'].replace('_',' '))}</span><small>{E(r['registrado_em'])}</small></div><p>{E(r['descricao'])}</p>{f'<p><strong>Providência:</strong> {E(r["providencia"])}</p>' if r['providencia'] else ''}<form method="post" action="/ocorrencias/situacao"><input type="hidden" name="csrf" value="{self.csrf}"><input type="hidden" name="id" value="{r['id']}"><select name="situacao"><option value="aberta" {'selected' if r['situacao']=='aberta' else ''}>Aberta</option><option value="em_analise" {'selected' if r['situacao']=='em_analise' else ''}>Em análise</option><option value="concluida" {'selected' if r['situacao']=='concluida' else ''}>Concluída</option></select><button class="btn secondary">Atualizar</button></form></div>''' for r in data)
        fields=form_field('categoria','Categoria',options=[('acesso','Acesso indevido'),('compartilhamento','Compartilhamento indevido'),('exportacao','Exportação incorreta'),('outro','Outra situação')])+form_field('descricao','Descrição sem dados pessoais',kind='textarea',required=True,hint='Use exemplos fictícios na apresentação; não registre CPF ou documentos aqui.')+form_field('providencia','Medida adotada',kind='textarea')
        form=f'''<section class="card"><h2>Registrar ocorrência de privacidade</h2><p>Este módulo é educativo e não substitui um procedimento institucional de gestão de incidentes.</p><form method="post" action="/ocorrencias/criar"><input type="hidden" name="csrf" value="{self.csrf}"><div class="formgrid">{fields}</div><button class="btn">Registrar ocorrência</button></form></section>'''
        return form+f'<section class="card"><h2>Histórico</h2>{entries or "<p>Nenhuma ocorrência registrada.</p>"}</section>'

    def save_incident(self,d,a):
        cat=clean(d.get('categoria'),30);desc=clean(d.get('descricao'),2000);med=clean(d.get('providencia'),2000)
        if cat not in ('acesso','compartilhamento','exportacao','outro') or len(desc)<10: raise ValueError('Selecione uma categoria e descreva a ocorrência com pelo menos dez caracteres.')
        rid=execute('INSERT INTO ocorrencia_privacidade(categoria,descricao,providencia,registrado_por) VALUES(?,?,?,?)',(cat,desc,med,a['id']))
        execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,'criar','ocorrencia',?)",(a['id'],rid))
        self.redirect('/ocorrencias?ok=incidente')
    def incident_status(self,d,a):
        st=clean(d.get('situacao'))
        if st not in ('aberta','em_analise','concluida'): raise ValueError('Situação inválida.')
        rid=int(d.get('id','0'));execute('UPDATE ocorrencia_privacidade SET situacao=? WHERE id=?',(st,rid))
        self.redirect('/ocorrencias?ok=incidente')

    def exports_page(self):
        logs=fetch('SELECT e.*,u.nome FROM exportacao e LEFT JOIN usuario u ON e.criado_por=u.id ORDER BY e.id DESC LIMIT 25')
        rows=''.join(f'<tr><td>{E(r["criado_em"])}</td><td>{E(r["tipo"])}</td><td>{int(r["total_registros"])}</td><td>{E(r["nome_arquivo"])}</td></tr>' for r in logs)
        return f'''<section class="card"><h2>Exportação de cadastros</h2>{note('<strong>CSV genérico:</strong> arquivos prontos para abrir em planilhas. Ainda não são planilhas homologadas pelo Bling. Para testar no Bling, precisaremos conferir as colunas com os modelos oficiais.')}<div class="buttons"><a class="btn" href="/baixar?tipo=clientes">Baixar clientes CSV</a><a class="btn secondary" href="/baixar?tipo=produtos">Baixar produtos CSV</a></div><div class="buttons"><a class="btn secondary" href="/backup">Salvar cópia de segurança do banco</a></div><p class="fine">Não serão incluídos clientes ou produtos arquivados. O Bling não é acessado por este aplicativo.</p></section><section class="card"><h2>Preparar uma planilha a partir do CSV modelo do Bling</h2><p>Baixe a <strong>Tabela Modelo em CSV</strong> dentro da conta da loja e envie-a aqui. O sistema preserva os cabeçalhos e preenche apenas as colunas que consegue reconhecer. Essa geração é experimental; será necessário validar e revisar a planilha no Bling antes de importar.</p><form action="/bling/modelo" method="post" enctype="multipart/form-data"><input type="hidden" name="csrf" value="{self.csrf}"><div class="formgrid">{form_field('tipo','Tipo de cadastro',options=[('clientes','Clientes / contatos'),('produtos','Produtos')])}<div class="field"><label for="modelo">Modelo CSV fornecido pelo Bling (máx. 500 KB)</label><input type="file" id="modelo" name="modelo" accept=".csv,text/csv" required></div></div><button class="btn">Gerar CSV no layout do modelo</button></form><p class="fine">Para clientes novos, o ID do Bling permanece vazio. Não envie a planilha gerada para importação sem conferir os dados e identificar cadastros que já existem no Bling.</p></section><section class="card"><h2>Arquivos gerados anteriormente</h2><div class="tablewrap"><table><thead><tr><th>Data</th><th>Categoria</th><th>Registros</th><th>Arquivo</th></tr></thead><tbody>{rows or '<tr><td colspan="4">Nenhuma exportação ainda.</td></tr>'}</tbody></table></div></section>'''

    def export_csv(self,a,qs):
        kind=qs.get('tipo',[''])[0]
        if kind=='clientes':
            fields=['codigo_space','tipo_pessoa','nome','documento','inscricao_estadual','email','telefone','cep','logradouro','numero','complemento','bairro','cidade','uf']
            rows=fetch('SELECT '+','.join(fields)+' FROM cliente WHERE ativo=1 ORDER BY nome')
        elif kind=='produtos':
            fields=['codigo_space','digito_space','descricao','unidade','grupo','quantidade_legacy','preco_reais','origem_space','codigo_tributario_space','aliquota_icms_space']
            rows=fetch('''SELECT p.codigo_space,p.digito_space,p.descricao,p.unidade,g.nome grupo,p.quantidade_legacy,p.preco_venda_centavos,p.origem_space,p.codigo_tributario_space,p.aliquota_icms_space FROM produto p LEFT JOIN grupo_produto g ON g.id=p.grupo_id WHERE p.ativo=1 ORDER BY p.descricao''')
            for r in rows: r['preco_reais']=str(Decimal(r['preco_venda_centavos'])/100).replace('.',',') if r['preco_venda_centavos'] is not None else ''
        else: raise ValueError('Tipo de exportação inválido.')
        output=io.StringIO(newline='');writer=csv.writer(output,delimiter=';',lineterminator='\r\n');writer.writerow(fields)
        for row in rows:
            def safe(v):
                s='' if v is None else str(v)
                return "'"+s if s.startswith(('=','+','-','@')) else s
            writer.writerow([safe(row.get(k)) for k in fields])
        file=f'{kind}_cadastro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with db() as c:
            eid=c.execute('INSERT INTO exportacao(tipo,nome_arquivo,total_registros,criado_por,destino,situacao) VALUES(?,?,?,?,?,?)',(kind,file,len(rows),a['id'],'arquivo CSV genérico','gerado')).lastrowid
            c.execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade,registro_id) VALUES(?,'exportar','exportacao',?)",(a['id'],eid))
        self.send_bytes(output.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8',filename=file)

    def backup_sqlite(self,a):
        """Download de snapshot consistente do SQLite (uso local)."""
        import tempfile
        fd,where=tempfile.mkstemp(prefix='bh_backup_',suffix='.sqlite3',dir=str(INSTANCE))
        os.close(fd)
        try:
            source=sqlite3.connect(str(DB))
            dest=sqlite3.connect(where)
            try: source.backup(dest)
            finally:dest.close();source.close()
            data=Path(where).read_bytes()
            execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade) VALUES(?,'backup','banco')",(a['id'],))
            self.send_bytes(data,'application/octet-stream',filename='backup_bh_lampadas_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.sqlite3')
        finally:
            try:os.unlink(where)
            except OSError:pass

    def export_bling_template(self,d,a):
        kind=clean(d.get('tipo'),20)
        if kind not in ('clientes','produtos'): raise ValueError('Escolha clientes ou produtos.')
        raw=d.get('modelo')
        if not isinstance(raw,bytes) or not raw or len(raw)>500*1024: raise ValueError('Envie um modelo Bling em CSV com até 500 KB.')
        try: decoded=raw.decode('utf-8-sig')
        except UnicodeDecodeError: decoded=raw.decode('cp1252')
        first=decoded.splitlines()[0] if decoded.splitlines() else ''
        sep=max((';',',','\t'),key=lambda x:first.count(x))
        headers=next(csv.reader(io.StringIO(decoded),delimiter=sep),[])
        if not headers or len(headers)>160: raise ValueError('Cabeçalho inválido ou não encontrado no modelo CSV.')
        # O modelo da loja define o layout, mas não comprova que os valores fiscais estão completos.
        norm=lambda t:''.join(c for c in unicodedata.normalize('NFKD',str(t).lower()) if not unicodedata.combining(c)).replace('_',' ').strip()
        hlist=[norm(x) for x in headers]
        if kind=='clientes':
            if not any('nome' in h for h in hlist): raise ValueError('Não reconheci uma coluna de nome de contato no CSV.')
            records=fetch('SELECT * FROM cliente WHERE ativo=1 ORDER BY nome')
            if len(records)>10000: raise ValueError('O Bling limita contatos por planilha. Divida o arquivo em lotes de até 10.000.')
            def value(h,r):
                h=norm(h)
                if h in ('id','id do contato','codigo bling'): return ''
                if 'nome' in h or 'razao social' in h: return r['nome']
                if 'tipo' in h and 'pessoa' in h: return {'fisica':'Pessoa Física','juridica':'Pessoa Jurídica','estrangeira':'Estrangeiro'}.get(r['tipo_pessoa'],'')
                if 'situac' in h or 'status'==h: return 'Ativo'
                if 'cpf' in h or 'cnpj' in h: return r['documento'] or ''
                if 'inscricao estadual' in h or h in ('ie',): return r['inscricao_estadual'] or ''
                if h in ('email','e-mail'):return r['email'] or ''
                if 'telefone' in h or 'celular' in h: return r['telefone'] or ''
                if h=='cep':return r['cep'] or ''
                if h in ('endereco','logradouro','rua'):return r['logradouro'] or ''
                if h in ('numero','numero endereco'):return r['numero'] or ''
                if h=='complemento':return r['complemento'] or ''
                if h=='bairro':return r['bairro'] or ''
                if h in ('cidade','municipio'):return r['cidade'] or ''
                if h in ('uf','estado'):return r['uf'] or ''
                return ''
        else:
            if not any(('descricao' in h or 'nome' in h) for h in hlist): raise ValueError('Não reconheci a coluna de descrição do produto.')
            records=fetch('SELECT p.*,g.nome AS grupo_nome FROM produto p LEFT JOIN grupo_produto g ON g.id=p.grupo_id WHERE p.ativo=1 ORDER BY p.descricao')
            if len(records)>1000: raise ValueError('O Bling limita produtos por planilha. Divida o arquivo em lotes de até 1.000.')
            def value(h,r):
                h=norm(h)
                if h=='id' or h=='id produto':return ''
                if 'codigo' in h and ('sku' in h or h=='codigo' or 'produto' in h):return r['codigo_space'] or ''
                if h in ('sku','referencia'):return r['codigo_space'] or ''
                if 'descricao' in h or h=='nome':return r['descricao']
                if h in ('unidade','unidade de medida'):return r['unidade']
                if h in ('grupo','grupo de produto','grupo de produtos','categoria'):return r['grupo_nome'] or ''
                if h in ('preco','preco de venda','valor de venda','valor'):return str(Decimal(r['preco_venda_centavos'])/100).replace('.',',') if r['preco_venda_centavos'] is not None else ''
                if 'estoque' in h or 'quantidade' in h:return ''  # quantidade do Space não é saldo comprovado
                if h in ('origem', 'ncm','cest','gtin','ean'):return ''  # dados fiscais dependem de conferência
                return ''
        out=io.StringIO(newline='');writer=csv.writer(out,delimiter=sep,lineterminator='\r\n')
        writer.writerow(headers)
        for record in records:
            row=[]
            for header in headers:
                val=str(value(header,record) or '')
                # evita células interpretadas como fórmulas no Excel
                if val.startswith(('=','+','-','@')): val="'"+val
                row.append(val)
            writer.writerow(row)
        file='bling_modelo_'+kind+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv'
        with db() as c:
            c.execute("INSERT INTO exportacao(tipo,nome_arquivo,total_registros,criado_por,destino,situacao) VALUES(?,?,?,?,?,?)",(kind,file,len(records),a['id'],'modelo CSV Bling (experimental)','gerado'))
            c.execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade) VALUES(?,'gerar_modelo_bling','exportacao')",(a['id'],))
        self.send_bytes(out.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8',filename=file)

    def space_page(self):
        return f'''<section class="card"><h2>Pré-visualizar exportação PRODUTO.TXT</h2><p>O Space mostrou a estrutura das <strong>primeiras 106 posições</strong> do arquivo de produtos. Esta ferramenta lê apenas o formato inicial fotografado. Não é um migrador completo ou certificado.</p><div class="notice warning">Atenção: o TXT não mostra o preço de venda. A quantidade também não foi confirmada como saldo de estoque. Esses dados não serão inventados.</div><form method="post" action="/space/preview" enctype="multipart/form-data"><input type="hidden" name="csrf" value="{self.csrf}"><div class="field"><label for="arquivo">Selecione um arquivo TXT de teste (até 2 MB)</label><input type="file" id="arquivo" name="arquivo" accept=".txt,text/plain" required></div><button class="btn">Analisar arquivo sem importar</button></form><p class="fine">O processamento ocorre no computador local, sem envio à Internet. Para testes acadêmicos, evite arquivos com dados reais.</p></section><section class="card"><h2>Campos identificados na foto do Space</h2><p><code>Tipo 1(1) | Código(10) | Dígito(1) | Descrição(40) | Unidade(3) | Quantidade(4) | Grupo(5) | Descrição grupo(25) | Fornecedores(5+5) | Origem(1) | Tributo(2) | ICMS(4)</code></p><p class="fine">Se o Space exportar uma linha mais longa, o leitor vai analisar apenas as primeiras 106 posições e avisar sobre o restante não mapeado.</p></section>'''

    def stage_space(self,d,a):
        raw=d.get('arquivo')
        if not isinstance(raw,bytes) or not raw: raise ValueError('Selecione um arquivo TXT válido.')
        if len(raw)>2*1024*1024: raise ValueError('Arquivo grande demais para demonstração (2 MB).')
        records,issues=parse_space(raw)
        if not records: raise ValueError('Nenhum registro PRODUTO.TXT reconhecido. Verifique se é o arquivo correto e se há registros do tipo 1.')
        token=uuid.uuid4().hex
        execute('INSERT INTO import_stage(token,dados,criado_em) VALUES(?,?,?)',(token,json.dumps(records,ensure_ascii=False),utc()))
        table=''.join(f'<tr><td>{E(r["codigo_space"])}</td><td>{E(r["descricao"])}</td><td>{E(r["unidade"])}</td><td>{E(r["grupo_nome"])}</td><td>{E(r["quantidade_legacy"])}</td></tr>' for r in records[:25])
        problems='<br>'.join(E(w) for w in issues[:10])
        content=f'''<section class="card"><h2>Prévia da leitura</h2>{note('Foram reconhecidos <b>'+str(len(records))+'</b> registros, mas ainda não foram incluídos no banco.')}<div class="tablewrap"><table><thead><tr><th>Código</th><th>Descrição</th><th>UN</th><th>Grupo</th><th>Qtd. referencial</th></tr></thead><tbody>{table}</tbody></table></div><p class="fine">Exibindo até 25 registros. Preço ausente: ficará em branco até conferência.</p>{warning(problems) if problems else ''}<form method="post" action="/space/confirmar"><input type="hidden" name="csrf" value="{self.csrf}"><input type="hidden" name="token" value="{token}"><label class="check"><input type="checkbox" name="confirmacao" value="sim" required> Confirmo que estes registros são fictícios ou que tenho autorização para processá-los e que desejo criar apenas produtos ainda não cadastrados.</label><button class="btn">Importar registros novos</button><a class="btn secondary" href="/space">Cancelar</a></form></section>'''
        self.layout('Prévia do Space',content,a,nav_active='space')

    def confirm_space(self,d,a):
        if d.get('confirmacao')!='sim': raise ValueError('Confirme o procedimento para prosseguir.')
        token=clean(d.get('token'),60);record=fetch('SELECT dados FROM import_stage WHERE token=?',(token,),True)
        if not record: raise ValueError('Essa prévia não existe mais. Gere outra.')
        products=json.loads(record['dados']);added=0;skipped=0
        with db() as c:
            for x in products:
                if c.execute('SELECT id FROM produto WHERE codigo_space=?',(x['codigo_space'],)).fetchone():skipped+=1;continue
                name=x.get('grupo_nome',''); gid=None
                if name:
                    g=c.execute('SELECT id FROM grupo_produto WHERE nome=? COLLATE NOCASE',(name,)).fetchone()
                    gid=g['id'] if g else c.execute('INSERT INTO grupo_produto(codigo_space,nome) VALUES(?,?)',(None,name)).lastrowid
                c.execute('''INSERT INTO produto (codigo_space,digito_space,descricao,unidade,grupo_id,quantidade_legacy,preco_venda_centavos,codigo_fornecedor_1,codigo_fornecedor_2,origem_space,codigo_tributario_space,aliquota_icms_space) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(x['codigo_space'],x['digito_space'],x['descricao'],x['unidade'],gid,x['quantidade_legacy'],None,x['fornecedor_1'],x['fornecedor_2'],x['origem_space'],x['codigo_tributario_space'],x['aliquota_icms_space']))
                added+=1
            c.execute('DELETE FROM import_stage WHERE token=?',(token,))
            c.execute("INSERT INTO log_auditoria(usuario_id,tipo_acao,entidade) VALUES(?,'importar_space','produto')",(a['id'],))
        alerta = warning('Revise preços, códigos fiscais e quantidade de referência antes de qualquer uso real.')
        conteudo = (
            f'<section class="card"><h2>Leitura concluída</h2>'
            f'<p><b>{added}</b> produtos adicionados · <b>{skipped}</b> já existentes, ignorados.</p>'
            f'{alerta}<a class="btn" href="/produtos">Conferir produtos</a></section>'
        )
        self.layout('Resultado da importação', conteudo, a, nav_active='space')


def parse_space(raw):
    """Interpreta posicoes 1..106 do registro tipo '1' do layout fotografado.
    Campos são endereçados por byte; CP1252 é hipótese de codificação legado.
    """
    result=[]; issues=[]
    for ln,line in enumerate(raw.splitlines(),1):
        if not line.strip(): continue
        if len(line)<106:
            issues.append(f'Linha {ln}: só {len(line)} bytes; precisa de 106.'); continue
        if line[:1]!=b'1':
            issues.append(f'Linha {ln}: tipo de registro diferente de 1; ignorado.');continue
        def field(a,b):return line[a-1:b].decode('cp1252',errors='replace').strip()
        code=field(2,11);desc=field(13,52)
        if not code or not desc:
            issues.append(f'Linha {ln}: código ou descrição ausente.');continue
        qty=field(56,59)
        if qty and not qty.isdigit(): issues.append(f'Linha {ln}: quantidade não numérica, mantida vazia.')
        result.append({'codigo_space':code,'digito_space':field(12,12),'descricao':desc,'unidade':field(53,55) or 'PC', 'quantidade_legacy':int(qty) if qty.isdigit() else None,'grupo_codigo':field(60,64),'grupo_nome':field(65,89), 'fornecedor_1':field(90,94),'fornecedor_2':field(95,99),'origem_space':field(100,100),'codigo_tributario_space':field(101,102),'aliquota_icms_space':field(103,106)})
        if len(line)>106 and len(issues)<20: issues.append(f'Linha {ln}: campos após posição 106 ignorados (layout parcial).')
    return result,issues

if __name__=='__main__':
    print('='*62)
    print('BH LÂMPADAS — protótipo acadêmico local')
    print(f'Abra no navegador: http://{HOST}:{PORT}')
    print(f'Banco local: {DB}')
    print('Para encerrar: Ctrl+C')
    print('='*62)
    try:
        ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nAplicação encerrada.')
