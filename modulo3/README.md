# BH Lâmpadas — Projeto Integrador II, Checkout 3

Documentação da etapa **Banco de Dados e Controle de Versão** do protótipo local da BH Lâmpadas.

## Arquivos

- `diagrama_relacional.png`: imagem do diagrama relacional resumido, com fundo quadriculado, que representa do esquema acadêmico existente em `../modulo2/schema.sql` (8 tabelas e 7 relacionamentos FK), com atributos principais.
- `consultas_academicas.sql`: exemplos de SELECT, JOIN, INSERT, UPDATE e DELETE para **um banco de teste**. O trecho demonstrativo usa `ROLLBACK`.
- `validar_banco.py`: cria um SQLite temporário, executa o esquema real do Módulo 2, testa integridade e CRUD, e apaga o banco ao terminar.
- `resultados_validacao.txt`: resultado real da execução local dos oito testes, não é evidência de validação na loja.
- `HISTORICO_VERSIONAMENTO.md`: registros verificados no histórico público do GitHub até 03/11/2026.
- `ROTEIRO_VALIDACAO_TECNICA.md`: orientações para a futura revisão do ex-funcionário que mantém o site.

## Execução

A pasta `modulo3` deve ficar ao lado de `modulo2` no repositório original. No Prompt de Comando, acesse a pasta `modulo3` e execute:

```bat
python validar_banco.py
```

O script usa exclusivamente os módulos padrão do Python. Ele lê `../modulo2/schema.sql`, cria um banco temporário, realiza oito verificações e não modifica a instalação atual nem os cadastros locais.

## Estado do projeto

Não há integração real com o Bling, migração homologada do Space, impressora Epson validada ou sistema desktop pronto. A tabela `pedido` **não existe** no `schema.sql` atual. As tabelas de exportação são estruturas previstas para evolução e **não representam sincronização com o Bling**. Não usar dados reais de clientes neste trabalho acadêmico.

Repositório principal: https://github.com/mizaelkervellyn-alt/bh-lampadas-sistema
