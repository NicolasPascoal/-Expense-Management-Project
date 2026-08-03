from app.database.db import get_db_connection


def projeto_pertence_a_empresa(projeto_id, empresa_id):
    """Confere se o projeto existe e pertence à empresa informada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projetos WHERE id = ? AND empresa_id = ?", (projeto_id, empresa_id))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def usuario_pertence_a_empresa(usuario_id, empresa_id):
    """Confere se o usuário existe e pertence à empresa informada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE id = ? AND empresa_id = ?", (usuario_id, empresa_id))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe
