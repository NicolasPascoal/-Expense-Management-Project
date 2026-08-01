import json

import psycopg2
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Empresa, Projeto, Usuario

USERNAME_MIN = 3
PASSWORD_MIN = 6
NOME_PROJETO_INICIAL = "Minha Primeira Obra"


def cadastrar_construtora(nome_empresa, username, password, colunas=None):
    """Cria uma nova empresa (tenant), seu primeiro usuário admin e um projeto/obra
    inicial, tudo em uma única transação — reverte tudo se qualquer passo falhar.

    Primeiro módulo migrado para SQLAlchemy (Tarefa 3.1, ver STATUS.md) — prova
    do padrão que os demais controllers vão seguir, um de cada vez."""
    nome_empresa = (nome_empresa or "").strip()
    username = (username or "").strip()

    if not nome_empresa:
        return {"erro": "Nome da construtora é obrigatório"}, 400
    if len(username) < USERNAME_MIN:
        return {"erro": f"Usuário precisa ter pelo menos {USERNAME_MIN} caracteres"}, 400
    if not password or len(password) < PASSWORD_MIN:
        return {"erro": f"Senha precisa ter pelo menos {PASSWORD_MIN} caracteres"}, 400

    try:
        empresa = Empresa(nome=nome_empresa)
        db.session.add(empresa)
        db.session.flush()  # popula empresa.id sem precisar commitar ainda

        db.session.add(Usuario(
            username=username,
            password=generate_password_hash(password),
            is_admin=1,
            role="admin",
            empresa_id=empresa.id,
        ))
        db.session.add(Projeto(
            nome=NOME_PROJETO_INICIAL,
            colunas=json.dumps(colunas or []),
            empresa_id=empresa.id,
        ))

        db.session.commit()
        return {"empresa_id": empresa.id}, 201
    except IntegrityError as e:
        db.session.rollback()
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            return {"erro": "Nome de usuário já está em uso"}, 400
        raise
