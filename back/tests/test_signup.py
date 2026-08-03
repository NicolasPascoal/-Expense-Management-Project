"""
Testes de cadastro público de construtora (Tarefa 5.1 do roadmap).
Sem verificação de e-mail (risco aceito — ver docs/Decisions.md ADR-003):
conta é criada e ativada na hora.

signup_controller foi migrado para SQLAlchemy (Tarefa 3.1) — usa a fixture
orm_session em vez de db_session (cursor cru).
"""
from app.controller.signup_controller import cadastrar_construtora
from app.models import Empresa, Projeto, Usuario


def test_signup_cria_empresa_usuario_admin_e_projeto_inicial(orm_session):
    resultado, status = cadastrar_construtora("Construtora Teste", "admin_novo", "senha123")
    assert status == 201
    empresa_id = resultado["empresa_id"]

    empresa = orm_session.get(Empresa, empresa_id)
    assert empresa.nome == "Construtora Teste"

    usuario = orm_session.query(Usuario).filter_by(username="admin_novo").first()
    assert usuario.is_admin == 1
    assert usuario.role == "admin"
    assert usuario.empresa_id == empresa_id

    projeto = orm_session.query(Projeto).filter_by(empresa_id=empresa_id).first()
    assert projeto.nome == "Minha Primeira Obra"


def test_signup_username_duplicado_nao_deixa_empresa_orfa(orm_session):
    resultado_1, status_1 = cadastrar_construtora("Construtora A", "duplicado", "senha123")
    assert status_1 == 201

    resultado_2, status_2 = cadastrar_construtora("Construtora B", "duplicado", "senha456")
    assert status_2 == 400
    assert "já está em uso" in resultado_2["erro"]

    # Rollback da transação de escrita precisa desfazer a empresa criada antes do
    # conflito de username — nunca pode sobrar uma empresa sem usuário admin.
    total = orm_session.query(Empresa).filter_by(nome="Construtora B").count()
    assert total == 0


def test_signup_valida_campos_obrigatorios(orm_session):
    _, status = cadastrar_construtora("", "usuario", "senha123")
    assert status == 400

    _, status = cadastrar_construtora("Construtora C", "ab", "senha123")
    assert status == 400

    _, status = cadastrar_construtora("Construtora D", "usuario_valido", "123")
    assert status == 400
