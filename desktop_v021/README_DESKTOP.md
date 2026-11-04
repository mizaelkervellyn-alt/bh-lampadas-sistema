# BH Lâmpadas — Desktop experimental v0.2.1

A aplicação local usa **FastAPI + SQLite + pywebview (Edge WebView2)**, abrindo em janela própria no Windows 11. Reaproveita as telas, banco e a logo da versão anterior.

## O que foi adicionado

- **Pedidos:** criação de pedidos com até seis produtos, quantidades, captura do preço registrado, total automático e histórico de pedidos.
- **Impressão de pedido:** botão **Imprimir** em uma página monoespaçada; chama a caixa de impressão do navegador embutido via `window.print()`. Alternativa: salvar **TXT Windows-1252 com CRLF**, apropriado para avaliar impressão simples em papel contínuo.
- **Contas a receber:** cobrança gerada automaticamente para pedidos a prazo ou cadastrada manualmente; vencimento, saldo, status e recebimentos parciais.
- **Inadimplência:** cliente é destacado quando há cobrança *vencida e com saldo pendente*. Após quitar a cobrança, deixa de aparecer como vencido.
- **Migração aditiva:** cria quatro novas tabelas sem apagar cadastros, produtos e informações anteriores. Antes da primeira migração faz backup do SQLite em `dados_locais/backups/`.

## Como abrir

1. Feche a v0.1. Extraia todo o ZIP.
2. Dê dois cliques em `INICIAR_DESKTOP_WINDOWS.bat` e instale as dependências, se solicitado (internet na primeira execução).
3. Faça login com o acesso já criado na v0.1. O banco compartilhado fica em `%LOCALAPPDATA%\BH_Lampadas_Desktop_Experimental\dados_locais`.
4. Faça os testes com dados fictícios. A pasta do código não inclui nenhuma senha nem banco de clientes.

## Como testar o novo fluxo

1. Cadastre cliente e produto (preço positivo).
2. Em **Pedidos > Novo pedido**, escolha cliente, produto, quantidade e pagamento. Se **a prazo**, informe vencimento.
3. Na lista de pedidos, abra **Detalhes > Imprimir pedido**; teste o botão **Imprimir (Ctrl+P)**. Alternativamente, salve o TXT com a caixa de diálogo do Windows.
4. Em **Contas a receber**, confira a cobrança. Para simular atraso, registre uma cobrança fictícia com vencimento anterior à data atual.
5. Registre um recebimento (parcial ou integral). O status e o alerta na lista de clientes refletem o saldo e o vencimento.
6. Rode o conjunto de testes: `python -m pytest -q modulo2/tests testes_desktop.py testes_fluxos_v02.py testes_download_v021.py` após instalar dependências.

**Limites:** não há baixa real de estoque, venda fiscal, geração de NF-e, conexão com Bling, importação real do Space, parcelamento com múltiplas datas nem integração bancária. O TXT é apenas para avaliação da impressora matricial Epson LQ-1070+; corte automático e comandos ESC/P não foram homologados. Os dados de teste são locais, não uma migração da loja.

## Segurança e implantação

A aplicação é vinculada à interface local 127.0.0.1 e usa sessão com senha hash e CSRF nas rotas que alteram dados. O `.exe` é gerado *no Windows* com `CRIAR_EXE_WINDOWS.bat`, e precisa ser testado no Windows real. Evite executar simultaneamente duas versões antigas apontando ao mesmo banco. Mantenha cópias de segurança antes de novas atualizações.


## Correção v0.2.1 — Salvar TXT na janela desktop

Uma falha foi encontrada nos testes manuais no Windows 11: clicar no botão
"Baixar TXT" não iniciava o download na janela pywebview. Isso acontecia
porque o pywebview desabilita downloads por padrão. A versão v0.2.1 habilita
`ALLOW_DOWNLOADS` e adiciona um botão com diálogo **Salvar como** do próprio
Windows, que usa a sessão autenticada para buscar o pedido. O TXT é salvo em
Windows-1252 com quebras de linha CRLF, para facilitar testes da Epson LQ-1070+.

**Teste manual no Windows:** feche a versão anterior, extraia a v0.2.1 em outra
pasta, execute `INICIAR_DESKTOP_WINDOWS.bat`, abra um pedido e clique em
**Salvar TXT para testar na matricial**. Escolha a pasta de destino e verifique
que um arquivo `pedido_000001_teste.txt` foi salvo. Também teste a opção
"Salvar pedido TXT" na tela de detalhes. O aplicativo reutiliza o mesmo banco
de testes em `%LOCALAPPDATA%\BH_Lampadas_Desktop_Experimental\dados_locais`, sem
apagar os pedidos e recebimentos anteriores.

**Situação atual:** o diálogo nativo e o salvamento TXT foram confirmados pelo estudante em 04/11/2026 no Windows. Os testes automatizados também validam a geração TXT, o fluxo HTTP e a lógica de gravação simulada. Não há homologação da impressora física, do corte de papel ou de ESC/P.

## Testes manuais confirmados no Windows (04/11/2026)

O estudante confirmou a abertura do aplicativo, criação de pedido a prazo de R$ 51,80, cobrança vencida, pagamento parcial de R$ 20,00, quitação de R$ 31,80, prévia e janela de impressão do Windows. Após a correção do botão de TXT na v0.2.1, confirmou o salvamento do arquivo `pedido_000001_teste.txt`. Evidências e relatório de teste estão em `../modulo4/`.

**Ainda não testado:** impressão física na Epson LQ-1070+, corte, uso real na loja e aprovação do profissional indicado.
