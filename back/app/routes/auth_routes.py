from flask import Blueprint, request, jsonify
from flask_limiter.util import get_remote_address
from app.controller.auth_controller import login_usuario
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)


def _username_da_requisicao():
    dados = request.get_json(silent=True) or {}
    username = (dados.get('username') or '').strip().lower()
    # Sem username no corpo, cai para o IP — evita que todas as requisições
    # malformadas compartilhem um único balde de rate limit vazio.
    return username or get_remote_address()


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")  # por IP: barra varredura vinda de um único endereço
@limiter.limit("5 per minute;20 per hour", key_func=_username_da_requisicao)  # por conta
def login():
    dados = request.get_json()
    username = dados.get('username')
    password = dados.get('password')

    if not username or not password:
        return jsonify({'erro': 'Usuário e senha são obrigatórios'}), 400

    resultado = login_usuario(username, password)
    
    if resultado:
        return jsonify(resultado), 200
    
    return jsonify({'erro': 'Usuário ou senha inválidos'}), 401
