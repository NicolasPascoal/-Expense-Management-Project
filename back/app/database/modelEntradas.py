def create_entradas_tables(cursor):
    """
    Cria a tabela de Entradas (aportes/recebimentos) para o fluxo de caixa.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entradas (
            id SERIAL PRIMARY KEY,
            projeto_id INTEGER NOT NULL REFERENCES projetos (id) ON DELETE CASCADE,
            descricao VARCHAR(255) NOT NULL,
            valor NUMERIC NOT NULL,
            data VARCHAR(50),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
