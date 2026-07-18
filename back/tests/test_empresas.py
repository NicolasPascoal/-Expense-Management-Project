"""
Testes da Tarefa 1.1 do roadmap (entidade Empresa/tenant).
Cobre apenas o que esta tarefa entrega: modelagem + vínculo de usuarios/projetos.
Isolamento de leitura entre tenants é objeto da Tarefa 1.2 (ainda não implementada).
"""
import jwt
import pytest

from app.controller.auth_controller import SECRET_KEY, login_usuario
from app.controller.usuarios_controller import criar_usuario


def test_seed_empresa_existe(db_session):
    cursor = db_session.cursor()
    cursor.execute("SELECT nome FROM empresas WHERE id = 1")
    empresa = cursor.fetchone()
    assert empresa is not None
    assert empresa["nome"] == "Obra Itanhaém"


def test_criar_usuario_grava_empresa_id(db_session):
    resultado = criar_usuario("teste_tenant_1", "senha123", empresa_id=1, is_admin=0, role="prestador")
    assert "erro" not in resultado
    assert resultado["empresa_id"] == 1

    cursor = db_session.cursor()
    cursor.execute("SELECT empresa_id FROM usuarios WHERE username = ?", ("teste_tenant_1",))
    usuario = cursor.fetchone()
    assert usuario["empresa_id"] == 1


def test_projetos_exige_empresa_id(db_session):
    cursor = db_session.cursor()
    with pytest.raises(Exception):
        cursor.execute("INSERT INTO projetos (nome, colunas) VALUES (?, ?)", ("Projeto sem empresa", "[]"))


def test_login_retorna_empresa_id_no_token(db_session):
    resultado = login_usuario("admin", "admin")
    assert resultado is not None
    assert resultado["user"]["empresa_id"] == 1

    payload = jwt.decode(resultado["token"], SECRET_KEY, algorithms=["HS256"])
    assert payload["empresa_id"] == 1
