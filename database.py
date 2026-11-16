import sqlite3
from pathlib import Path


def get_db(database_path):
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(database_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA journal_mode = WAL")
    return db


def init_db(database_path):
    db = get_db(database_path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS configuracao_usuario (
            id_usuario INTEGER PRIMARY KEY,
            tema TEXT NOT NULL DEFAULT 'claro' CHECK (tema IN ('claro', 'escuro')),
            cor_destaque TEXT NOT NULL DEFAULT '#315ee8',
            FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS aluno (
            id_aluno INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER NOT NULL CHECK (idade > 0),
            contato_responsavel TEXT,
            data_cadastro TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ativo'
                CHECK (status IN ('Ativo', 'Inativo'))
        );

        CREATE TABLE IF NOT EXISTS turma (
            id_turma INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_turma TEXT NOT NULL,
            curso TEXT NOT NULL,
            descricao TEXT,
            status TEXT NOT NULL DEFAULT 'Ativa'
                CHECK (status IN ('Ativa', 'Inativa'))
        );

        CREATE TABLE IF NOT EXISTS matricula (
            id_matricula INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER NOT NULL,
            id_turma INTEGER NOT NULL,
            data_matricula TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ativa'
                CHECK (status IN ('Ativa', 'Inativa')),
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno),
            FOREIGN KEY (id_turma) REFERENCES turma(id_turma),
            UNIQUE (id_aluno, id_turma)
        );

        CREATE TABLE IF NOT EXISTS atividade (
            id_atividade INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aluno INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT,
            data_registro TEXT NOT NULL,
            observacao TEXT,
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno)
        );

        CREATE TABLE IF NOT EXISTS aula (
            id_aula INTEGER PRIMARY KEY AUTOINCREMENT,
            id_turma INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            data_aula TEXT NOT NULL,
            hora_inicio TEXT,
            hora_fim TEXT,
            conteudo_previsto TEXT,
            conteudo_ministrado TEXT,
            observacoes TEXT,
            status TEXT NOT NULL DEFAULT 'Planejada'
                CHECK (status IN ('Planejada', 'Realizada', 'Cancelada')),
            FOREIGN KEY (id_turma) REFERENCES turma(id_turma)
        );

        CREATE TABLE IF NOT EXISTS presenca (
            id_presenca INTEGER PRIMARY KEY AUTOINCREMENT,
            id_aula INTEGER NOT NULL,
            id_aluno INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Presente', 'Falta', 'Justificada')),
            observacao TEXT,
            data_registro TEXT NOT NULL,
            FOREIGN KEY (id_aula) REFERENCES aula(id_aula) ON DELETE CASCADE,
            FOREIGN KEY (id_aluno) REFERENCES aluno(id_aluno),
            UNIQUE (id_aula, id_aluno)
        );

        CREATE INDEX IF NOT EXISTS idx_aluno_nome ON aluno(nome);
        CREATE INDEX IF NOT EXISTS idx_atividade_aluno_data
            ON atividade(id_aluno, data_registro);
    """)
    # Migração segura para bancos existentes: adiciona a nota sem apagar registros.
    colunas_atividade = {linha[1] for linha in db.execute("PRAGMA table_info(atividade)")}
    if "nota" not in colunas_atividade:
        db.execute("ALTER TABLE atividade ADD COLUMN nota REAL CHECK (nota IS NULL OR (nota >= 0 AND nota <= 10))")

    db.execute("CREATE INDEX IF NOT EXISTS idx_aula_turma_data ON aula(id_turma, data_aula)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_presenca_aluno ON presenca(id_aluno, status)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_presenca_aula ON presenca(id_aula)")
    db.commit()
    db.close()
