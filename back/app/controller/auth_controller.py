import jwt
import datetime
import os
from app.database.db import get_db_connection
from werkzeug.security import check_password_hash

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "FATAL: A variavel de ambiente JWT_SECRET_KEY nao esta definida no .env! "
        "Gere uma chave segura e adicione ao seu arquivo .env antes de iniciar o servidor."
    )

def login_usuario(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
    usuario = cursor.fetchone()
    conn.close()

    if usuario and check_password_hash(usuario['password'], password):
        token = jwt.encode({
            'id': usuario['id'],
            'username': usuario['username'],
            'is_admin': usuario['is_admin'],
            'role': usuario['role'],
            'empresa_id': usuario['empresa_id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")

        return {
            'token': token,
            'user': {
                'id': usuario['id'],
                'username': usuario['username'],
                'is_admin': bool(usuario['is_admin']),
                'role': usuario['role'],
                'empresa_id': usuario['empresa_id']
            }
        }

    return None
