import os
import secrets
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, g, redirect, render_template, request,
    session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_db

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "ctrlplay.db"))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-publicar"),
    DATABASE=DB_PATH,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
)


@app.before_request
def prepare_request():
    g.db = get_db(app.config["DATABASE"])
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def csrf_protect():
    token = request.form.get("csrf_token", "")
    if not secrets.compare_digest(token, session.get("csrf_token", "")):
        abort(400, description="Token de segurança inválido. Atualize a página e tente novamente.")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para acessar o sistema.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.context_processor
def inject_globals():
    return {"today": date.today().isoformat()}


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        csrf_protect()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = g.db.execute(
            "SELECT id_usuario, nome, senha_hash FROM usuario WHERE usuario = ?",
            (username,)
        ).fetchone()
        if user and check_password_hash(user["senha_hash"], password):
            session.clear()
            session["user_id"] = user["id_usuario"]
            session["user_name"] = user["nome"]
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            flash("Login realizado com sucesso.", "success")
            return redirect(url_for("index"))
        flash("Usuário ou senha inválidos.", "danger")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    csrf_protect()
    session.clear()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    totals = {
        "alunos": g.db.execute("SELECT COUNT(*) FROM aluno WHERE status = 'Ativo'").fetchone()[0],
        "turmas": g.db.execute("SELECT COUNT(*) FROM turma WHERE status = 'Ativa'").fetchone()[0],
        "atividades": g.db.execute("SELECT COUNT(*) FROM atividade").fetchone()[0],
    }
    recent = g.db.execute("""
        SELECT a.id_aluno, a.nome, a.data_cadastro
        FROM aluno a ORDER BY a.id_aluno DESC LIMIT 5
    """).fetchall()
    return render_template("index.html", totals=totals, recent=recent)


@app.route("/alunos")
@login_required
def alunos():
    termo = request.args.get("q", "").strip()
    if termo:
        registros = g.db.execute("""
            SELECT a.*, GROUP_CONCAT(t.nome_turma, ', ') AS turmas
            FROM aluno a
            LEFT JOIN matricula m ON m.id_aluno = a.id_aluno AND m.status = 'Ativa'
            LEFT JOIN turma t ON t.id_turma = m.id_turma
            WHERE a.nome LIKE ?
            GROUP BY a.id_aluno
            ORDER BY a.nome
        """, (f"%{termo}%",)).fetchall()
    else:
        registros = g.db.execute("""
            SELECT a.*, GROUP_CONCAT(t.nome_turma, ', ') AS turmas
            FROM aluno a
            LEFT JOIN matricula m ON m.id_aluno = a.id_aluno AND m.status = 'Ativa'
            LEFT JOIN turma t ON t.id_turma = m.id_turma
            GROUP BY a.id_aluno
            ORDER BY a.nome
        """).fetchall()
    return render_template("alunos.html", alunos=registros, termo=termo)


