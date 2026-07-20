from flask import Blueprint, request, jsonify, g
from app.controller.tarefas_controller import (
    get_tarefas, criar_tarefa, atualizar_tarefa, deletar_tarefa
)
from app.utils.auth_middleware import token_required
from app.utils.auditoria import log_auditoria

tarefas_bp = Blueprint('tarefas', __name__)

@tarefas_bp.route('/tarefas', methods=['GET'])
@token_required
def listar_tarefas():
    usuario_id = g.user.get('id')
    is_admin = g.user.get('is_admin')

    tarefas = get_tarefas(usuario_id, is_admin, g.user['empresa_id'])
    return jsonify(tarefas), 200

@tarefas_bp.route('/tarefas', methods=['POST'])
@token_required
def nova_tarefa():
    is_admin = g.user.get('is_admin')

    if not is_admin:
        return jsonify({'erro': 'Apenas administradores podem criar tarefas'}), 403

    dados = request.get_json()
    res, status_code = criar_tarefa(dados, g.user['empresa_id'])
    if status_code == 201:
        log_auditoria(g.user['empresa_id'], g.user['id'], 'tarefa', res.get('id'), 'criar', dados.get('titulo', ''))
    return jsonify(res), status_code

@tarefas_bp.route('/tarefas/<int:id>', methods=['PUT'])
@token_required
def editar_tarefa(id):
    usuario_id = g.user.get('id')
    is_admin = g.user.get('is_admin')
    dados = request.get_json()

    res, status_code = atualizar_tarefa(id, dados, usuario_id, is_admin, g.user['empresa_id'])
    if status_code == 200:
        log_auditoria(g.user['empresa_id'], g.user['id'], 'tarefa', id, 'editar', ', '.join(f'{k}={v}' for k, v in dados.items()))
    return jsonify(res), status_code

@tarefas_bp.route('/tarefas/<int:id>', methods=['DELETE'])
@token_required
def remover_tarefa(id):
    is_admin = g.user.get('is_admin')
    res, status_code = deletar_tarefa(id, is_admin, g.user['empresa_id'])
    if status_code == 200:
        log_auditoria(g.user['empresa_id'], g.user['id'], 'tarefa', id, 'excluir', '')
    return jsonify(res), status_code
