from flask import Blueprint, request, jsonify, g
from app.controller.usuarios_controller import (
    get_todos_usuarios, criar_usuario, deletar_usuario
)
from app.utils.auth_middleware import admin_required

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/usuarios', methods=['GET'])
@admin_required
def listar_usuarios():
    return jsonify(get_todos_usuarios(g.user['empresa_id'])), 200

@usuarios_bp.route('/usuarios', methods=['POST'])
@admin_required
def novo_usuario():
    dados = request.get_json()
    username = dados.get('username')
    password = dados.get('password')
    is_admin = dados.get('is_admin', False)
    role = dados.get('role', 'admin' if is_admin else 'prestador')

    if not username or not password:
        return jsonify({'erro': 'Username e senha são obrigatórios'}), 400

    res = criar_usuario(username, password, g.user['empresa_id'], is_admin, role)
    if 'erro' in res:
        return jsonify(res), 400
        
    return jsonify(res), 201

@usuarios_bp.route('/usuarios/<int:id>', methods=['DELETE'])
@admin_required
def remover_usuario(id):
    if deletar_usuario(id, g.user['empresa_id']):
        return jsonify({'mensagem': 'Usuário removido'}), 200
    return jsonify({'erro': 'Não foi possível remover o usuário'}), 400
