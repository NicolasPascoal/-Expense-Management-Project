import os
import sys
from app.database.db import get_db_connection
from werkzeug.security import generate_password_hash

EMPRESA_SEED_ID = 1  # empresa seed ("Obra Itanhaém") — único tenant existente até o cadastro público (Tarefa 5.1)

def create_admin():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        sys.exit(
            "ADMIN_USERNAME e ADMIN_PASSWORD precisam estar definidos no ambiente "
            "(ex.: ADMIN_USERNAME=meuadmin ADMIN_PASSWORD=senha_forte python create_admin.py)."
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    is_admin = 1
    
    hashed_password = generate_password_hash(password)
    
    # Verifica se o usuário já existe
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user:
        print(f"Usuário {username} já existe. Atualizando senha, privilégios de admin e cargo...")
        cursor.execute("UPDATE usuarios SET password = ?, is_admin = ?, role = ? WHERE username = ?",
                       (hashed_password, is_admin, 'admin', username))
    else:
        print(f"Criando usuário {username}...")
        cursor.execute("INSERT INTO usuarios (username, password, is_admin, role, empresa_id) VALUES (?, ?, ?, ?, ?)",
                       (username, hashed_password, is_admin, 'admin', EMPRESA_SEED_ID))
    
    conn.commit()
    conn.close()
    print("Sucesso!")

if __name__ == "__main__":
    create_admin()
