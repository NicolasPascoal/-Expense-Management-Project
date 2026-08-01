from flask import Blueprint, request, jsonify

from app.controller.auth_controller import login_usuario
from app.controller.signup_controller import cadastrar_construtora
from app.extensions import limiter

signup_bp = Blueprint('signup', __name__)


@signup_bp.route('/signup', methods=['POST'])
@limiter.limit("5 per hour")  # cadastro público — mesma infra de rate limiting da Tarefa 2.2
def signup():
    dados = request.get_json(silent=True) or {}
    nome_empresa = dados.get('nome_empresa')
    username = dados.get('username')
    password = dados.get('password')
    colunas = dados.get('colunas', [])

    resultado, status = cadastrar_construtora(nome_empresa, username, password, colunas)
    if status != 201:
        return jsonify(resultado), status

    # Sem verificação de e-mail (Tarefa 5.1, risco aceito — ver docs/Decisions.md ADR-003):
    # loga o admin recém-criado direto, mesmo fluxo/formato de POST /login.
    return jsonify(login_usuario(username, password)), 201
