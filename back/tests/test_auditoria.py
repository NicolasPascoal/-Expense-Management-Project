"""
Testes de Timeline/Auditoria (Tarefa 6.3 do roadmap).
Cobre: log_auditoria grava evento; isolamento cross-tenant no endpoint de leitura;
ações de lançamentos/requisições/tarefas geram entrada de auditoria.
"""
import datetime

import jwt
import pytest
from flask import Flask

from app.controller.auth_controller import SECRET_KEY
from app.controller.usuarios_controller import criar_usuario
from app.utils.auditoria import log_auditoria
from app.routes import auditoria_routes, lancamentos_routes

_app = Flask(__name__)


def _criar_empresa(cursor, nome):
    cursor.execute("INSERT INTO empresas (nome) VALUES (?)", (nome,))
    return cursor.lastrowid


def _criar_projeto(cursor, nome, empresa_id):
    cursor.execute("INSERT INTO projetos (nome, colunas, empresa_id) VALUES (?, ?, ?)", (nome, '[]', empresa_id))
    return cursor.lastrowid


def _token_para(usuario_id, username, is_admin, role, empresa_id):
    payload = {
        'id': usuario_id,
        'username': username,
        'is_admin': is_admin,
        'role': role,
        'empresa_id': empresa_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def duas_empresas(db_session):
    cursor = db_session.cursor()
    empresa_a = _criar_empresa(cursor, "Empresa A")
    empresa_b = _criar_empresa(cursor, "Empresa B")
    projeto_a = _criar_projeto(cursor, "Obra A", empresa_a)
    projeto_b = _criar_projeto(cursor, "Obra B", empresa_b)
    return {"empresa_a": empresa_a, "empresa_b": empresa_b, "projeto_a": projeto_a, "projeto_b": projeto_b}


def test_log_auditoria_grava_evento(db_session, duas_empresas):
    admin_a = criar_usuario("admin_aud_a", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    log_auditoria(duas_empresas["empresa_a"], admin_a["id"], "lancamento", 1, "criar", "teste")

    cursor = db_session.cursor()
    cursor.execute("SELECT * FROM auditoria WHERE empresa_id = ?", (duas_empresas["empresa_a"],))
    linha = cursor.fetchone()
    assert linha is not None
    assert linha["entidade"] == "lancamento"
    assert linha["acao"] == "criar"


def test_auditoria_nao_vaza_entre_empresas(duas_empresas):
    admin_a = criar_usuario("admin_aud_a2", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    admin_b = criar_usuario("admin_aud_b", "senha123", duas_empresas["empresa_b"], is_admin=1, role="admin")
    log_auditoria(duas_empresas["empresa_a"], admin_a["id"], "tarefa", 1, "criar", "tarefa A")
    log_auditoria(duas_empresas["empresa_b"], admin_b["id"], "tarefa", 2, "criar", "tarefa B")

    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])
    with _app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        resposta, status = auditoria_routes.listar_auditoria()
        eventos = resposta.get_json()

    assert all(e["detalhes"] != "tarefa B" for e in eventos)
    assert any(e["detalhes"] == "tarefa A" for e in eventos)


def test_criar_lancamento_gera_auditoria(db_session, duas_empresas):
    admin_a = criar_usuario("admin_aud_a3", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        "/lancamentos",
        method="POST",
        json={"projeto_id": duas_empresas["projeto_a"], "categoria": "Fundação", "valor": "100"},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = lancamentos_routes.novo_lancamento()
        assert status == 201

    cursor = db_session.cursor()
    cursor.execute(
        "SELECT * FROM auditoria WHERE empresa_id = ? AND entidade = 'lancamento' AND acao = 'criar'",
        (duas_empresas["empresa_a"],)
    )
    assert cursor.fetchone() is not None
