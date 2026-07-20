from app.database.db import get_db_connection

def get_entradas(empresa_id, projeto_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if projeto_id:
        cursor.execute('''
            SELECT e.* FROM entradas e
            JOIN projetos p ON e.projeto_id = p.id
            WHERE e.projeto_id = ? AND p.empresa_id = ?
            ORDER BY e.criado_em DESC
        ''', (projeto_id, empresa_id))
    else:
        cursor.execute('''
            SELECT e.* FROM entradas e
            JOIN projetos p ON e.projeto_id = p.id
            WHERE p.empresa_id = ?
            ORDER BY e.criado_em DESC
        ''', (empresa_id,))
    linhas = cursor.fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]

def criar_entrada(projeto_id, descricao, valor, data):
    """O chamador (rota) deve validar antes que projeto_id pertence à empresa do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entradas (projeto_id, descricao, valor, data) VALUES (?, ?, ?, ?)",
        (projeto_id, descricao, valor, data)
    )
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return {"id": novo_id, "projeto_id": projeto_id, "descricao": descricao, "valor": valor, "data": data}

def deletar_entrada(id, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM entradas
        WHERE id = ? AND projeto_id IN (SELECT id FROM projetos WHERE empresa_id = ?)
    ''', (id, empresa_id))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0
