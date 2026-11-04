# BH Lâmpadas — Checkout 4: Testes e Garantia de Qualidade

Esta pasta documenta a validação acadêmica da **versão desktop experimental v0.2.1**, desenvolvida com FastAPI, SQLite e pywebview. O código-fonte completo está em `../desktop_v021/`.

## Evidências registradas no Windows (04/11/2026)

Foram testados com dados inteiramente fictícios: cadastro de produto e cliente, pedido a prazo de R$ 51,80, alerta de vencimento, pagamento parcial de R$ 20,00 (saldo R$ 31,80), quitação (saldo zero), visualização e caixa de impressão do Windows e salvamento de TXT. Imagens de cada etapa ficam em `evidencias/`. O identificador local de login foi ocultado nas capturas destinadas à publicação.

**Defeito encontrado:** na v0.2 o botão de baixar TXT não gerava arquivo dentro da janela pywebview; o comportamento foi corrigido na v0.2.1. O arquivo `evidencias/pedido_000001_teste.txt` foi salvo no Windows e enviado pelo estudante como confirmação.

**Testes automatizados:** 14 aprovados, 0 falhas e 2 avisos de bibliotecas no ambiente de desenvolvimento (ver `resultados_automatizados_v021.txt`).

**Pendente:** impressão física e corte na Epson LQ-1070+, driver/conexão no Windows 11, testes multiusuário, instalação por `.exe`, revisão técnica indicada pela proprietária, integração com Bling e migração real do Space. Nenhuma dessas tarefas foi homologada ou implantada.

**Privacidade:** não publicar `dados_locais/`, arquivos `.sqlite3`, credenciais, ou dados reais de clientes.
