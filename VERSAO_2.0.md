# Ctrl Play — Versão 2.0

## Novidades

- Detalhe de turma com lista de alunos matriculados.
- Matrícula de aluno diretamente na página da turma.
- Remoção de matrícula sem excluir aluno ou histórico.
- Reativação de matrícula anteriormente inativada.
- Nota opcional de 0 a 10 nas atividades, com validação no servidor e no formulário.
- Nota exibida na listagem de atividades e no histórico individual.
- Cronograma com cadastro, edição, filtro por turma e exclusão de aulas.
- Registro de data, horários, conteúdo previsto, conteúdo ministrado, observações e situação da aula.
- Migração aditiva do SQLite: a coluna `atividade.nota` e a tabela `aula` são criadas sem apagar registros existentes.

## Atualização do banco existente

1. Faça backup de `database/ctrlplay.db` com a aplicação parada.
2. Ative o ambiente virtual.
3. Execute `python -m flask --app app init-db`.
4. Inicie com `python -m flask --app app run --debug`.

A migração não apaga as tabelas ou registros existentes. Ainda assim, mantenha o backup.

## Limites

Esta versão continua sendo um protótipo acadêmico. Use dados fictícios nos testes. Antes de uso real, é necessária revisão de segurança, privacidade, permissões e adequação à LGPD.
