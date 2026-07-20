from flask import Blueprint, request, jsonify, g
from app.controller.entradas_controller import get_entradas, criar_entrada, deletar_entrada
from app.utils.auth_middleware import token_required, non_prestador_required
from app.utils.tenant import projeto_pertence_a_empresa

entradas_bp = Blueprint('entradas', __name__)

@entradas_bp.route('/entradas', methods=['GET'])
@token_required
@non_prestador_required
def listar_entradas():
    projeto_id = request.args.get('projeto_id')
    return jsonify(get_entradas(g.user['empresa_id'], projeto_id)), 200

@entradas_bp.route('/entradas', methods=['POST'])
@token_required
@non_prestador_required
def nova_entrada():
    dados = request.get_json()
    projeto_id = dados.get('projeto_id')
    descricao = dados.get('descricao')
    valor = dados.get('valor')
    data = dados.get('data')

    if not projeto_id or not descricao or valor is None:
        return jsonify({'erro': 'projeto_id, descricao e valor são obrigatórios'}), 400

    if not projeto_pertence_a_empresa(projeto_id, g.user['empresa_id']):
        return jsonify({'erro': 'projeto_id inválido'}), 400

    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return jsonify({'erro': 'valor precisa ser numérico'}), 400

    if valor <= 0:
        return jsonify({'erro': 'valor precisa ser maior que zero'}), 400

    return jsonify(criar_entrada(projeto_id, descricao, valor, data)), 201

@entradas_bp.route('/entradas/<int:id>', methods=['DELETE'])
@token_required
@non_prestador_required
def remover_entrada(id):
    if deletar_entrada(id, g.user['empresa_id']):
        return jsonify({'mensagem': 'Entrada removida'}), 200
    return jsonify({'erro': 'Não encontrado'}), 404
