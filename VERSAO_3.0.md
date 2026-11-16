# Ctrl Play — Versão 3.0

## Personalização da aparência
- Adicionada página Configurações ao menu principal.
- Adicionada opção de tema claro e escuro.
- Adicionado seletor de cor de destaque personalizada e paleta de cores sugeridas.
- Preferências salvas individualmente por usuário no banco SQLite.
- Criada tabela `configuracao_usuario` sem alterar ou apagar os registros existentes.

## Atualização
Execute `python -m flask --app app init-db` uma vez para criar a nova tabela de preferências. O comando preserva as tabelas e os dados anteriores.
