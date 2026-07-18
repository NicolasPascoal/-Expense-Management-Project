from app.database.db import get_db_connection
from app.utils.tenant import usuario_pertence_a_empresa

def get_tarefas(usuario_id, is_admin, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_admin:
        # Admin vê todas as tarefas da própria empresa, com info do prestador
        cursor.execute('''
            SELECT t.*, u.username as prestador_nome
            FROM tarefas t
            LEFT JOIN usuarios u ON t.prestador_id = u.id
            WHERE u.empresa_id = ?
            ORDER BY t.data_criacao DESC
        ''', (empresa_id,))
    else:
        # Prestador vê apenas as suas tarefas
        cursor.execute('''
            SELECT t.*, u.username as prestador_nome
            FROM tarefas t
            LEFT JOIN usuarios u ON t.prestador_id = u.id
            WHERE t.prestador_id = ?
            ORDER BY t.data_criacao DESC
        ''', (usuario_id,))

    tarefas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tarefas

def _tarefa_pertence_a_empresa(cursor, tarefa_id, empresa_id):
    cursor.execute('''
        SELECT t.prestador_id FROM tarefas t
        JOIN usuarios u ON t.prestador_id = u.id
        WHERE t.id = ? AND u.empresa_id = ?
    ''', (tarefa_id, empresa_id))
    return cursor.fetchone()

def criar_tarefa(dados, empresa_id):
    titulo = dados.get('titulo')
    descricao = dados.get('descricao', '')
    prestador_id = dados.get('prestador_id')
    status = dados.get('status', 'Pendente')
    observacoes = dados.get('observacoes', '')

    if not titulo or not prestador_id:
        return {'erro': 'Título e Prestador são obrigatórios'}, 400

    if not usuario_pertence_a_empresa(prestador_id, empresa_id):
        return {'erro': 'Prestador inválido'}, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO tarefas (titulo, descricao, prestador_id, status, observacoes)
            VALUES (?, ?, ?, ?, ?)
        ''', (titulo, descricao, prestador_id, status, observacoes))
        conn.commit()
        novo_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        return {'erro': f'Erro ao criar tarefa: {str(e)}'}, 500

    conn.close()
    return {'mensagem': 'Tarefa criada com sucesso!', 'id': novo_id}, 201

def atualizar_tarefa(tarefa_id, dados, usuario_id, is_admin, empresa_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar se a tarefa existe, a quem pertence e se é da mesma empresa
    tarefa = _tarefa_pertence_a_empresa(cursor, tarefa_id, empresa_id)

    if not tarefa:
        conn.close()
        return {'erro': 'Tarefa não encontrada'}, 404

    if not is_admin and tarefa['prestador_id'] != usuario_id:
        conn.close()
        return {'erro': 'Acesso negado'}, 403

    try:
        if is_admin:
            # Admin pode atualizar tudo
            titulo = dados.get('titulo')
            descricao = dados.get('descricao')
            prestador_id = dados.get('prestador_id')
            status = dados.get('status')
            observacoes = dados.get('observacoes')

            if prestador_id is not None:
                cursor.execute('SELECT id FROM usuarios WHERE id = ? AND empresa_id = ?', (prestador_id, empresa_id))
                if cursor.fetchone() is None:
                    conn.close()
                    return {'erro': 'Prestador inválido'}, 400

            updates = []
            params = []

            if titulo is not None:
                updates.append("titulo = ?")
                params.append(titulo)
            if descricao is not None:
                updates.append("descricao = ?")
                params.append(descricao)
            if prestador_id is not None:
                updates.append("prestador_id = ?")
                params.append(prestador_id)
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if observacoes is not None:
                updates.append("observacoes = ?")
                params.append(observacoes)

            if not updates:
                conn.close()
                return {'mensagem': 'Nenhum dado para atualizar'}, 200

            query = f"UPDATE tarefas SET {', '.join(updates)} WHERE id = ?"
            params.append(tarefa_id)
            cursor.execute(query, tuple(params))

        else:
            # Prestador só pode atualizar status e observações
            status = dados.get('status')
            observacoes = dados.get('observacoes')

            updates = []
            params = []

            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if observacoes is not None:
                updates.append("observacoes = ?")
                params.append(observacoes)

            if not updates:
                conn.close()
                return {'mensagem': 'Nenhum dado para atualizar'}, 200

            query = f"UPDATE tarefas SET {', '.join(updates)} WHERE id = ?"
            params.append(tarefa_id)
            cursor.execute(query, tuple(params))

        conn.commit()
    except Exception as e:
        conn.close()
        return {'erro': f'Erro ao atualizar tarefa: {str(e)}'}, 500

    conn.close()
    return {'mensagem': 'Tarefa atualizada com sucesso!'}, 200

def deletar_tarefa(tarefa_id, is_admin, empresa_id):
    if not is_admin:
        return {'erro': 'Acesso negado'}, 403

    conn = get_db_connection()
    cursor = conn.cursor()

    if _tarefa_pertence_a_empresa(cursor, tarefa_id, empresa_id) is None:
        conn.close()
        return {'erro': 'Tarefa não encontrada'}, 404

    cursor.execute('DELETE FROM tarefas WHERE id = ?', (tarefa_id,))

    conn.commit()
    conn.close()
    return {'mensagem': 'Tarefa deletada com sucesso!'}, 200
