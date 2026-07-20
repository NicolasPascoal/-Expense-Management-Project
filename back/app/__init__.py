from flask import Flask
from flask_cors import CORS
from app.database.db import init_db
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
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
    from app.routes.usuarios_routes import usuarios_bp
    from app.routes.requisicao_routes import requisicao_bp
    from app.routes.tarefas_routes import tarefas_bp
    from app.routes.orcamentos_routes import orcamentos_bp

    app.register_blueprint(lancamentos_bp, url_prefix='/api')
    app.register_blueprint(projeto_bp, url_prefix='/api')
    app.register_blueprint(servicos_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(usuarios_bp, url_prefix='/api')
    app.register_blueprint(requisicao_bp, url_prefix='/api')
    app.register_blueprint(tarefas_bp, url_prefix='/api')
    app.register_blueprint(orcamentos_bp, url_prefix='/api')
    
    return app
