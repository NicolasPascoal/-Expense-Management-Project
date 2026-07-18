import jwt
import os
from functools import wraps
from flask import request, jsonify, g

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "FATAL: A variavel de ambiente JWT_SECRET_KEY nao esta definida no .env! "
        "Gere uma chave segura e adicione ao seu arquivo .env antes de iniciar o servidor."
    )

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'erro': 'Token de autorização ausente!'}), 401
            
        try:
            # Remove o prefixo 'Bearer ' se existir
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
                
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'erro': 'Token expirado!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'erro': 'Token inválido!'}), 401
        except Exception as e:
            return jsonify({'erro': str(e)}), 401
            
        return f(*args, **kwargs)
    return decorated

def non_prestador_required(f):
    """Bloqueia role='prestador' — usar depois de @token_required, que já populou g.user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user.get('role') == 'prestador':
            return jsonify({'erro': 'Acesso negado para este papel de usuário.'}), 403
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'erro': 'Token ausente!'}), 401

        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if not data.get('is_admin'):
                return jsonify({'erro': 'Acesso negado. Apenas administradores!'}), 403
            g.user = data
        except:
            return jsonify({'erro': 'Token inválido!'}), 401

        return f(*args, **kwargs)
    return decorated
