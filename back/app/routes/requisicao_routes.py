from flask import Blueprint, request, jsonify, g
from app.database.db import get_db_connection
from app.utils.auth_middleware import token_required, permissao_required
from app.utils.auditoria import log_auditoria
from app.utils.permissions import tem_permissao

requisicao_bp = Blueprint('requisicoes', __name__)

@requisicao_bp.route('/requisicoes', methods=['GET'])
@token_required
def listar_requisicoes():
    user = g.user
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if tem_permissao(user, 'aprovar_requisicoes'):
        cursor.execute(
            'SELECT r.*, u.username FROM requisicoes_materiais r JOIN usuarios u ON r.usuario_id = u.id '
            'WHERE u.empresa_id = ? ORDER BY data_criacao DESC',
            (user['empresa_id'],)
        )
    else:
        cursor.execute('SELECT r.*, u.username FROM requisicoes_materiais r JOIN usuarios u ON r.usuario_id = u.id WHERE r.usuario_id = ? ORDER BY data_criacao DESC', (user['id'],))
        
    requisicoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(requisicoes)

@requisicao_bp.route('/requisicoes', methods=['POST'])
@token_required
def criar_requisicao():
    user = g.user
    dados = request.get_json()
    nome = dados.get('nome')
    funcao = dados.get('funcao')
    material = dados.get('material')
    
    if not all([nome, funcao, material]):
        return jsonify({'erro': 'Campos obrigatórios: nome, funcao, material'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO requisicoes_materiais (usuario_id, nome, funcao, material) VALUES (?, ?, ?, ?)',
        (user['id'], nome, funcao, material)
    )
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_auditoria(user['empresa_id'], user['id'], 'requisicao', req_id, 'criar', material)
    return jsonify({'id': req_id, 'status': 'Pendente'}), 201

@requisicao_bp.route('/requisicoes/<int:id>/status', methods=['PUT'])
@permissao_required('aprovar_requisicoes')
def atualizar_status(id):
    dados = request.get_json()
    status = dados.get('status')
    
    if not status:
        return jsonify({'erro': 'Status é obrigatório'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE requisicoes_materiais SET status = ? '
        'WHERE id = ? AND usuario_id IN (SELECT id FROM usuarios WHERE empresa_id = ?)',
        (status, id, g.user['empresa_id'])
    )
    atualizado = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not atualizado:
        return jsonify({'erro': 'Não encontrado'}), 404
    log_auditoria(g.user['empresa_id'], g.user['id'], 'requisicao', id, 'editar', f'status -> {status}')
    return jsonify({'mensagem': 'Status atualizado'})
