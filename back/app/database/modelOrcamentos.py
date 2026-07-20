def create_orcamentos_tables(cursor):
    """
    Cria a tabela de Orcamentos (valor orcado por categoria dentro de um projeto).
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orcamentos (
            id SERIAL PRIMARY KEY,
            projeto_id INTEGER NOT NULL REFERENCES projetos (id) ON DELETE CASCADE,
            categoria_id INTEGER NOT NULL REFERENCES categorias (id) ON DELETE CASCADE,
            valor_orcado NUMERIC NOT NULL,
            UNIQUE (projeto_id, categoria_id)
        )
    ''')
