"""
Testes de Orçado x Realizado (Tarefa 7.1 do roadmap).
Cobre: isolamento cross-tenant e upsert do orçamento por categoria/projeto.
"""
import datetime

import jwt
import pytest
from flask import Flask

from app.controller.auth_controller import SECRET_KEY
from app.controller.usuarios_controller import criar_usuario
from app.controller import orcamentos_controller
from app.routes import orcamentos_routes

_app = Flask(__name__)


def _criar_empresa(cursor, nome):
    cursor.execute("INSERT INTO empresas (nome) VALUES (?)", (nome,))
    return cursor.lastrowid


def _criar_projeto(cursor, nome, empresa_id):
    cursor.execute("INSERT INTO projetos (nome, colunas, empresa_id) VALUES (?, ?, ?)", (nome, '[]', empresa_id))
    return cursor.lastrowid


def _criar_categoria(cursor, nome, projeto_id):
    cursor.execute("INSERT INTO categorias (nome, projeto_id) VALUES (?, ?)", (nome, projeto_id))
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
    categoria_a = _criar_categoria(cursor, "Fundação", projeto_a)
    categoria_b = _criar_categoria(cursor, "Fundação", projeto_b)
    return {
        "empresa_a": empresa_a, "empresa_b": empresa_b,
        "projeto_a": projeto_a, "projeto_b": projeto_b,
        "categoria_a": categoria_a, "categoria_b": categoria_b,
    }


def test_upsert_cria_orcamento(duas_empresas):
    res = orcamentos_controller.upsert_orcamento(duas_empresas["projeto_a"], duas_empresas["categoria_a"], 5000)
    assert res["valor_orcado"] == 5000

    lista = orcamentos_controller.get_orcamentos(duas_empresas["empresa_a"])
    assert len(lista) == 1
    assert lista[0]["categoria_nome"] == "Fundação"


def test_upsert_atualiza_em_vez_de_duplicar(duas_empresas):
    orcamentos_controller.upsert_orcamento(duas_empresas["projeto_a"], duas_empresas["categoria_a"], 5000)
    orcamentos_controller.upsert_orcamento(duas_empresas["projeto_a"], duas_empresas["categoria_a"], 7500)

    lista = orcamentos_controller.get_orcamentos(duas_empresas["empresa_a"])
    assert len(lista) == 1
    assert float(lista[0]["valor_orcado"]) == 7500


def test_orcamentos_nao_vazam_entre_empresas(duas_empresas):
    orcamentos_controller.upsert_orcamento(duas_empresas["projeto_a"], duas_empresas["categoria_a"], 5000)
    orcamentos_controller.upsert_orcamento(duas_empresas["projeto_b"], duas_empresas["categoria_b"], 9000)

    da_empresa_a = orcamentos_controller.get_orcamentos(duas_empresas["empresa_a"])
    assert all(o["projeto_id"] == duas_empresas["projeto_a"] for o in da_empresa_a)
    assert len(da_empresa_a) == 1


def test_deletar_orcamento_de_outra_empresa_falha(duas_empresas):
    orcamento = orcamentos_controller.upsert_orcamento(duas_empresas["projeto_a"], duas_empresas["categoria_a"], 5000)
    assert orcamentos_controller.deletar_orcamento(orcamento["id"], duas_empresas["empresa_b"]) is False
    assert orcamentos_controller.deletar_orcamento(orcamento["id"], duas_empresas["empresa_a"]) is True


def test_post_orcamento_com_projeto_de_outra_empresa_falha(duas_empresas):
    admin_a = criar_usuario("admin_orc_a", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        "/orcamentos",
        method="POST",
        json={"projeto_id": duas_empresas["projeto_b"], "categoria_id": duas_empresas["categoria_b"], "valor_orcado": 1000},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = orcamentos_routes.salvar_orcamento()
        assert status == 400


def test_post_orcamento_com_categoria_de_outro_projeto_falha(duas_empresas):
    cursor_extra_projeto = None
    admin_a = criar_usuario("admin_orc_a2", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    # categoria_b pertence ao projeto_b (empresa B), mas o request usa projeto_a (empresa A)
    with _app.test_request_context(
        "/orcamentos",
        method="POST",
        json={"projeto_id": duas_empresas["projeto_a"], "categoria_id": duas_empresas["categoria_b"], "valor_orcado": 1000},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = orcamentos_routes.salvar_orcamento()
        assert status == 400


def test_post_orcamento_valido_funciona(duas_empresas):
    admin_a = criar_usuario("admin_orc_a3", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        "/orcamentos",
        method="POST",
        json={"projeto_id": duas_empresas["projeto_a"], "categoria_id": duas_empresas["categoria_a"], "valor_orcado": 3000},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta = orcamentos_routes.salvar_orcamento()
        body, status = resposta
        assert status == 201
        assert body.get_json()["valor_orcado"] == 3000
