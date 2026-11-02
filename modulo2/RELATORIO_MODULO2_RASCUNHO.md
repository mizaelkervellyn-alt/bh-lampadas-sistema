# Subsídios para o relatório — Checkout / Módulo 2

## Tema
Continuidade do desenvolvimento do sistema de gestão da BH Lâmpadas, com framework, páginas HTML e CSS responsivo.

## Tecnologias efetivamente utilizadas
Python, **FastAPI** (framework de rotas e lógica no servidor), Jinja2 (templates HTML), HTML5, CSS3, JavaScript (busca dinâmica) e SQLite. O **Flask não foi utilizado nesta etapa**: ele aparecia no Módulo 1 como uma possibilidade, e a mudança para FastAPI precisa ser descrita como uma decisão atual.

## Planejamento
O protótipo anterior já oferecia funções de cadastro e exportação. Para atender ao Módulo 2, optou-se por manter o armazenamento local e reorganizar as funcionalidades prioritárias em um framework Python, separando páginas HTML, folha de estilos e JavaScript.

## Implementação
Foram criados templates HTML para login, painel, produtos, clientes e registro de ocorrência; CSS para estilos responsivos; rotas FastAPI para consultas, formulários, login e exportação; busca dinâmica com atualização sem recarregar a página. Utilizou-se o mesmo esquema acadêmico de banco SQLite.

## Resultados observados
Em ambiente de desenvolvimento, os testes automatizados da nova versão passaram para cadastro inicial, login, validação de formulário, inserção e edição de produto, pesquisa por nome/código, clientes, registro de ocorrência, exportação e persistência do banco. Esses testes **não** equivalem à validação na loja, à impressão física ou ao uso operacional.

## Limitações e próximos passos
A versão do Módulo 2 é uma evolução experimental independente. Os módulos de pedidos, impressora Epson LQ-1070+, migração do Space e integração com Bling ainda não foram homologados. A futura versão instalada no Windows exige estudos específicos de distribuição e compatibilidade.

## Publicação no GitHub
Repositório existente: https://github.com/mizaelkervellyn-alt/bh-lampadas-sistema

**[Após publicar esta evolução, colocar aqui o link da branch ou do pull request correspondente.]**

## Evidências

**Figura 1:** [Inserir captura da tela inicial do Módulo 2]  
**Figura 2:** [Inserir captura de pesquisa dinâmica de produtos]  
**Figura 3:** [Inserir captura do GitHub com a nova versão]  
**Fonte:** elaboração própria (2026).

## Conclusão proposta
Nesta etapa, consegui organizar melhor a base do protótipo da BH Lâmpadas e experimentar um framework para desenvolver as páginas e funcionalidades. A mudança facilitou separar o código da interface e acrescentar uma pesquisa que responde enquanto o usuário digita. Ainda preciso testar a aplicação com a responsável, melhorar os módulos de pedidos e conferir a impressão. O trabalho me ajudou a entender melhor como transformar um protótipo em um projeto mais organizado, mantendo os cuidados com os dados e com a rotina da loja.
