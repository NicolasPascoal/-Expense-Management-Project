from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

# Storage em memória: adequado para um único processo backend (ver docker-compose.yml,
# um container `backend`). Se o app for escalado para múltiplos processos/instâncias,
# os contadores de rate limit passam a ser por-processo, não globais — trocar
# storage_uri por um Redis compartilhado nesse cenário.
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

# ORM (Tarefa 3.1 — introdução gradual, ver STATUS.md): coexiste com o pool raw
# psycopg2 de app/database/db.py enquanto os controllers são migrados um a um.
db = SQLAlchemy()
