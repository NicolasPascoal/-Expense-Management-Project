from app.database.db import get_db_connection

# Categorias
def get_todas_categorias(empresa_id, projeto_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if projeto_id:
        cursor.execute('''
            SELECT c.* FROM categorias c
            JOIN projetos p ON c.projeto_id = p.id
            WHERE c.projeto_id = ? AND p.empresa_id = ?
            ORDER BY c.nome ASC
        ''', (projeto_id, empresa_id))
    else:
        cursor.execute('''
            SELECT c.* FROM categorias c
            JOIN projetos p ON c.projeto_id = p.id
            WHERE p.empresa_id = ?
            ORDER BY c.nome ASC
        ''', (empresa_id,))
    linhas = cursor.fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]

def criar_categoria(nome, projeto_id):
    """O chamador (rota) deve validar antes que projeto_id pertence à empresa do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categorias (nome, projeto_id) VALUES (?, ?)", (nome, projeto_id))
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return {"id": novo_id, "nome": nome, "projeto_id": projeto_id}
    except Exception as e:
        conn.close()
        return {"erro": str(e)}

def deletar_categoria(id, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM categorias
        WHERE id = ? AND projeto_id IN (SELECT id FROM projetos WHERE empresa_id = ?)
    ''', (id, empresa_id))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0

# Contas
def get_todas_contas(empresa_id, projeto_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if projeto_id:
        cursor.execute('''
            SELECT c.* FROM contas c
            JOIN projetos p ON c.projeto_id = p.id
            WHERE c.projeto_id = ? AND p.empresa_id = ?
            ORDER BY c.nome ASC
        ''', (projeto_id, empresa_id))
    else:
        cursor.execute('''
            SELECT c.* FROM contas c
            JOIN projetos p ON c.projeto_id = p.id
            WHERE p.empresa_id = ?
            ORDER BY c.nome ASC
        ''', (empresa_id,))
    linhas = cursor.fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]

def criar_conta(nome, projeto_id):
    """O chamador (rota) deve validar antes que projeto_id pertence à empresa do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO contas (nome, projeto_id) VALUES (?, ?)", (nome, projeto_id))
        conn.commit()
        novo_id = cursor.lastrowid
        conn.close()
        return {"id": novo_id, "nome": nome, "projeto_id": projeto_id}
    except Exception as e:
        conn.close()
        return {"erro": str(e)}

def deletar_conta(id, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM contas
        WHERE id = ? AND projeto_id IN (SELECT id FROM projetos WHERE empresa_id = ?)
    ''', (id, empresa_id))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0
