"""
Testes da Tarefa 1.2 do roadmap (middleware/decorator de isolamento por tenant).
Cobre: nenhum endpoint de leitura vaza dado de outra empresa; nenhuma
escrita/edição/exclusão consegue agir sobre um recurso de outra empresa.
"""
import datetime

import jwt
import pytest
from flask import Flask

from app.controller.auth_controller import SECRET_KEY
from app.controller.usuarios_controller import criar_usuario, get_todos_usuarios, deletar_usuario
from app.controller import lancamentos_controller, servicos_controller, tarefas_controller
from app.routes import projeto_routes, requisicao_routes

_app = Flask(__name__)  # usado só para abrir um contexto de request nos testes de rota


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


# ---------- lançamentos ----------

def test_lancamentos_nao_vazam_entre_empresas(duas_empresas):
    lancamentos_controller.criar_lancamento(duas_empresas["projeto_a"], {"valor": "100"}, duas_empresas["empresa_a"])
    lancamentos_controller.criar_lancamento(duas_empresas["projeto_b"], {"valor": "200"}, duas_empresas["empresa_b"])

    da_empresa_a = lancamentos_controller.get_todos_lancamentos(duas_empresas["empresa_a"])
    assert all(l["projeto_id"] == duas_empresas["projeto_a"] for l in da_empresa_a)
    assert len(da_empresa_a) == 1


def test_lancamento_de_outra_empresa_retorna_none(duas_empresas):
    criado = lancamentos_controller.criar_lancamento(duas_empresas["projeto_a"], {"valor": "100"}, duas_empresas["empresa_a"])

    assert lancamentos_controller.get_lancamento_por_id(criado["id"], duas_empresas["empresa_b"]) is None
    assert lancamentos_controller.atualizar_lancamento(criado["id"], {"valor": "999"}, duas_empresas["empresa_b"]) is None
    assert lancamentos_controller.deletar_lancamento(criado["id"], duas_empresas["empresa_b"]) is False
    # a empresa dona continua enxergando o registro normalmente
    assert lancamentos_controller.get_lancamento_por_id(criado["id"], duas_empresas["empresa_a"]) is not None


# ---------- categorias / contas ----------

def test_categorias_nao_vazam_entre_empresas(duas_empresas):
    servicos_controller.criar_categoria("Cat A", duas_empresas["projeto_a"])
    servicos_controller.criar_categoria("Cat B", duas_empresas["projeto_b"])

    da_empresa_a = servicos_controller.get_todas_categorias(duas_empresas["empresa_a"])
    assert all(c["projeto_id"] == duas_empresas["projeto_a"] for c in da_empresa_a)


def test_deletar_categoria_de_outra_empresa_falha(duas_empresas):
    cat = servicos_controller.criar_categoria("Cat A", duas_empresas["projeto_a"])
    assert servicos_controller.deletar_categoria(cat["id"], duas_empresas["empresa_b"]) is False
    assert servicos_controller.deletar_categoria(cat["id"], duas_empresas["empresa_a"]) is True


def test_contas_nao_vazam_entre_empresas(duas_empresas):
    servicos_controller.criar_conta("Conta A", duas_empresas["projeto_a"])
    servicos_controller.criar_conta("Conta B", duas_empresas["projeto_b"])

    da_empresa_a = servicos_controller.get_todas_contas(duas_empresas["empresa_a"])
    assert all(c["projeto_id"] == duas_empresas["projeto_a"] for c in da_empresa_a)


def test_deletar_conta_de_outra_empresa_falha(duas_empresas):
    conta = servicos_controller.criar_conta("Conta A", duas_empresas["projeto_a"])
    assert servicos_controller.deletar_conta(conta["id"], duas_empresas["empresa_b"]) is False
    assert servicos_controller.deletar_conta(conta["id"], duas_empresas["empresa_a"]) is True


# ---------- tarefas ----------

def test_tarefas_admin_nao_ve_de_outra_empresa(db_session, duas_empresas):
    prestador_a = criar_usuario("prestador_a", "senha123", duas_empresas["empresa_a"], is_admin=0, role="prestador")
    prestador_b = criar_usuario("prestador_b", "senha123", duas_empresas["empresa_b"], is_admin=0, role="prestador")

    tarefas_controller.criar_tarefa({"titulo": "Tarefa A", "prestador_id": prestador_a["id"]}, duas_empresas["empresa_a"])
    tarefas_controller.criar_tarefa({"titulo": "Tarefa B", "prestador_id": prestador_b["id"]}, duas_empresas["empresa_b"])

    tarefas_admin_a = tarefas_controller.get_tarefas(usuario_id=None, is_admin=True, empresa_id=duas_empresas["empresa_a"])
    assert all(t["prestador_id"] == prestador_a["id"] for t in tarefas_admin_a)


def test_criar_tarefa_com_prestador_de_outra_empresa_falha(duas_empresas):
    prestador_b = criar_usuario("prestador_b2", "senha123", duas_empresas["empresa_b"], is_admin=0, role="prestador")
    res, status = tarefas_controller.criar_tarefa({"titulo": "Tarefa X", "prestador_id": prestador_b["id"]}, duas_empresas["empresa_a"])
    assert status == 400
    assert "erro" in res


