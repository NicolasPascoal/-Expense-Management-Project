from app.database.db import get_db_connection

def get_orcamentos(empresa_id, projeto_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if projeto_id:
        cursor.execute('''
            SELECT o.id, o.projeto_id, o.categoria_id, o.valor_orcado, c.nome AS categoria_nome
            FROM orcamentos o
            JOIN projetos p ON o.projeto_id = p.id
            JOIN categorias c ON o.categoria_id = c.id
            WHERE o.projeto_id = ? AND p.empresa_id = ?
            ORDER BY c.nome ASC
        ''', (projeto_id, empresa_id))
    else:
        cursor.execute('''
            SELECT o.id, o.projeto_id, o.categoria_id, o.valor_orcado, c.nome AS categoria_nome
            FROM orcamentos o
            JOIN projetos p ON o.projeto_id = p.id
            JOIN categorias c ON o.categoria_id = c.id
            WHERE p.empresa_id = ?
            ORDER BY c.nome ASC
        ''', (empresa_id,))
    linhas = cursor.fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]

def upsert_orcamento(projeto_id, categoria_id, valor_orcado):
    """O chamador (rota) deve validar antes que projeto_id/categoria_id pertencem à empresa do usuário."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM orcamentos WHERE projeto_id = ? AND categoria_id = ?",
        (projeto_id, categoria_id)
    )
    existente = cursor.fetchone()

    if existente:
        cursor.execute(
            "UPDATE orcamentos SET valor_orcado = ? WHERE id = ?",
            (valor_orcado, existente['id'])
        )
        orcamento_id = existente['id']
    else:
        cursor.execute(
            "INSERT INTO orcamentos (projeto_id, categoria_id, valor_orcado) VALUES (?, ?, ?)",
            (projeto_id, categoria_id, valor_orcado)
        )
        orcamento_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return {"id": orcamento_id, "projeto_id": projeto_id, "categoria_id": categoria_id, "valor_orcado": valor_orcado}

def deletar_orcamento(id, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM orcamentos
        WHERE id = ? AND projeto_id IN (SELECT id FROM projetos WHERE empresa_id = ?)
    ''', (id, empresa_id))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0
