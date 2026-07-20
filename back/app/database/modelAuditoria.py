def create_auditoria_tables(cursor):
    """
    Cria a tabela de Auditoria (log de quem fez o que, quando).
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditoria (
            id SERIAL PRIMARY KEY,
            empresa_id INTEGER NOT NULL REFERENCES empresas (id) ON DELETE CASCADE,
            usuario_id INTEGER REFERENCES usuarios (id) ON DELETE SET NULL,
            entidade VARCHAR(50) NOT NULL,
            entidade_id INTEGER,
            acao VARCHAR(20) NOT NULL,
            detalhes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
