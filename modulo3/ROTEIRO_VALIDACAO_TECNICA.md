# Roteiro de avaliação técnica — BH Lâmpadas

**Situação:** avaliação solicitada pela responsável da loja ao antigo funcionário que hoje mantém o site. Este roteiro descreve uma proposta de envio e avaliação, **não comprova que a avaliação já tenha acontecido**.

## Material para enviar

Link público: https://github.com/mizaelkervellyn-alt/bh-lampadas-sistema/tree/main/modulo2

Enviar apenas o código e a documentação ou uma cópia limpa do pacote. **Não enviar** `dados_locais/`, `.sqlite3`, `.segredo_sessao*`, arquivos `.env`, CPF de clientes, registros reais ou senhas. Primeiro, a responsável deve autorizar o compartilhamento do material com o avaliador.

## Conferência sugerida (com dados inteiramente fictícios)

1. Verificar se a aplicação inicia no Windows de teste e se o README permite reproduzir a instalação.
2. Testar login, inclusão, pesquisa e edição de clientes e produtos, exportação CSV e alertas de preço.
3. Conferir se o esquema SQLite é adequado aos dados que a loja precisa preservar e se há campos importantes ausentes.
4. Avaliar como importar dados de produtos e clientes do Space, sem modificar a instalação utilizada pela empresa.
5. Identificar a estrutura de arquivos, autenticação e permissões que seriam necessárias para integração futura com o Bling; **não alegar integração existente**.
6. Levantar requisitos de impressão para a Epson LQ-1070+, incluindo driver, papel contínuo, comandos de impressão e modelo de pedido. **Esta versão ainda não imprime fisicamente na Epson.**
7. Recomendar backups, testes de recuperação, controle de acesso e cuidados de segurança antes de qualquer uso com dados reais.

## Retorno solicitado

Registrar data, ambiente de testes, funcionalidades conferidas, erros encontrados, recomendações, classificação de prioridade e autorização ou não para uma nova etapa de testes. O aval técnico **não autoriza por si só** substituir o sistema antigo: essa decisão depende da loja e de uma migração planejada e reversível.
