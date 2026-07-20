from flask import Blueprint, jsonify, g
from app.database.db import get_db_connection
from app.utils.auth_middleware import token_required, non_prestador_required

auditoria_bp = Blueprint('auditoria', __name__)

LIMITE_PADRAO = 100

@auditoria_bp.route('/auditoria', methods=['GET'])
@token_required
@non_prestador_required
def listar_auditoria():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, a.entidade, a.entidade_id, a.acao, a.detalhes, a.criado_em,
               COALESCE(u.username, 'usuário removido') AS usuario_nome
        FROM auditoria a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.empresa_id = ?
        ORDER BY a.criado_em DESC
        LIMIT ?
    ''', (g.user['empresa_id'], LIMITE_PADRAO))
    eventos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(eventos), 200