@app.route("/alunos/novo", methods=["GET", "POST"])
@app.route("/alunos/<int:aluno_id>/editar", methods=["GET", "POST"])
@login_required
def aluno_form(aluno_id=None):
    aluno = None
    if aluno_id is not None:
        aluno = g.db.execute("SELECT * FROM aluno WHERE id_aluno = ?", (aluno_id,)).fetchone()
        if aluno is None:
            abort(404)
    if request.method == "POST":
        csrf_protect()
        nome = request.form.get("nome", "").strip()
        idade_texto = request.form.get("idade", "").strip()
        contato = request.form.get("contato_responsavel", "").strip()
        status = request.form.get("status", "Ativo")
        erros = []
        try:
            idade = int(idade_texto)
            if idade <= 0 or idade > 120:
                erros.append("A idade deve ser um número entre 1 e 120.")
        except ValueError:
            idade = None
            erros.append("Informe uma idade válida.")
        if not nome:
            erros.append("O nome do aluno é obrigatório.")
        if status not in ("Ativo", "Inativo"):
            erros.append("Status inválido.")
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("aluno_form.html", aluno=aluno)
        if aluno:
            g.db.execute("""
                UPDATE aluno SET nome = ?, idade = ?, contato_responsavel = ?, status = ?
                WHERE id_aluno = ?
            """, (nome, idade, contato, status, aluno_id))
            flash("Dados do aluno atualizados.", "success")
        else:
            g.db.execute("""
                INSERT INTO aluno (nome, idade, contato_responsavel, data_cadastro, status)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, idade, contato or None, date.today().isoformat(), status))
            flash("Aluno cadastrado com sucesso.", "success")
        g.db.commit()
        return redirect(url_for("alunos"))
    return render_template("aluno_form.html", aluno=aluno)


@app.post("/alunos/<int:aluno_id>/inativar")
@login_required
def aluno_inativar(aluno_id):
    csrf_protect()
    g.db.execute("UPDATE aluno SET status = 'Inativo' WHERE id_aluno = ?", (aluno_id,))
    g.db.execute("UPDATE matricula SET status = 'Inativa' WHERE id_aluno = ?", (aluno_id,))
    g.db.commit()
    flash("Aluno inativado. O histórico foi preservado.", "success")
    return redirect(url_for("alunos"))


@app.route("/turmas")
@login_required
def turmas():
    registros = g.db.execute("""
        SELECT t.*, COUNT(CASE WHEN m.status = 'Ativa' THEN 1 END) AS total_alunos
        FROM turma t
        LEFT JOIN matricula m ON m.id_turma = t.id_turma
        GROUP BY t.id_turma
        ORDER BY t.nome_turma
    """).fetchall()
    return render_template("turmas.html", turmas=registros)


@app.route("/turmas/nova", methods=["GET", "POST"])
@app.route("/turmas/<int:turma_id>/editar", methods=["GET", "POST"])
@login_required
def turma_form(turma_id=None):
    turma = None
    if turma_id is not None:
        turma = g.db.execute("SELECT * FROM turma WHERE id_turma = ?", (turma_id,)).fetchone()
        if turma is None:
            abort(404)
    if request.method == "POST":
        csrf_protect()
        nome = request.form.get("nome_turma", "").strip()
        curso = request.form.get("curso", "").strip()
        descricao = request.form.get("descricao", "").strip()
        status = request.form.get("status", "Ativa")
        if not nome or not curso:
            flash("Nome da turma e curso são obrigatórios.", "danger")
            return render_template("turma_form.html", turma=turma)
        if status not in ("Ativa", "Inativa"):
            flash("Status inválido.", "danger")
            return render_template("turma_form.html", turma=turma)
        if turma:
            g.db.execute("""
                UPDATE turma SET nome_turma=?, curso=?, descricao=?, status=?
                WHERE id_turma=?
            """, (nome, curso, descricao or None, status, turma_id))
            flash("Turma atualizada.", "success")
        else:
            g.db.execute("""
                INSERT INTO turma (nome_turma, curso, descricao, status)
                VALUES (?, ?, ?, ?)
            """, (nome, curso, descricao or None, status))
            flash("Turma cadastrada.", "success")
        g.db.commit()
        return redirect(url_for("turmas"))
    return render_template("turma_form.html", turma=turma)


@app.post("/turmas/<int:turma_id>/inativar")
@login_required
def turma_inativar(turma_id):
    csrf_protect()
    g.db.execute("UPDATE turma SET status='Inativa' WHERE id_turma=?", (turma_id,))
    g.db.execute("UPDATE matricula SET status='Inativa' WHERE id_turma=?", (turma_id,))
    g.db.commit()
    flash("Turma inativada. Os registros históricos foram preservados.", "success")
    return redirect(url_for("turmas"))


@app.route("/matriculas/nova", methods=["GET", "POST"])
@login_required
def matricula_nova():
    alunos = g.db.execute("SELECT id_aluno, nome FROM aluno WHERE status='Ativo' ORDER BY nome").fetchall()
    turmas = g.db.execute("SELECT id_turma, nome_turma, curso FROM turma WHERE status='Ativa' ORDER BY nome_turma").fetchall()
    if request.method == "POST":
        csrf_protect()
        try:
            aluno_id = int(request.form.get("id_aluno", ""))
            turma_id = int(request.form.get("id_turma", ""))
        except ValueError:
            flash("Selecione um aluno e uma turma válidos.", "danger")
            return render_template("matricula_form.html", alunos=alunos, turmas=turmas)
        aluno = g.db.execute("SELECT id_aluno FROM aluno WHERE id_aluno=? AND status='Ativo'", (aluno_id,)).fetchone()
        turma = g.db.execute("SELECT id_turma FROM turma WHERE id_turma=? AND status='Ativa'", (turma_id,)).fetchone()
        if not aluno or not turma:
            flash("O aluno ou a turma não existe ou está inativo.", "danger")
        else:
            try:
                g.db.execute("""
                    INSERT INTO matricula (id_aluno, id_turma, data_matricula, status)
                    VALUES (?, ?, ?, 'Ativa')
                """, (aluno_id, turma_id, date.today().isoformat()))
                g.db.commit()
                flash("Matrícula realizada com sucesso.", "success")
                return redirect(url_for("alunos"))
            except sqlite3.IntegrityError:
                flash("Este aluno já possui matrícula nesta turma.", "warning")
    return render_template("matricula_form.html", alunos=alunos, turmas=turmas)


@app.route("/atividades")
@login_required
def atividades():
    registros = g.db.execute("""
        SELECT at.*, a.nome AS aluno_nome
        FROM atividade at JOIN aluno a ON a.id_aluno = at.id_aluno
        ORDER BY at.data_registro DESC, at.id_atividade DESC
    """).fetchall()
    return render_template("atividades.html", atividades=registros)


@app.route("/atividades/nova", methods=["GET", "POST"])
@login_required
def atividade_nova():
    alunos = g.db.execute("SELECT id_aluno, nome FROM aluno WHERE status='Ativo' ORDER BY nome").fetchall()
    if request.method == "POST":
        csrf_protect()
        try:
            aluno_id = int(request.form.get("id_aluno", ""))
        except ValueError:
            aluno_id = None
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        observacao = request.form.get("observacao", "").strip()
        data_registro = request.form.get("data_registro", "").strip()
        aluno = g.db.execute("SELECT id_aluno FROM aluno WHERE id_aluno=? AND status='Ativo'", (aluno_id,)).fetchone() if aluno_id else None
        try:
            date.fromisoformat(data_registro)
            data_valida = True
        except ValueError:
            data_valida = False
        if not aluno or not titulo or not data_valida:
            flash("Selecione um aluno ativo, informe o título e uma data válida.", "danger")
        else:
            g.db.execute("""
                INSERT INTO atividade (id_aluno, titulo, descricao, data_registro, observacao)
                VALUES (?, ?, ?, ?, ?)
            """, (aluno_id, titulo, descricao or None, data_registro, observacao or None))
            g.db.commit()
            flash("Atividade registrada com sucesso.", "success")
            return redirect(url_for("historico", aluno_id=aluno_id))
    return render_template("atividade_form.html", alunos=alunos)


@app.route("/alunos/<int:aluno_id>/historico")
@login_required
def historico(aluno_id):
    aluno = g.db.execute("SELECT * FROM aluno WHERE id_aluno=?", (aluno_id,)).fetchone()
    if aluno is None:
        abort(404)
    registros = g.db.execute("""
        SELECT * FROM atividade WHERE id_aluno=?
        ORDER BY data_registro DESC, id_atividade DESC
    """, (aluno_id,)).fetchall()
    return render_template("historico.html", aluno=aluno, atividades=registros)


@app.cli.command("init-db")
def init_db_command():
    init_db(app.config["DATABASE"])
    print("Banco de dados inicializado.")


@app.cli.command("create-admin")
def create_admin_command():
    import getpass
    init_db(app.config["DATABASE"])
    nome = input("Nome do administrador: ").strip()
    usuario = input("Nome de usuário: ").strip()
    senha = getpass.getpass("Senha (mínimo 10 caracteres): ")
    if len(senha) < 10:
        print("A senha precisa ter pelo menos 10 caracteres.")
        return
    db = get_db(app.config["DATABASE"])
    try:
        db.execute(
            "INSERT INTO usuario (nome, usuario, senha_hash) VALUES (?, ?, ?)",
            (nome, usuario, generate_password_hash(senha, method="scrypt"))
        )
        db.commit()
        print("Administrador criado com sucesso.")
    except sqlite3.IntegrityError:
        print("Esse nome de usuário já existe.")
    finally:
        db.close()


@app.cli.command("seed-demo")
def seed_demo_command():
    init_db(app.config["DATABASE"])
    db = get_db(app.config["DATABASE"])
    if db.execute("SELECT COUNT(*) FROM aluno").fetchone()[0] == 0:
        db.execute("INSERT INTO aluno (nome, idade, contato_responsavel, data_cadastro, status) VALUES (?, ?, ?, ?, ?)",
                   ("Lucas Martins", 12, "(11) 99999-1234", date.today().isoformat(), "Ativo"))
        db.execute("INSERT INTO turma (nome_turma, curso, descricao, status) VALUES (?, ?, ?, ?)",
                   ("Programação Kids", "Programação", "Turma demonstrativa.", "Ativa"))
        db.commit()
        aluno_id = db.execute("SELECT id_aluno FROM aluno WHERE nome='Lucas Martins'").fetchone()[0]
        turma_id = db.execute("SELECT id_turma FROM turma WHERE nome_turma='Programação Kids'").fetchone()[0]
        db.execute("INSERT INTO matricula (id_aluno, id_turma, data_matricula, status) VALUES (?, ?, ?, 'Ativa')",
                   (aluno_id, turma_id, date.today().isoformat()))
        db.execute("INSERT INTO atividade (id_aluno, titulo, descricao, data_registro, observacao) VALUES (?, ?, ?, ?, ?)",
                   (aluno_id, "Primeiro jogo em Python", "Atividade demonstrativa.", date.today().isoformat(), "Dados fictícios."))
        db.commit()
        print("Dados fictícios inseridos.")
    else:
        print("O banco já possui alunos; nenhum dado foi inserido.")
    db.close()


if __name__ == "__main__":
    init_db(app.config["DATABASE"])
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
