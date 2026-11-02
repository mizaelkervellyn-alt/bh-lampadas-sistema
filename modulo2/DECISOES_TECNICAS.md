# Decisões técnicas — Módulo 2

**Data:** 02/11/2026  
**Projeto:** BH Lâmpadas / UFMS · Projeto Integrador de TI II

## 1. Dar continuidade ao protótipo existente

O projeto já possuía um protótipo web local desenvolvido em Python com SQLite. Em vez de substituir o sistema antigo da loja, o Módulo 2 trabalha em uma **cópia experimental independente**, preservando a versão de referência e os arquivos `dados_locais` do usuário.

## 2. Escolher FastAPI como framework web

O planejamento do Módulo 1 mencionava Flask como opção, mas não como parte já implementada. Para esta evolução foi escolhido **FastAPI**, framework Python moderno que facilita criar rotas HTTP, validar acessos e fornecer dados para pesquisas assíncronas. A disciplina pede o uso de um framework, mas não determina o Flask como obrigatório. Esta é uma **mudança de escolha tecnológica**, que deve ser relatada honestamente no Checkout 2.

O código antigo do repositório continua separado. Não foi feita uma migração integral de todas as funcionalidades antigas: esta etapa prioriza cadastros, autenticação, busca e interface.

## 3. Preservar SQLite e o esquema de dados inicial

O arquivo `schema.sql` do protótipo anterior foi reaproveitado e os testes criam um banco novo e isolado. Senhas do protótipo anterior continuam verificáveis pelo mesmo algoritmo de hash PBKDF2, caso uma futura migração local e autorizada reutilize o banco. **Nenhum banco do usuário foi copiado para o projeto.**

## 4. Organizar HTML e acessibilidade

As páginas HTML foram separadas em `templates/` e utilizam elementos `<header>`, `<nav>`, `<main>`, `<section>`, `<label>` e cabeçalhos hierárquicos. A interface contém atalho para pular ao conteúdo, foco visível e atualizações de busca anunciadas com `aria-live`.

## 5. Criar estilos responsivos

O CSS utiliza `grid`, `flex` e consultas de mídia (`@media`) em duas larguras; tabelas longas possuem rolagem horizontal e o menu vira uma faixa horizontal nas telas menores. Isso permite demonstrar adaptação ao computador e celular sem prometer que toda a experiência foi homologada em dispositivos reais.

## 6. Busca dinâmica e progressiva

O JavaScript usa `fetch()` para atualizar os resultados de produtos e clientes enquanto o usuário digita; as respostas JSON são convertidas em elementos seguros com `textContent`, evitando inserir HTML vindo dos cadastros. A busca por formulário continua funcionando se o JavaScript estiver desativado.

## 7. Boas práticas e limitações

A nova versão utiliza token CSRF nos formulários, cookies de sessão assinados, senhas protegidas com PBKDF2 e banco SQLite parametrizado. Como aplicativo acadêmico local, ainda exige avaliação de segurança antes de receber dados reais. Não foi implementada autenticação multiusuário com níveis de permissão detalhados nem atualização automática no Bling.

## 8. Testes e GitHub

Foram executados testes automatizados locais para primeiro acesso, autenticação, CSRF, cadastros, edição de produto, pesquisa, exportação CSV, registro de ocorrência e persistência. O código foi preparado para revisão e publicação em branch separada, sem substituir silenciosamente a versão principal do repositório.

## Identidade visual — atualização com logo

A marca fornecida pela BH Lâmpadas foi incorporada como arquivo estático `static/logo_bh_lampadas.png`, sem redesenhar a identidade visual. A imagem aparece no cabeçalho compartilhado (`templates/base.html`) de todas as páginas. A aplicação também utiliza um ícone extraído da imagem original em `static/favicon_bh.png`. O CSS limita a largura da marca em telas pequenas, e os testes verificam a disponibilidade dos arquivos.

## Compatibilidade com Python 3.8.10 — ajuste do iniciador

O instalador em lote foi ajustado para reconhecer os comandos `python` e `py`, criar `.venv` e instalar dependências dentro dele. Os pacotes foram limitados a versões que declaram compatibilidade com Python 3.8. Não foi executado teste real em um Windows com Python 3.8 neste ambiente de desenvolvimento: o usuário deverá executar o iniciador e registrar o resultado. A versão Python 3.8 não é mais mantida e não é indicada para operação comercial.
