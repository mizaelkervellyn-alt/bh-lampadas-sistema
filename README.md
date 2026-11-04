

# BH Lâmpadas | Sistema de Gestão

Sistema de gestão desenvolvido para a BH Lâmpadas, como parte do Projeto Integrador de Tecnologia da Informação da Universidade Federal de Mato Grosso do Sul (UFMS).

## Sobre o projeto

O projeto surgiu da necessidade de modernizar os processos da BH Lâmpadas, uma loja de Belo Horizonte que utiliza o Space Informática para gerenciar produtos, clientes e vendas, enquanto o Bling é utilizado para emitir notas fiscais.

A proposta é desenvolver uma solução mais prática para a rotina da loja, reduzindo tarefas repetitivas e facilitando a organização das informações.

Inicialmente, foi desenvolvido um protótipo web local. Durante o Projeto Integrador II, o sistema evoluiu com a utilização de um framework, melhorias na interface, organização do banco de dados e criação de uma versão desktop experimental.

Atualmente, o projeto está na versão desktop **v0.2.1**, que já foi executada e testada no Windows 11, mas ainda não está pronta para substituir os sistemas utilizados pela empresa.

## Funcionalidades desenvolvidas

O sistema permite cadastrar, editar e pesquisar clientes e produtos, organizar produtos por categorias, controlar preços e exportar informações em CSV.

Na versão desktop, foram acrescentadas novas funcionalidades:

- Registro e consulta de pedidos de venda.
- Cálculo automático dos valores dos pedidos.
- Visualização e impressão de pedidos pelo Windows.
- Exportação de pedidos em TXT para testes com impressora matricial.
- Controle de contas a receber.
- Identificação de clientes com cobranças vencidas.
- Registro de pagamentos parciais e integrais.
- Atualização dos saldos de cobranças.
- Armazenamento local das informações em SQLite.

O sistema também possui autenticação por senha e recursos acadêmicos relacionados à proteção de dados.

## Tecnologias utilizadas

**Python:** desenvolvimento das funcionalidades e regras do sistema.

**FastAPI:** framework utilizado para organizar a aplicação.

**HTML, CSS e JavaScript:** estruturação, estilização responsiva e recursos dinâmicos da interface.

**SQLite:** armazenamento local dos dados.

**Jinja2:** organização das páginas HTML.

**pywebview:** apresentação da aplicação em uma janela própria no Windows.

**Git e GitHub:** controle de versões e documentação do desenvolvimento.

O protótipo inicial utilizava recursos nativos do Python, enquanto as versões posteriores incorporaram frameworks e novas funcionalidades.

## Organização do repositório

O repositório preserva as diferentes etapas do desenvolvimento.

### Protótipo inicial

Arquivos da primeira versão, disponíveis na estrutura principal do repositório.

### Módulo 2

Aplicação web desenvolvida com FastAPI, HTML, CSS, JavaScript e SQLite.

Pasta: `modulo2/`

### Módulo 3

Modelagem do banco de dados, operações SQL e testes de integridade.

Pasta: `modulo3/`

### Desktop experimental v0.2.1

Versão desktop com pedidos, impressão e contas a receber.

Pasta: `desktop_v021/`

### Módulo 4

Testes e garantia de qualidade, com resultados automatizados e evidências do funcionamento no Windows.

Pasta: `modulo4/`

Essa organização permite acompanhar a evolução do projeto sem perder os trabalhos anteriores.

## Como executar a versão desktop

Para executar a versão experimental, é necessário ter o Python e as dependências do projeto instalados.

1. Baixe o repositório pela opção **Code > Download ZIP**.
2. Extraia os arquivos no computador.
3. Abra a pasta `desktop_v021`.
4. Execute o arquivo `INICIAR_DESKTOP_WINDOWS.bat`.
5. Aguarde a preparação do ambiente na primeira execução.
6. O sistema deverá abrir em uma janela própria no Windows.

A versão atual ainda depende de um ambiente Python. A geração e os testes de um executável independente e de um instalador serão realizados posteriormente.

O protótipo inicial continua disponível por meio do arquivo `INICIAR_WINDOWS.bat`, localizado na pasta principal.

## Testes e garantia de qualidade

Durante o Módulo 4, foram realizados testes automatizados e manuais para avaliar o funcionamento e a confiabilidade do sistema.

A bateria automatizada da versão desktop v0.2.1 apresentou **14 testes aprovados e nenhuma falha**, no ambiente de desenvolvimento.

Também foram realizados testes manuais no Windows 11, utilizando dados fictícios.

### Testes manuais realizados

- Cadastro de produtos e clientes.
- Criação de pedido a prazo.
- Identificação de cobrança vencida.
- Registro de pagamento parcial.
- Quitação da cobrança.
- Atualização do alerta de inadimplência.
- Visualização do pedido para impressão.
- Abertura da caixa de impressão do Windows.
- Salvamento do pedido em formato TXT.

### Correção identificada durante os testes

Durante a validação manual, foi identificada uma falha no download do arquivo TXT na versão v0.2.

O problema foi corrigido na versão v0.2.1, com a implementação de uma opção de salvamento pelo próprio Windows.

Após a correção, o arquivo TXT foi gerado e salvo corretamente.

As evidências dos testes estão disponíveis na pasta `modulo4/`.

## Segurança e privacidade

O sistema utiliza armazenamento local, autenticação por senha e mecanismos de proteção de formulários.

Os testes acadêmicos são realizados com informações fictícias.

Bancos de dados locais, senhas, arquivos de sessão e informações reais de clientes não devem ser publicados no GitHub.

A aplicação ainda precisa passar por avaliações adicionais antes de ser utilizada com dados reais da empresa.

## Situação atual

A versão desktop experimental v0.2.1 já permite demonstrar funcionalidades de cadastro, pedidos, impressão e contas a receber.

Entretanto, o sistema ainda não substitui o Space Informática ou o Bling.

A aplicação não emite notas fiscais, não realiza sincronização automática com esses programas e ainda não foi implantada na loja.

A impressão pelo Windows e o salvamento de pedidos em TXT foram testados, mas a impressão física na Epson LQ-1070+ ainda precisa ser validada.

## Próximas etapas

As próximas etapas do desenvolvimento incluem:

- Avaliação técnica pelo profissional indicado pela responsável da loja.
- Apresentação e validação das funcionalidades com a proprietária.
- Teste físico da impressão na Epson LQ-1070+.
- Verificação de compatibilidade da impressora com Windows 11.
- Avaliação da migração segura dos dados do Space.
- Estudo da integração com o Bling.
- Melhorias de interface, desempenho e segurança.
- Criação e validação de um executável e instalador para Windows.

O objetivo é continuar aperfeiçoando a aplicação até que seja possível avaliar sua utilização na empresa de forma segura, sem comprometer as operações existentes.

## Código e documentação

**Versão desktop experimental:**

[desktop_v021](desktop_v021/)

**Testes e evidências do Módulo 4:**

[modulo4](modulo4/)

**Modelagem e validação do banco de dados:**

[modulo3](modulo3/)

**Aplicação web do Módulo 2:**

[modulo2](modulo2/)

## Status do projeto

**Versão atual:** Desktop experimental v0.2.1.

**Testes:** 14 testes automatizados aprovados e testes manuais realizados no Windows 11.

**Situação:** desenvolvimento acadêmico em andamento, com validação operacional na empresa ainda pendente.

