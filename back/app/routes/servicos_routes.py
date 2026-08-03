from flask import Blueprint, request, jsonify, g
from app.controller.servicos_controller import (
    get_todas_categorias, criar_categoria, deletar_categoria,
    get_todas_contas, criar_conta, deletar_conta
)
from app.utils.auth_middleware import token_required, non_prestador_required
from app.utils.tenant import projeto_pertence_a_empresa

servicos_bp = Blueprint('servicos', __name__)

# Categorias
@servicos_bp.route('/categorias', methods=['GET'])
@token_required
@non_prestador_required
def listar_categorias():
    projeto_id = request.args.get('projeto_id')
    return jsonify(get_todas_categorias(g.user['empresa_id'], projeto_id)), 200

@servicos_bp.route('/categorias', methods=['POST'])
@token_required
@non_prestador_required
def nova_categoria():
    dados = request.get_json()
    nome = dados.get('nome')
    projeto_id = dados.get('projeto_id')
    if not nome or not projeto_id:
        return jsonify({'erro': 'Nome e projeto_id são obrigatórios'}), 400
    if not projeto_pertence_a_empresa(projeto_id, g.user['empresa_id']):
        return jsonify({'erro': 'projeto_id inválido'}), 400
    res = criar_categoria(nome, projeto_id)
    if 'erro' in res:
        return jsonify(res), 400
    return jsonify(res), 201

@servicos_bp.route('/categorias/<int:id>', methods=['DELETE'])
@token_required
@non_prestador_required
def remover_categoria(id):
    if deletar_categoria(id, g.user['empresa_id']):
        return jsonify({'mensagem': 'Categoria removida'}), 200
    return jsonify({'erro': 'Não encontrado'}), 404

# Contas
@servicos_bp.route('/contas', methods=['GET'])
@token_required
@non_prestador_required
def listar_contas():
    projeto_id = request.args.get('projeto_id')
    return jsonify(get_todas_contas(g.user['empresa_id'], projeto_id)), 200

@servicos_bp.route('/contas', methods=['POST'])
@token_required
@non_prestador_required
def nova_conta():
    dados = request.get_json()
    nome = dados.get('nome')
    projeto_id = dados.get('projeto_id')
    if not nome or not projeto_id:
        return jsonify({'erro': 'Nome e projeto_id são obrigatórios'}), 400
    if not projeto_pertence_a_empresa(projeto_id, g.user['empresa_id']):
        return jsonify({'erro': 'projeto_id inválido'}), 400
    res = criar_conta(nome, projeto_id)
    if 'erro' in res:
        return jsonify(res), 400
    return jsonify(res), 201

@servicos_bp.route('/contas/<int:id>', methods=['DELETE'])
@token_required
@non_prestador_required
def remover_conta(id):
    if deletar_conta(id, g.user['empresa_id']):
        return jsonify({'mensagem': 'Conta removida'}), 200
    return jsonify({'erro': 'Não encontrado'}), 404
