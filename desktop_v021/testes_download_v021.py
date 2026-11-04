# -*- coding: utf-8 -*-
"""Valida a ponte de salvamento desktop sem abrir a janela do Windows."""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import desktop


def test_dialogo_nativo_salva_txt_e_preserva_crlf():
    with tempfile.TemporaryDirectory(prefix='bh_teste_txt_') as d:
        destino = Path(d) / 'pedido_000001_teste.txt'
        dialogo = SimpleNamespace(create_file_dialog=lambda *a, **k: (str(destino),))
        api = desktop.ExportacaoTXTDesktop(dialogo)
        txt = 'BH LAMPADAS - PEDIDO DE DEMONSTRACAO\r\nPEDIDO: 000001\r\nCLIENTE: Joao Sao\r\n'
        with patch.dict(sys.modules, {'webview': SimpleNamespace(SAVE_DIALOG=20)}):
            resposta = api.salvar_txt_pedido(1, txt)
        assert resposta == {'status': 'salvo', 'arquivo': destino.name}
        assert destino.read_bytes() == txt.encode('cp1252')


def test_cancelamento_nao_cria_arquivo():
    dialogo = SimpleNamespace(create_file_dialog=lambda *a, **k: None)
    api = desktop.ExportacaoTXTDesktop(dialogo)
    with patch.dict(sys.modules, {'webview': SimpleNamespace(SAVE_DIALOG=20)}):
        resposta = api.salvar_txt_pedido(3, 'BH LAMPADAS - PEDIDO DE DEMONSTRACAO\r\n')
    assert resposta['status'] == 'cancelado'


def test_conteudo_invalido_rejeitado_sem_dialogo():
    dialogo = SimpleNamespace(create_file_dialog=lambda *a, **k: (_ for _ in ()).throw(AssertionError('nao deveria abrir')))
    api = desktop.ExportacaoTXTDesktop(dialogo)
    with patch.dict(sys.modules, {'webview': SimpleNamespace(SAVE_DIALOG=20)}):
        resposta = api.salvar_txt_pedido(2, 'texto arbitrario')
    assert resposta['status'] == 'erro'


def test_interface_inclui_salvamento_em_ambas_telas():
    base = Path(__file__).resolve().parent / 'modulo2'
    for nome in ['pedido_detalhe.html', 'pedido_impressao.html']:
        conteudo = (base / 'templates' / nome).read_text(encoding='utf-8')
        assert 'data-pedido-id="{{ pedido.id }}"' in conteudo
        assert '/static/salvar_txt_desktop.js' in conteudo
    assert "webview.settings['ALLOW_DOWNLOADS'] = True" in (Path(__file__).resolve().parent / 'desktop.py').read_text(encoding='utf-8')
