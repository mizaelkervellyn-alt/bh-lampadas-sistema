
# BH Lâmpadas | Sistema de Gestão

Protótipo desenvolvido para o Projeto Integrador de Tecnologia da Informação da Universidade Federal de Mato Grosso do Sul (UFMS).

## Sobre o projeto

O projeto busca desenvolver um sistema de gestão para a BH Lâmpadas, uma loja de Belo Horizonte que utiliza o Space Informática para controlar produtos, clientes e vendas.

A proposta surgiu da necessidade de modernizar esse processo, reduzir o retrabalho causado pelo uso de sistemas diferentes e facilitar as atividades diárias da responsável pela loja.

O sistema ainda é um protótipo web local, mas a intenção é desenvolver uma versão final que possa ser instalada no computador da empresa.

## Funcionalidades disponíveis

O protótipo permite cadastrar, editar e pesquisar produtos e clientes, organizar produtos por categorias e identificar preços zerados ou não informados.

Também permite exportar informações em CSV, realizar a leitura experimental de arquivos TXT do Space, registrar ocorrências relacionadas à privacidade e gerar cópias de segurança.

O acesso é protegido por usuário e senha, e as informações são armazenadas localmente.

## Tecnologias utilizadas

Python para desenvolver as funcionalidades do sistema.

HTML e CSS para a estrutura e aparência da interface.

SQLite para armazenar as informações em um banco de dados local.

O protótipo utiliza recursos nativos do Python, sem depender de frameworks externos.

## Como executar

É necessário ter Python 3.8 ou superior instalado.

Primeiro, baixe o repositório pela opção Code > Download ZIP e extraia os arquivos.

Depois, abra a pasta do projeto e execute o arquivo INICIAR_WINDOWS.bat.

No navegador, acesse:

http://127.0.0.1:8765

No primeiro acesso, crie a conta de administrador e uma senha com pelo menos 10 caracteres.

Nos próximos acessos, utilize o usuário admin e a senha cadastrada.

Também é possível iniciar o programa pelo terminal com o comando:

`python app.py`

## Testes

O projeto possui testes automatizados para verificar funcionalidades como login, cadastros, exportação de arquivos e armazenamento de informações.

Para executar os testes, utilize:

`python testes_automaticos.py`

Os testes utilizam dados fictícios e não alteram o banco de dados principal do usuário.

## Segurança e privacidade

O programa armazena os dados localmente na pasta dados_locais, que não deve ser publicada no GitHub.

O protótipo deve ser utilizado com dados fictícios, pois ainda não passou pelas validações necessárias para operar com informações reais da empresa.

## Próximas etapas

Durante o Projeto Integrador II, a proposta é melhorar a interface, ampliar as funcionalidades de pedidos e desenvolver novos recursos para facilitar o trabalho da loja.

Também será necessário testar a impressão dos pedidos na impressora matricial, avaliar a migração dos dados do Space e verificar a compatibilidade dos arquivos exportados com o Bling.

O objetivo futuro é disponibilizar um sistema instalado no computador da empresa, sem depender da abertura manual pelo navegador.

## Situação atual

O projeto está em desenvolvimento e ainda não substitui o Space Informática nem o Bling.

O protótipo não emite notas fiscais e não realiza sincronização automática entre os sistemas.

As próximas melhorias serão desenvolvidas e testadas conforme as necessidades identificadas na BH Lâmpadas.
