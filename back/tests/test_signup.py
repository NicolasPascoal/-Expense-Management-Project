"""
Testes de cadastro público de construtora (Tarefa 5.1 do roadmap).
Sem verificação de e-mail (risco aceito — ver docs/Decisions.md ADR-003):
conta é criada e ativada na hora.
"""
from app.controller.signup_controller import cadastrar_construtora


def test_signup_cria_empresa_usuario_admin_e_projeto_inicial(db_session):
    resultado, status = cadastrar_construtora("Construtora Teste", "admin_novo", "senha123")
    assert status == 201
    empresa_id = resultado["empresa_id"]

    cursor = db_session.cursor()

    cursor.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
    assert cursor.fetchone()["nome"] == "Construtora Teste"

    cursor.execute("SELECT is_admin, role, empresa_id FROM usuarios WHERE username = ?", ("admin_novo",))
    usuario = cursor.fetchone()
    assert usuario["is_admin"] == 1
    assert usuario["role"] == "admin"
    assert usuario["empresa_id"] == empresa_id

    cursor.execute("SELECT nome FROM projetos WHERE empresa_id = ?", (empresa_id,))
    projeto = cursor.fetchone()
    assert projeto["nome"] == "Minha Primeira Obra"


def test_signup_username_duplicado_nao_deixa_empresa_orfa(db_session):
    resultado_1, status_1 = cadastrar_construtora("Construtora A", "duplicado", "senha123")
    assert status_1 == 201

    resultado_2, status_2 = cadastrar_construtora("Construtora B", "duplicado", "senha456")
    assert status_2 == 400
    assert "já está em uso" in resultado_2["erro"]

    cursor = db_session.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM empresas WHERE nome = ?", ("Construtora B",))
    # Rollback da transação de escrita precisa desfazer a empresa criada antes do
    # conflito de username — nunca pode sobrar uma empresa sem usuário admin.
    assert cursor.fetchone()["total"] == 0


def test_signup_valida_campos_obrigatorios(db_session):
    _, status = cadastrar_construtora("", "usuario", "senha123")
    assert status == 400

    _, status = cadastrar_construtora("Construtora C", "ab", "senha123")
    assert status == 400

    _, status = cadastrar_construtora("Construtora D", "usuario_valido", "123")
    assert status == 400
