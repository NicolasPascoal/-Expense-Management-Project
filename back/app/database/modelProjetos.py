import json

def create_projetos_tables(cursor):
    """
    Cria as tabelas relacionadas a Projetos e Lancamentos, e insere as colunas padrao.
    """
    # Tabela de Projetos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projetos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            colunas TEXT,
            empresa_id INTEGER NOT NULL REFERENCES empresas(id)
        )
    ''')

    # Garantir que existe ao menos um projeto para as chaves estrangeiras, vinculado à empresa seed (id=1)
    cursor.execute("SELECT COUNT(*) FROM projetos")
    default_cols = '[{"name":"data","label":"Data","type":"text"},{"name":"categoria","label":"Categoria","type":"select"},{"name":"item","label":"Item / Descrição","type":"text"},{"name":"fornecedor","label":"Fornecedor","type":"text"},{"name":"quantidade","label":"Qtd","type":"number"},{"name":"unitario","label":"Unitário (R$)","type":"text"},{"name":"valor","label":"Valor Pago (R$)","type":"text"},{"name":"forma","label":"Forma","type":"select"},{"name":"conta","label":"Conta","type":"select"},{"name":"obs","label":"Observações","type":"textarea"}]'
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO projetos (id, nome, colunas, empresa_id) VALUES (1, 'Obra Itanhaém', ?, 1)", (default_cols,))
        # Sincroniza a sequência
        cursor.execute("SELECT setval(pg_get_serial_sequence('projetos', 'id'), COALESCE((SELECT MAX(id) FROM projetos), 1))")
    else:
        cursor.execute("UPDATE projetos SET colunas = ? WHERE id = 1 AND (colunas IS NULL OR colunas = '[]' OR colunas = '')", (default_cols,))

    # Nova tabela de lançamentos (versão 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos_v2 (
            id SERIAL PRIMARY KEY,
            projeto_id INTEGER NOT NULL,
            dados TEXT NOT NULL,
            FOREIGN KEY (projeto_id) REFERENCES projetos (id) ON DELETE CASCADE
        )
    ''')
    
    # Mantemos a tabela antiga por compatibilidade
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id SERIAL PRIMARY KEY,
            data VARCHAR(50) NOT NULL,
            categoria VARCHAR(255),
            item VARCHAR(255),
            fornecedor VARCHAR(255),
            quantidade REAL,
            unitario REAL,
            valor REAL,
            forma VARCHAR(255),
            conta VARCHAR(255),
            obs TEXT
        )
    ''')
