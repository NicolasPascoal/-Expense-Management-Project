from flask import Blueprint, request, jsonify, g
from app.controller.orcamentos_controller import get_orcamentos, upsert_orcamento, deletar_orcamento
from app.utils.auth_middleware import token_required, non_prestador_required
from app.utils.tenant import projeto_pertence_a_empresa
from app.database.db import get_db_connection

orcamentos_bp = Blueprint('orcamentos', __name__)

def _categoria_pertence_ao_projeto(categoria_id, projeto_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categorias WHERE id = ? AND projeto_id = ?", (categoria_id, projeto_id))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

@orcamentos_bp.route('/orcamentos', methods=['GET'])
@token_required
@non_prestador_required
def listar_orcamentos():
    projeto_id = request.args.get('projeto_id')
    return jsonify(get_orcamentos(g.user['empresa_id'], projeto_id)), 200

@orcamentos_bp.route('/orcamentos', methods=['POST'])
@token_required
@non_prestador_required
def salvar_orcamento():
    dados = request.get_json()
    projeto_id = dados.get('projeto_id')
    categoria_id = dados.get('categoria_id')
    valor_orcado = dados.get('valor_orcado')

    if not projeto_id or not categoria_id or valor_orcado is None:
        return jsonify({'erro': 'projeto_id, categoria_id e valor_orcado são obrigatórios'}), 400

    if not projeto_pertence_a_empresa(projeto_id, g.user['empresa_id']):
        return jsonify({'erro': 'projeto_id inválido'}), 400

    if not _categoria_pertence_ao_projeto(categoria_id, projeto_id):
        return jsonify({'erro': 'categoria_id inválido para este projeto'}), 400

    try:
        valor_orcado = float(valor_orcado)
    except (TypeError, ValueError):
        return jsonify({'erro': 'valor_orcado precisa ser numérico'}), 400

    if valor_orcado < 0:
        return jsonify({'erro': 'valor_orcado não pode ser negativo'}), 400

    return jsonify(upsert_orcamento(projeto_id, categoria_id, valor_orcado)), 201

@orcamentos_bp.route('/orcamentos/<int:id>', methods=['DELETE'])
@token_required
@non_prestador_required
def remover_orcamento(id):
    if deletar_orcamento(id, g.user['empresa_id']):
        return jsonify({'mensagem': 'Orçamento removido'}), 200
    return jsonify({'erro': 'Não encontrado'}), 404
