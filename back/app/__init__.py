import logging
import os
import uuid
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from app.database.db import init_db
from app.extensions import db, limiter
from app.logging_config import configure_logging

load_dotenv()

logger = logging.getLogger("gabaro.request")


def _sqlalchemy_database_uri():
    # Mesmas env vars PG* de app/database/db.py — só uma segunda forma de
    # conectar ao mesmo Postgres (Tarefa 3.1, introdução gradual do ORM).
    usuario = quote_plus(os.getenv("PGUSER", "postgres"))
    senha = quote_plus(os.getenv("PGPASSWORD", "postgres"))
    host = os.getenv("PGHOST", "localhost")
    porta = os.getenv("PGPORT", "5432")
    banco = os.getenv("PGDATABASE", "expense_management")
    return f"postgresql+psycopg2://{usuario}:{senha}@{host}:{porta}/{banco}"


def _contexto_log(status_code=None):
    usuario = getattr(g, "user", None) or {}
    contexto = {
        "request_id": getattr(g, "request_id", None),
        "empresa_id": usuario.get("empresa_id"),
        "usuario_id": usuario.get("id"),
        "method": request.method,
        "path": request.path,
    }
    if status_code is not None:
        contexto["status_code"] = status_code
    return contexto


def create_app():
    configure_logging()
    app = Flask(__name__)
    limiter.init_app(app)

    app.config["SQLALCHEMY_DATABASE_URI"] = _sqlalchemy_database_uri()
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    db.init_app(app)
    from app import models  # noqa: F401 — registra as classes ORM em db.metadata

    @app.before_request
    def _atribuir_request_id():
        g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    @app.after_request
    def _logar_requisicao(response):
        logger.info("request concluída", extra=_contexto_log(response.status_code))
        response.headers["X-Request-Id"] = getattr(g, "request_id", "")
        return response

    @app.errorhandler(HTTPException)
    def _tratar_erro_http(e):
        # Erros HTTP esperados (400/401/403/404/405/429...) — sem stack trace, log em WARNING.
        logger.warning(e.description, extra=_contexto_log(e.code))
        return jsonify({"erro": e.description, "request_id": getattr(g, "request_id", None)}), e.code

    @app.errorhandler(Exception)
    def _tratar_erro_interno(e):
        # Qualquer exceção não prevista (bug, falha de banco, etc.) — nunca expõe
        # stack trace, nome de tabela/coluna ou mensagem crua de driver ao cliente.
        # Detalhe completo só vai para o log interno (exc_info).
        logger.error("Erro interno não tratado", exc_info=e, extra=_contexto_log(500))
        return jsonify({"erro": "Erro interno do servidor", "request_id": getattr(g, "request_id", None)}), 500

    # Configura CORS com origens permitidas do .env
    # Em producao, restringe para aceitar apenas requisicoes do seu frontend
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
    if allowed_origins != "*":
        origins_list = [o.strip() for o in allowed_origins.split(",")]
        CORS(app, origins=origins_list)
    else:
        CORS(app)
    
    # Inicializa o schema do banco de dados PostgreSQL
    init_db()
    
    # Importar e registrar os blueprints (rotas)
    from app.routes.lancamentos_routes import lancamentos_bp
    from app.routes.projeto_routes import projeto_bp
    from app.routes.servicos_routes import servicos_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.signup_routes import signup_bp
    from app.routes.usuarios_routes import usuarios_bp
    from app.routes.requisicao_routes import requisicao_bp
    from app.routes.tarefas_routes import tarefas_bp
    from app.routes.orcamentos_routes import orcamentos_bp
    from app.routes.entradas_routes import entradas_bp
    from app.routes.auditoria_routes import auditoria_bp

    app.register_blueprint(lancamentos_bp, url_prefix='/api')
    app.register_blueprint(projeto_bp, url_prefix='/api')
    app.register_blueprint(servicos_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(signup_bp, url_prefix='/api')
    app.register_blueprint(usuarios_bp, url_prefix='/api')
    app.register_blueprint(requisicao_bp, url_prefix='/api')
    app.register_blueprint(tarefas_bp, url_prefix='/api')
    app.register_blueprint(orcamentos_bp, url_prefix='/api')
    app.register_blueprint(entradas_bp, url_prefix='/api')
    app.register_blueprint(auditoria_bp, url_prefix='/api')
    
    return app
