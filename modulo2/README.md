# BH Lâmpadas — Projeto Integrador II · Módulo 2

Evolução acadêmica do protótipo de gestão da BH Lâmpadas, com **FastAPI**, HTML semântico, CSS responsivo, busca dinâmica e banco de dados **SQLite**.

> **Atenção:** esta é uma versão experimental local. Use somente dados fictícios. Não emite NF-e, não sincroniza com o Bling e não substitui o Space em produção. A versão desktop instalada e a impressão real na Epson LQ-1070+ ainda não foram validadas.

## O que foi implementado

- Framework **FastAPI** para organizar rotas e respostas HTTP.
- Templates HTML com **Jinja2**, navegação semântica, formulários com rótulos e mensagens acessíveis.
- **Logo original da BH Lâmpadas** no cabeçalho e ícone da aplicação, com imagem fornecida para o projeto.
- CSS responsivo, layout adaptado a dispositivos menores, menu, tabelas roláveis e botões maiores.
- **Busca dinâmica** de produtos e clientes, por nome/código, com JavaScript; a pesquisa por botão funciona sem JS.
- Cadastro e edição de produtos (categoria, preço, código) e clientes (campos básicos).
- Login e acesso inicial por senha, com hash PBKDF2 compatível com o cadastro do protótipo anterior.
- Exportação CSV e demonstração de registro de ocorrência de privacidade.
- Testes automatizados das principais funcionalidades e persistência no SQLite.

## Como executar no Windows (incluindo Python 3.8.10)

1. Extraia **todo o ZIP** em uma pasta diferente do protótipo antigo.
2. Abra a pasta `modulo2` e dê **dois cliques** em `INICIAR_MODULO2_WINDOWS.bat`.
3. Na **primeira execução**, mantenha a Internet conectada: o iniciador cria `.venv/` e instala as bibliotecas exigidas em um ambiente separado, sem afetar o protótipo anterior.
4. Quando aparecer `Iniciando sistema em http://127.0.0.1:8766`, abra o navegador no endereço **http://127.0.0.1:8766**.
5. Cadastre uma senha própria no primeiro acesso e use **dados fictícios**.
6. Para encerrar, pressione `Ctrl+C` na janela do iniciador.

O pacote também aceita o comando `python` quando o iniciador `py` do Windows não está instalado.

**Importante:** o Python 3.8 chegou ao fim do suporte em 2024. As dependências deste pacote foram fixadas em versões que declaram compatibilidade com o Python 3.8.10, para permitir os testes acadêmicos. Isso não significa que a nova versão já tenha sido validada no seu computador ou que seja adequada para uso com dados reais. Para desenvolvimento futuro, prefira um Python suportado (por exemplo, Python 3.11/3.12) em um Windows atualizado.

### Se a instalação automática falhar

Abra o Prompt de Comando **dentro da pasta `modulo2`** e execute:

```bat
python -m pip install -r requirements.txt
python -m uvicorn app_modulo2:app --host 127.0.0.1 --port 8766
```

Se o erro mencionar a pasta `.venv`, você pode renomeá-la para `.venv_antiga` e executar o iniciador novamente. Não mexa na pasta `dados_locais`, que guarda seu banco de testes.

### Testes automatizados

Execute dentro da pasta `modulo2`:

```bat
.venv\Scripts\python.exe -m pytest -q
```

Os testes utilizam um diretório temporário e não devem alterar os cadastros locais.

## Organização do código

| Pasta/arquivo | Função |
| --- | --- |
| `app_modulo2.py` | Rotas, autenticação, regras e consultas SQL |
| `templates/` | Páginas HTML com elementos semânticos |
| `static/modulo2.css` | Estilização responsiva |
| `static/modulo2.js` | Busca dinâmica sem recarregar a página |
| `static/logo_bh_lampadas.png` | Logo da loja no cabeçalho |
| `static/favicon_bh.png` | Ícone da aba do navegador |
| `schema.sql` | Estrutura das tabelas SQLite |
| `tests/` | Testes automatizados |
| `INICIAR_MODULO2_WINDOWS.bat` | Inicia no Windows, após instalar as dependências |
| `.gitignore` | Protege arquivos de banco local, segredos e arquivos temporários |

## Segurança e dados

Não publique `dados_locais/`, arquivos `.sqlite3`, `.db` ou `.segredo_sessao*`. A senha criada no primeiro acesso é armazenada como hash PBKDF2; o segredo de sessão é gerado automaticamente e guardado localmente. A execução está restrita a `127.0.0.1` quando iniciada pelos comandos recomendados.

**Não copie o banco SQLite real da loja para o GitHub.** Para avaliação acadêmica, use dados de demonstração. A migração real do Space exigirá validações e cópias de segurança.

## Limites e próximos passos

O código do Módulo 2 **não implementa ainda** o fluxo completo de pedidos, estoque, impressão matricial ou integração fiscal com Bling. A versão anterior publicada no GitHub deve ser mantida como referência até a revisão desta evolução. Em etapas futuras, testar novos módulos, importações reais, funcionamento multiusuário e embalagem em programa desktop para Windows.

## Registro do desenvolvimento

Veja `DECISOES_TECNICAS.md` e `RELATORIO_MODULO2_RASCUNHO.md` para os critérios de escolha do framework, mudanças no protótipo, testes e espaços reservados para capturas de tela.