def test_editar_deletar_tarefa_de_outra_empresa_falha(duas_empresas):
    prestador_a = criar_usuario("prestador_a3", "senha123", duas_empresas["empresa_a"], is_admin=0, role="prestador")
    _, status = tarefas_controller.criar_tarefa({"titulo": "Tarefa A3", "prestador_id": prestador_a["id"]}, duas_empresas["empresa_a"])
    assert status == 201

    tarefas_admin_a = tarefas_controller.get_tarefas(usuario_id=None, is_admin=True, empresa_id=duas_empresas["empresa_a"])
    tarefa_id = tarefas_admin_a[0]["id"]

    res, status = tarefas_controller.atualizar_tarefa(tarefa_id, {"status": "Concluído"}, usuario_id=None, is_admin=True, empresa_id=duas_empresas["empresa_b"])
    assert status == 404

    res, status = tarefas_controller.deletar_tarefa(tarefa_id, is_admin=True, empresa_id=duas_empresas["empresa_b"])
    assert status == 404


# ---------- usuários ----------

def test_listar_usuarios_filtra_por_empresa(duas_empresas):
    criar_usuario("user_a", "senha123", duas_empresas["empresa_a"], is_admin=0, role="prestador")
    criar_usuario("user_b", "senha123", duas_empresas["empresa_b"], is_admin=0, role="prestador")

    usuarios_a = get_todos_usuarios(duas_empresas["empresa_a"])
    assert all(u["username"] != "user_b" for u in usuarios_a)
    assert any(u["username"] == "user_a" for u in usuarios_a)


def test_deletar_usuario_de_outra_empresa_falha(duas_empresas):
    user_b = criar_usuario("user_b2", "senha123", duas_empresas["empresa_b"], is_admin=0, role="prestador")
    assert deletar_usuario(user_b["id"], duas_empresas["empresa_a"]) is False
    assert deletar_usuario(user_b["id"], duas_empresas["empresa_b"]) is True


# ---------- projetos (rota, sem controller dedicado) ----------

def test_listar_projetos_filtra_por_empresa(duas_empresas):
    admin_a = criar_usuario("admin_a_proj", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        resposta = projeto_routes.listar_projetos()
        projetos = resposta.get_json()

    assert all(p["id"] != duas_empresas["projeto_b"] for p in projetos)
    assert any(p["id"] == duas_empresas["projeto_a"] for p in projetos)


def test_editar_deletar_projeto_de_outra_empresa_falha(duas_empresas):
    admin_a = criar_usuario("admin_a_proj2", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        f"/projetos/{duas_empresas['projeto_b']}",
        method="PUT",
        json={"nome": "Hackeado"},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = projeto_routes.atualizar_projeto(duas_empresas["projeto_b"])
        assert status == 404

    with _app.test_request_context(
        f"/projetos/{duas_empresas['projeto_b']}",
        method="DELETE",
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = projeto_routes.deletar_projeto(duas_empresas["projeto_b"])
        assert status == 404


# ---------- requisições (rota, sem controller dedicado) ----------

def test_listar_requisicoes_admin_filtra_por_empresa(db_session, duas_empresas):
    cursor = db_session.cursor()
    prestador_a = criar_usuario("prestador_req_a", "senha123", duas_empresas["empresa_a"], is_admin=0, role="prestador")
    prestador_b = criar_usuario("prestador_req_b", "senha123", duas_empresas["empresa_b"], is_admin=0, role="prestador")
    cursor.execute(
        "INSERT INTO requisicoes_materiais (usuario_id, nome, funcao, material) VALUES (?, ?, ?, ?)",
        (prestador_a["id"], "Fulano A", "Pedreiro", "Cimento"),
    )
    cursor.execute(
        "INSERT INTO requisicoes_materiais (usuario_id, nome, funcao, material) VALUES (?, ?, ?, ?)",
        (prestador_b["id"], "Fulano B", "Pedreiro", "Areia"),
    )

    admin_a = criar_usuario("admin_req_a", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
        resposta = requisicao_routes.listar_requisicoes()
        requisicoes = resposta.get_json()

    assert all(r["username"] != "prestador_req_b" for r in requisicoes)
    assert any(r["username"] == "prestador_req_a" for r in requisicoes)


def test_atualizar_status_requisicao_de_outra_empresa_falha(db_session, duas_empresas):
    cursor = db_session.cursor()
    prestador_b = criar_usuario("prestador_req_b2", "senha123", duas_empresas["empresa_b"], is_admin=0, role="prestador")
    cursor.execute(
        "INSERT INTO requisicoes_materiais (usuario_id, nome, funcao, material) VALUES (?, ?, ?, ?)",
        (prestador_b["id"], "Fulano B2", "Pedreiro", "Areia"),
    )
    requisicao_id = cursor.lastrowid

    admin_a = criar_usuario("admin_req_a2", "senha123", duas_empresas["empresa_a"], is_admin=1, role="admin")
    token = _token_para(admin_a["id"], admin_a["username"], True, "admin", duas_empresas["empresa_a"])

    with _app.test_request_context(
        f"/requisicoes/{requisicao_id}/status",
        method="PUT",
        json={"status": "Aprovado"},
        headers={"Authorization": f"Bearer {token}"},
    ):
        resposta, status = requisicao_routes.atualizar_status(requisicao_id)
        assert status == 404
