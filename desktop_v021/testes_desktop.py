"""Testes isolados que nao abrem a GUI. Executar: python -m unittest -v testes_desktop.py"""
import os
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

import desktop


class TestDesktop(unittest.TestCase):
    def test_recursos(self):
        root = desktop.resource_dir()
        for p in ['app_modulo2.py','schema.sql','static/logo_bh_lampadas.png','templates/base.html']:
            self.assertTrue((root / p).is_file(), p)

    def test_dados_separados(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {'LOCALAPPDATA': root}):
                data = desktop.user_data_dir()
                self.assertTrue(str(data).startswith(str(root)))
                self.assertNotEqual(data, desktop.resource_dir() / 'dados_locais')

    def test_servidor_local_e_parada(self):
        from fastapi import FastAPI
        app = FastAPI()
        @app.get('/saude')
        def health(): return {'status': 'ok'}
        server, worker, sock, url = desktop.start_local_server(app)
        try:
            self.assertTrue(url.startswith('http://127.0.0.1:'))
            with urllib.request.urlopen(url + '/saude', timeout=3) as reply:
                self.assertEqual(reply.status, 200)
                self.assertIn(b'ok', reply.read())
        finally:
            server.should_exit = True
            worker.join(timeout=7)
            sock.close()
            self.assertFalse(worker.is_alive())

    def test_fluxo_app_em_base_temporaria(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {'LOCALAPPDATA': td}):
                _, data = desktop.prepare_environment()
                from app_modulo2 import create_app
                from fastapi.testclient import TestClient
                with TestClient(create_app(data), base_url='http://testserver') as client:
                    resp = client.get('/', follow_redirects=True)
                    self.assertEqual(resp.status_code, 200)
                    self.assertIn('Configurar acesso inicial', resp.text)
                    self.assertEqual(client.get('/static/logo_bh_lampadas.png').status_code, 200)
                self.assertTrue((data / 'cadastros.sqlite3').exists())

if __name__ == '__main__':
    unittest.main()
