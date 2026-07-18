from app.database.db import get_db_connection
from werkzeug.security import generate_password_hash

def get_todos_usuarios(empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, is_admin, role FROM usuarios WHERE empresa_id = ?", (empresa_id,))
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return usuarios

def criar_usuario(username, password, empresa_id, is_admin=0, role='prestador'):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (username, password, is_admin, role, empresa_id) VALUES (?, ?, ?, ?, ?)",
            (username, generate_password_hash(password), 1 if is_admin else 0, role, empresa_id)
        )
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return {"id": novo_id, "username": username, "is_admin": bool(is_admin), "role": role, "empresa_id": empresa_id}
    except Exception as e:
        conn.close()
        return {"erro": str(e)}

def deletar_usuario(id, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Impede deletar o admin principal (id 1)
    if id == 1:
        conn.close()
        return False
    cursor.execute("DELETE FROM usuarios WHERE id = ? AND empresa_id = ?", (id, empresa_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success
