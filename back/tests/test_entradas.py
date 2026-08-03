"""
Testes de Fluxo de Caixa (Tarefa 7.2 do roadmap).
Cobre: isolamento cross-tenant de entradas (aportes/recebimentos).
"""
import datetime

import jwt
import pytest
from flask import Flask

from app.controller.auth_controller import SECRET_KEY
from app.controller.usuarios_controller import criar_usuario
from app.controller import entradas_controller
from app.routes import entradas_routes

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


def test_criar_entrada(duas_empresas):
    res = entradas_controller.criar_entrada(duas_empresas["projeto_a"], "Aporte sócio", 10000, "2026-07-19")
    assert res["valor"] == 10000

    lista = entradas_controller.get_entradas(duas_empresas["empresa_a"])
    assert len(lista) == 1
    assert lista[0]["descricao"] == "Aporte sócio"


def test_entradas_nao_vazam_entre_empresas(duas_empresas):
    entradas_controller.criar_entrada(duas_empresas["projeto_a"], "Aporte A", 5000, "2026-07-19")
    entradas_controller.criar_entrada(duas_empresas["projeto_b"], "Aporte B", 9000, "2026-07-19")

    da_empresa_a = entradas_controller.get_entradas(duas_empresas["empresa_a"])
    assert all(e["projeto_id"] == duas_empresas["projeto_a"] for e in da_empresa_a)
    assert len(da_empresa_a) == 1


def test_deletar_entrada_de_outra_empresa_falha(duas_empresas):
    entrada = entradas_controller.criar_entrada(duas_empresas["projeto_a"], "Aporte A", 5000, "2026-07-19")
    assert entradas_controller.deletar_entrada(entrada["id"], duas_empresas["empresa_b"]) is False
    assert entradas_controller.deletar_entrada(entrada["id"], duas_empresas["empresa_a"]) is True


def test_post_entrada_com_projeto_de_outra_empresa_falha(duas_empresas):
    admin_a = criar_usuario("admin_ent_a", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        "/entradas",
        method="POST",
        json={"projeto_id": duas_empresas["projeto_b"], "descricao": "Hackeado", "valor": 1000},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = entradas_routes.nova_entrada()
        assert status == 400


def test_post_entrada_valor_zero_ou_negativo_falha(duas_empresas):
    admin_a = criar_usuario("admin_ent_a2", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        "/entradas",
        method="POST",
        json={"projeto_id": duas_empresas["projeto_a"], "descricao": "Zero", "valor": 0},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = entradas_routes.nova_entrada()
        assert status == 400
