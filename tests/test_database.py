
import sqlite3
import database


def test_get_db_cria_conexao_e_pasta(tmp_path):
    caminho = tmp_path / "dados" / "teste.db"

    db = database.get_db(caminho)

    assert caminho.exists()
    assert db.row_factory == sqlite3.Row
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"

    db.close()


def test_init_db_cria_tabelas(tmp_path):
    caminho = tmp_path / "teste.db"

    database.init_db(caminho)

    db = sqlite3.connect(caminho)

    tabelas = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table'
    """).fetchall()

    nomes = [tabela[0] for tabela in tabelas]

    assert "usuario" in nomes
    assert "aluno" in nomes
    assert "turma" in nomes
    assert "matricula" in nomes
    assert "atividade" in nomes
    assert "aula" in nomes
    assert "presenca" in nomes

    db.close()


def test_migracao_adiciona_coluna_nota(tmp_path):
    caminho = tmp_path / "antigo.db"

    db = sqlite3.connect(caminho)

    db.execute("""
        CREATE TABLE atividade (
            id_atividade INTEGER PRIMARY KEY,
            id_aluno INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT,
            data_registro TEXT NOT NULL,
            observacao TEXT
        )
    """)

    db.commit()
    db.close()

    database.init_db(caminho)

    db = sqlite3.connect(caminho)

    colunas = db.execute(
        "PRAGMA table_info(atividade)"
    ).fetchall()

    nomes = [coluna[1] for coluna in colunas]

    assert "nota" in nomes

    db.close()


def test_init_db_pode_ser_executado_mais_de_uma_vez(tmp_path):
    caminho = tmp_path / "teste.db"

    database.init_db(caminho)
    database.init_db(caminho)

    db = sqlite3.connect(caminho)

    tabelas = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table'
    """).fetchall()

    assert len(tabelas) > 0

    db.close()
