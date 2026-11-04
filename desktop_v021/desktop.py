# -*- coding: utf-8 -*-
"""BH Lampadas Desktop experimental. Somente teste local com dados ficticios.
Abre uma janela nativa via Edge WebView2 + pywebview e executa o FastAPI
na interface de loopback local. Nao substitui o Space nem emite NF-e.
"""
import os
import socket
import sys
import threading
import time
from pathlib import Path


def resource_dir():
    # Diretório dos recursos dentro do ZIP ou da distribuição do PyInstaller.
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'modulo2'


def user_data_dir():
    """Dados ficam fora do diretório de código, em local privado do usuário."""
    local = os.environ.get('LOCALAPPDATA')
    if local:
        return Path(local) / 'BH_Lampadas_Desktop_Experimental' / 'dados_locais'
    return Path.home() / '.bh_lampadas_desktop_experimental' / 'dados_locais'


def prepare_environment():
    resources = resource_dir()
    if not (resources / 'schema.sql').is_file():
        raise FileNotFoundError('Recursos do aplicativo ausentes: ' + str(resources / 'schema.sql'))
    data = user_data_dir()
    data.mkdir(parents=True, exist_ok=True)
    os.environ['BH_DATA_DIR'] = str(data)
    os.environ['BH_RESOURCES_DIR'] = str(resources)
    # No ZIP o arquivo app_modulo2.py é localizado dentro da pasta modulo2.
    # No executável sua importação é encontrada pelo PyInstaller (via --paths).
    if str(resources) not in sys.path:
        sys.path.insert(0, str(resources))
    return resources, data


def start_local_server(app, timeout=15.0):
    """Inicia Uvicorn em porta livre restrita a 127.0.0.1. Retorna servidor e thread.
    Porta livre é escolhida com socket já aberto, evitando colisão com módulo 2.
    """
    import uvicorn
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    config = uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning', access_log=False)
    server = uvicorn.Server(config)
    worker = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True, name='FastAPI-local')
    worker.start()
    limit = time.monotonic() + timeout
    while not server.started and worker.is_alive() and time.monotonic() < limit:
        time.sleep(0.05)
    if not server.started:
        server.should_exit = True
        worker.join(timeout=2)
        sock.close()
        raise RuntimeError('Nao foi possivel iniciar o servidor local do sistema.')
    return server, worker, sock, 'http://127.0.0.1:{}'.format(port)


def report_error(error):
    message = ('Nao foi possivel abrir o BH Lampadas Desktop.\n\n' + str(error) +
               '\n\nConfira a instalacao do WebView2 Runtime no Windows 11.\n'
               'https://developer.microsoft.com/microsoft-edge/webview2/')
    print(message, file=sys.stderr)
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, 'BH Lampadas - Erro', 0x10)
        except Exception:
            pass



class ExportacaoTXTDesktop:
    """Salva, mediante confirmacao do usuario, um TXT recebido da rota autenticada.

    A interface JS requisita o pedido usando o cookie de sessao existente; esta
    ponte apenas abre a caixa Salvar como, sem acesso direto ao banco de dados.
    """
    def __init__(self, janela=None):
        self.janela = janela

    def salvar_txt_pedido(self, pedido_id, texto):
        try:
            import webview
            numero = int(pedido_id)
            if not (1 <= numero <= 999999999):
                raise ValueError('Numero de pedido invalido.')
            if not isinstance(texto, str) or not texto.startswith('BH LAMPADAS - PEDIDO DE DEMONSTRACAO'):
                raise ValueError('Conteudo de pedido invalido.')
            if len(texto) > 500000:
                raise ValueError('TXT acima do limite permitido.')
            if not self.janela:
                raise RuntimeError('Janela desktop indisponivel.')
            resultado = self.janela.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename='pedido_{:06d}_teste.txt'.format(numero),
                file_types=('Arquivo de texto (*.txt)',)
            )
            if not resultado:
                return {'status': 'cancelado'}
            caminho = Path(resultado[0])
            if caminho.suffix.lower() != '.txt':
                caminho = caminho.with_suffix('.txt')
            # Mantem a codificacao Windows-1252 e as quebras CRLF do gerador.
            caminho.write_bytes(texto.encode('cp1252', errors='replace'))
            return {'status': 'salvo', 'arquivo': caminho.name}
        except Exception as exc:
            return {'status': 'erro', 'mensagem': str(exc)}

def main():
    prepare_environment()
    # A importacao cria app com banco no LOCALAPPDATA, nunca junto ao codigo.
    from app_modulo2 import create_app
    application = create_app()
    server = worker = sock = None
    try:
        server, worker, sock, url = start_local_server(application)
        import webview
        # Em pywebview o download de arquivos e bloqueado por padrao.
        # Habilitamos a via padrao e a ponte nativa com dialogo Salvar como.
        webview.settings['ALLOW_DOWNLOADS'] = True
        exportador = ExportacaoTXTDesktop()
        janela = webview.create_window('BH Lâmpadas | Desktop (versão experimental)',
                              url, width=1280, height=780, min_size=(900, 560),
                              background_color='#f8fafc', js_api=exportador)
        exportador.janela = janela
        # O WebView2 abre uma janela propria, sem precisar abrir o navegador.
        webview.start(gui='edgechromium', debug=False)
    finally:
        if server is not None:
            server.should_exit = True
        if worker is not None:
            worker.join(timeout=7)
        if sock is not None:
            try: sock.close()
            except OSError: pass


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        report_error(exc)
        raise SystemExit(1)
