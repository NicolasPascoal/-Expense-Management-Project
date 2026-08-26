"""
Testes da Tarefa 1.3 do roadmap (autorização por papel).
Cobre o mecanismo unificado de autenticação (token_required / admin_required /
non_prestador_required) e a matriz papel × rota dos módulos principais.
Matriz completa documentada em docs/Authorization.md.
"""
import datetime

import jwt
import pytest
from flask import Flask

from app.controller.auth_controller import SECRET_KEY
from app.controller.usuarios_controller import criar_usuario
from app.routes import lancamentos_routes, usuarios_routes, requisicao_routes, tarefas_routes

_app = Flask(__name__)


def _criar_empresa(cursor, nome):
    cursor.execute("INSERT INTO empresas (nome) VALUES (?)", (nome,))
    return cursor.lastrowid


def _token_para(usuario_id, username, is_admin, role, empresa_id, exp_delta_horas=1):
    payload = {
        'id': usuario_id,
        'username': username,
        'is_admin': is_admin,
        'role': role,
        'empresa_id': empresa_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=exp_delta_horas),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def papeis(db_session):
    """Uma empresa com um usuário de cada papel: admin, prestador, 'user' (sem
    regra própria — papel legado/bug documentado, Tarefa 6.1), financeiro e
    gestor_obra (papéis novos da Tarefa 6.1)."""
    cursor = db_session.cursor()
    empresa_id = _criar_empresa(cursor, "Empresa Auth")
    admin = criar_usuario("auth_admin", "senha123", empresa_id, is_admin=1, role="admin")
    prestador = criar_usuario("auth_prestador", "senha123", empresa_id, is_admin=0, role="prestador")
    comum = criar_usuario("auth_user", "senha123", empresa_id, is_admin=0, role="user")
    financeiro = criar_usuario("auth_financeiro", "senha123", empresa_id, is_admin=0, role="financeiro")
    gestor_obra = criar_usuario("auth_gestor_obra", "senha123", empresa_id, is_admin=0, role="gestor_obra")
    return {
        "empresa_id": empresa_id,
        "admin_id": admin["id"],
        "prestador_id": prestador["id"],
        "gestor_obra_id": gestor_obra["id"],
        "token_admin": _token_para(admin["id"], "auth_admin", True, "admin", empresa_id),
        "token_prestador": _token_para(prestador["id"], "auth_prestador", False, "prestador", empresa_id),
        "token_comum": _token_para(comum["id"], "auth_user", False, "user", empresa_id),
        "token_financeiro": _token_para(financeiro["id"], "auth_financeiro", False, "financeiro", empresa_id),
        "token_gestor_obra": _token_para(gestor_obra["id"], "auth_gestor_obra", False, "gestor_obra", empresa_id),
    }


# ---------- mecanismo de autenticação (ponto único) ----------

def test_sem_token_retorna_401(papeis):
    with _app.test_request_context():
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 401


