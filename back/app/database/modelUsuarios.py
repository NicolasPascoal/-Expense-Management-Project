from werkzeug.security import generate_password_hash

def create_usuarios_tables(cursor):
    """
    Cria a tabela de Usuarios e insere o administrador padrao.
    """
    # Tabela de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            is_admin INTEGER DEFAULT 0,
            role VARCHAR(50) DEFAULT 'prestador',
            empresa_id INTEGER NOT NULL REFERENCES empresas(id)
        )
    ''')

    # Seed inicial admin, vinculado à empresa seed (id=1).
    # O backfill de role a partir de is_admin (antes rodava a cada boot aqui)
    # virou migration de dado única — ver migrations/versions/61a73b52f4cf_*.py
    # (Tarefa 3.1, STATUS.md).
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, password, is_admin, role, empresa_id) VALUES ('admin', ?, 1, 'admin', 1)",
                       (generate_password_hash("admin"),))
        cursor.execute("SELECT setval(pg_get_serial_sequence('usuarios', 'id'), COALESCE((SELECT MAX(id) FROM usuarios), 1))")
