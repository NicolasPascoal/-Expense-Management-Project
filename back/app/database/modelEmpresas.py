def create_empresas_tables(cursor):
    """
    Cria a tabela de Empresas (tenant) e insere a empresa seed
    que herda o histórico legado (a antiga instância única "Obra Itanhaém").
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM empresas")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO empresas (id, nome) VALUES (1, 'Obra Itanhaém')")
        cursor.execute("SELECT setval(pg_get_serial_sequence('empresas', 'id'), COALESCE((SELECT MAX(id) FROM empresas), 1))")