def test_token_invalido_retorna_401(papeis):
    with _app.test_request_context(headers={"Authorization": "Bearer nao-e-um-token"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 401


def test_header_malformado_retorna_401(papeis):
    # "Bearer " sem nada depois — regressão: o split antigo estourava IndexError (500)
    with _app.test_request_context(headers={"Authorization": "Bearer "}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 401


def test_token_expirado_retorna_401(papeis):
    expirado = _token_para(1, "auth_admin", True, "admin", papeis["empresa_id"], exp_delta_horas=-1)
    with _app.test_request_context(headers={"Authorization": f"Bearer {expirado}"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 401


def test_admin_required_popula_g_user_com_empresa_id(papeis):
    """Regressão da Tarefa 1.1: admin_required precisa expor o payload completo em g.user."""
    from flask import g
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_admin']}"}):
        resposta, status = usuarios_routes.listar_usuarios()
        assert status == 200
        assert g.user["empresa_id"] == papeis["empresa_id"]


# ---------- matriz: lançamentos (dado financeiro — prestador bloqueado) ----------

def test_prestador_nao_acessa_lancamentos(papeis):
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_prestador']}"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 403


def test_role_desconhecido_nao_acessa_lancamentos(papeis):
    """Tarefa 6.1: non_prestador_required virou lista de permissão positiva —
    um papel sem regra própria ('user', bug legado documentado) não passa mais
    por acidente como passava antes ('libera tudo exceto prestador')."""
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_comum']}"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 403


def test_admin_acessa_lancamentos(papeis):
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_admin']}"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 200


# ---------- matriz: usuários (só admin) ----------

def test_prestador_nao_lista_usuarios(papeis):
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_prestador']}"}):
        resposta, status = usuarios_routes.listar_usuarios()
        assert status == 403


def test_role_user_nao_lista_usuarios(papeis):
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_comum']}"}):
        resposta, status = usuarios_routes.listar_usuarios()
        assert status == 403


# ---------- matriz: requisições (prestador PODE criar; só admin muda status) ----------

def test_prestador_cria_requisicao(papeis):
    with _app.test_request_context(
        "/requisicoes",
        method="POST",
        json={"nome": "Fulano", "funcao": "Pedreiro", "material": "Cimento"},
        headers={"Authorization": f"Bearer {papeis['token_prestador']}"},
    ):
        resposta, status = requisicao_routes.criar_requisicao()
        assert status == 201


def test_prestador_nao_atualiza_status_requisicao(papeis):
    with _app.test_request_context(
        "/requisicoes/1/status",
        method="PUT",
        json={"status": "Aprovado"},
        headers={"Authorization": f"Bearer {papeis['token_prestador']}"},
    ):
        resposta, status = requisicao_routes.atualizar_status(1)
        assert status == 403


# ---------- matriz: tarefas (prestador não cria) ----------

def test_prestador_nao_cria_tarefa(papeis):
    with _app.test_request_context(
        "/tarefas",
        method="POST",
        json={"titulo": "Tarefa X", "prestador_id": papeis["prestador_id"]},
        headers={"Authorization": f"Bearer {papeis['token_prestador']}"},
    ):
        resposta, status = tarefas_routes.nova_tarefa()
        assert status == 403


# ---------- matriz: papéis expandidos (Tarefa 6.1) ----------

def test_financeiro_acessa_lancamentos(papeis):
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_financeiro']}"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 200


def test_financeiro_nao_lista_usuarios(papeis):
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_financeiro']}"}):
        resposta, status = usuarios_routes.listar_usuarios()
        assert status == 403


def test_gestor_obra_nao_acessa_lancamentos(papeis):
    """Tarefa 6.2 (ainda não implementada) é quem vai dar acesso financeiro
    escopado por obra — até lá, gestor_obra não tem acesso_financeiro nenhum."""
    with _app.test_request_context(headers={"Authorization": f"Bearer {papeis['token_gestor_obra']}"}):
        resposta, status = lancamentos_routes.listar_lancamentos()
        assert status == 403


def test_gestor_obra_aprova_requisicao(papeis):
    with _app.test_request_context(
        "/requisicoes",
        method="POST",
        json={"nome": "Fulano", "funcao": "Pedreiro", "material": "Cimento"},
        headers={"Authorization": f"Bearer {papeis['token_prestador']}"},
    ):
        resposta, status = requisicao_routes.criar_requisicao()
        assert status == 201
        requisicao_id = resposta.get_json()["id"]

    with _app.test_request_context(
        f"/requisicoes/{requisicao_id}/status",
        method="PUT",
        json={"status": "Comprado"},
        headers={"Authorization": f"Bearer {papeis['token_gestor_obra']}"},
    ):
        # Sucesso não retorna tupla (status) — só o Response, default 200.
        resposta = requisicao_routes.atualizar_status(requisicao_id)
        assert resposta.status_code == 200


def test_gestor_obra_gerencia_tarefa_de_outro_prestador(papeis):
    with _app.test_request_context(
        "/tarefas",
        method="POST",
        json={"titulo": "Tarefa gestor_obra", "prestador_id": papeis["prestador_id"]},
        headers={"Authorization": f"Bearer {papeis['token_gestor_obra']}"},
    ):
        resposta, status = tarefas_routes.nova_tarefa()
        assert status == 201
        tarefa_id = resposta.get_json()["id"]

    with _app.test_request_context(
        f"/tarefas/{tarefa_id}",
        method="PUT",
        json={"status": "Em Andamento"},
        headers={"Authorization": f"Bearer {papeis['token_gestor_obra']}"},
    ):
        resposta, status = tarefas_routes.editar_tarefa(tarefa_id)
        assert status == 200
