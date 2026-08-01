import json

import psycopg2
from werkzeug.security import generate_password_hash

from app.database.db import get_db_connection

USERNAME_MIN = 3
PASSWORD_MIN = 6
NOME_PROJETO_INICIAL = "Minha Primeira Obra"


def cadastrar_construtora(nome_empresa, username, password, colunas=None):
    """Cria uma nova empresa (tenant), seu primeiro usuário admin e um projeto/obra
    inicial, tudo em uma única transação — reverte tudo se qualquer passo falhar."""
    nome_empresa = (nome_empresa or "").strip()
    username = (username or "").strip()

    if not nome_empresa:
        return {"erro": "Nome da construtora é obrigatório"}, 400
    if len(username) < USERNAME_MIN:
        return {"erro": f"Usuário precisa ter pelo menos {USERNAME_MIN} caracteres"}, 400
    if not password or len(password) < PASSWORD_MIN:
        return {"erro": f"Senha precisa ter pelo menos {PASSWORD_MIN} caracteres"}, 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("INSERT INTO empresas (nome) VALUES (?)", (nome_empresa,))
        empresa_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO usuarios (username, password, is_admin, role, empresa_id) VALUES (?, ?, ?, ?, ?)",
            (username, generate_password_hash(password), 1, "admin", empresa_id)
        )

        cursor.execute(
            "INSERT INTO projetos (nome, colunas, empresa_id) VALUES (?, ?, ?)",
            (NOME_PROJETO_INICIAL, json.dumps(colunas or []), empresa_id)
        )

        conn.commit()
        return {"empresa_id": empresa_id}, 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return {"erro": "Nome de usuário já está em uso"}, 400
    finally:
        conn.close()
