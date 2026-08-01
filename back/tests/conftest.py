"""
Fixtures compartilhadas de testes de integração (ADR-001 — ver docs/Decisions.md):
backend testado contra um Postgres real (nunca mockado), cada teste isolado em uma
transação com rollback ao final.

Pré-requisito para rodar esta suíte: um Postgres acessível via as mesmas variáveis
PGUSER/PGPASSWORD/PGHOST/PGPORT do `.env`, com um banco de teste dedicado já criado
(nome definido por TEST_PGDATABASE, default "expense_management_test"). Este arquivo
nunca aponta para PGDATABASE do `.env` — sempre para o banco de teste, para nunca
mutar dado de desenvolvimento por acidente.
"""
import importlib
import os

os.environ["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "chave-de-teste-nao-usar-em-producao")
os.environ["PGDATABASE"] = os.getenv("TEST_PGDATABASE", "expense_management_test")

import psycopg2
import pytest

from app.database import db as db_module
from app.database.db import PostgreSQLConnectionWrapper, init_db

# Módulos que fizeram `from app.database.db import get_db_connection` diretamente —
# cada um criou sua própria referência ao símbolo, então precisa ser repatchado
# individualmente para os testes desta tarefa enxergarem a conexão de teste.
# app.controller.signup_controller NÃO está aqui: foi migrado para SQLAlchemy
# (Tarefa 3.1) e usa a fixture orm_session, não get_db_connection.
_MODULOS_COM_GET_DB_CONNECTION = [
    "app.controller.usuarios_controller",
    "app.controller.auth_controller",
    "app.controller.lancamentos_controller",
    "app.controller.servicos_controller",
    "app.controller.tarefas_controller",
    "app.controller.orcamentos_controller",
    "app.controller.entradas_controller",
    "app.utils.tenant",
    "app.utils.auditoria",
    "app.routes.projeto_routes",
    "app.routes.requisicao_routes",
    "app.routes.orcamentos_routes",
    "app.routes.auditoria_routes",
]


@pytest.fixture(scope="session", autouse=True)
def _garantir_schema():
    """Cria o schema (incluindo a empresa seed) no banco de teste, uma vez por sessão."""
    init_db()


@pytest.fixture
def db_session(monkeypatch):
    """
    Isola o teste em uma única transação: toda chamada a get_db_connection() feita
    durante o teste (inclusive por dentro de controllers) reaproveita esta mesma
    conexão; commit()/close() viram no-op e o rollback real só acontece no teardown.
    """
    raw_conn = psycopg2.connect(
        user=db_module.PG_USER,
        password=db_module.PG_PASSWORD,
        host=db_module.PG_HOST,
        port=db_module.PG_PORT,
        database=db_module.PG_DATABASE,
    )

    class _TestConnectionWrapper(PostgreSQLConnectionWrapper):
        def commit(self):
            pass

        def close(self):
            pass

    wrapper = _TestConnectionWrapper(raw_conn)

    monkeypatch.setattr(db_module, "get_db_connection", lambda: wrapper)
    for nome_modulo in _MODULOS_COM_GET_DB_CONNECTION:
        modulo = importlib.import_module(nome_modulo)
        monkeypatch.setattr(modulo, "get_db_connection", lambda: wrapper)

    yield wrapper

    raw_conn.rollback()
    raw_conn.close()


@pytest.fixture(scope="session")
def _orm_app():
    """App Flask completo (com db.init_app já feito) para os módulos migrados
    para SQLAlchemy (Tarefa 3.1). Criado uma vez por sessão — init_db() é
    idempotente (CREATE TABLE IF NOT EXISTS), então recriá-lo por teste seria
    só desperdício."""
    from app import create_app
    return create_app()


@pytest.fixture
def orm_session(_orm_app, monkeypatch):
    """Isola o teste: o código sob teste chama db.session.commit() normalmente
    (ex.: signup_controller), mas aqui commit() vira flush() — os dados ficam
    visíveis para queries dentro do mesmo teste sem nunca serem commitados de
    verdade no Postgres. Rollback explícito no teardown descarta tudo.

    (Tentativa anterior com join_transaction_mode="create_savepoint" não
    isolava de verdade com o Flask-SQLAlchemy — dado vazava pro banco de teste
    entre execuções da suíte. Substituir commit por flush é mais simples e
    não depende de como o Flask-SQLAlchemy resolve engine/bind internamente.)
    """
    from app.extensions import db as _db

    with _orm_app.app_context():
        monkeypatch.setattr(_db.session, "commit", _db.session.flush)

        yield _db.session

        _db.session.rollback()
        _db.session.remove()
