# Sistema de Gerenciamento de Alunos e Turmas — Ctrl Play

MVP acadêmico para organizar cadastros de alunos, turmas, matrículas e atividades.

> **Atenção:** este projeto é uma versão inicial para demonstração acadêmica. Antes de utilizar com dados reais de crianças e adolescentes, é necessário realizar revisão de segurança, privacidade, permissões, política de backup e adequação à LGPD. Utilize somente dados fictícios durante os testes.

## Funcionalidades

- Login de usuário.
- Cadastro, listagem, pesquisa, edição e inativação de alunos.
- Cadastro, listagem, edição e inativação de turmas.
- Matrícula de alunos em turmas, com visualização de alunos por turma, remoção do vínculo e reativação de matrícula sem apagar histórico.
- Registro de atividades por aluno com nota opcional de 0 a 10.
- Cronograma de aulas em calendário mensal interativo, com navegação entre meses, seleção de dia, filtro por turma e consulta dos detalhes de cada aula.
- Consulta do histórico individual.
- Validação de campos no servidor.
- Consultas SQL parametrizadas.
- Senhas armazenadas com hash scrypt por meio do Werkzeug.
- Proteção CSRF simples para formulários POST.
- Interface responsiva e navegação por teclado.

## Tecnologias

- Python 3.12
- Flask 3.x
- SQLite com `sqlite3`
- HTML5, CSS3 e JavaScript
- Jinja2 (integrado ao Flask)

## Requisitos

- Python 3.10 ou superior (recomendado Python 3.12)
- pip

## Instalação no Windows

Abra o terminal na pasta do projeto:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Crie uma chave secreta e configure-a no terminal:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

Inicialize o banco:

```powershell
python -m flask --app app init-db
```

Crie o primeiro usuário administrador:

```powershell
python -m flask --app app create-admin
```

Opcionalmente, insira dados fictícios:

```powershell
python -m flask --app app seed-demo
```

Inicie a aplicação:

```powershell
python -m flask --app app run --debug
```

Acesse `http://127.0.0.1:5000`.

## Instalação no Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python -m flask --app app init-db
python -m flask --app app create-admin
python -m flask --app app seed-demo
python -m flask --app app run --debug
```

## Estrutura

```text
ctrlplay-gerenciamento/
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── templates/
└── static/
```

## Banco de dados

O arquivo SQLite é criado em `database/ctrlplay.db`. É possível alterar o caminho com a variável `DATABASE_PATH`.

Entidades:
- `aula`: cronograma, turma, horários, conteúdo previsto e ministrado, observações e situação.
- `usuario`: credenciais dos usuários autorizados.
- `aluno`: dados básicos dos alunos.
- `turma`: cursos e turmas.
- `matricula`: relacionamento entre alunos e turmas.
- `atividade`: histórico de atividades de cada aluno, com nota opcional de 0 a 10.

O banco impede matrícula duplicada para o mesmo par aluno/turma. A inativação preserva os registros históricos.

## Segurança e limitações

- Não existe usuário/senha padrão. Crie a conta pelo comando `create-admin`.
- Senhas são armazenadas com hash scrypt, não em texto puro.
- As consultas usam parâmetros SQL.
- O sistema inclui token CSRF nos formulários POST.
- Em produção, configure `SECRET_KEY` forte e privada, HTTPS e `COOKIE_SECURE=1`.
- Não execute o servidor de desenvolvimento do Flask em produção. Utilize um servidor WSGI.
- O controle de acesso atual diferencia usuário autenticado de visitante, mas ainda não possui perfis/permissões detalhados.
- A proteção contra tentativas repetidas de login, recuperação de senha, auditoria de ações e política de retenção ainda precisam ser implementadas antes de uso real.
- Ao atualizar uma instalação existente para a versão 2.0, faça uma cópia de segurança do arquivo `database/ctrlplay.db` e execute novamente `python -m flask --app app init-db`. A inicialização adiciona a coluna de nota e a tabela de aulas sem apagar os registros existentes.
- O banco SQLite é adequado ao protótipo. Para muitos usuários escrevendo simultaneamente, avalie PostgreSQL.
- Faça backups consistentes usando a API de backup do SQLite ou com a aplicação parada.

## Testes manuais sugeridos

1. Entrar com usuário válido e inválido.
2. Cadastrar aluno com dados válidos.
3. Tentar cadastrar idade inválida.
4. Editar e inativar aluno.
5. Cadastrar turma.
6. Matricular aluno em turma.
7. Tentar repetir a mesma matrícula.
8. Registrar atividade com nota entre 0 e 10 e consultar o histórico.
9. Matricular aluno, removê-lo da turma e matriculá-lo novamente.
10. Criar, editar, filtrar e excluir aulas no cronograma.
11. Sair e verificar que páginas protegidas solicitam login.
12. Navegar usando somente teclado e ampliar a página.

## Licença e finalidade

Projeto desenvolvido para fins acadêmicos. Os dados de demonstração são fictícios.


## Versão 3.0 — Configurações visuais

A versão 3.0 permite que cada usuário escolha o tema claro ou escuro e personalize a cor de destaque. As preferências são salvas individualmente no banco de dados. Para atualizar um banco existente, execute `python -m flask --app app init-db`.


### Versão 4.0 — Calendário interativo
O cronograma agora apresenta um calendário mensal. Selecione um dia para consultar as aulas cadastradas, use as setas para navegar entre meses ou escolha diretamente o mês e o ano. Os dias com aulas recebem um indicador visual. O filtro por turma e as opções de criar, editar e excluir aulas foram mantidos. Não é necessária migração do banco de dados nesta versão.
