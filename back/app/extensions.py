from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Storage em memória: adequado para um único processo backend (ver docker-compose.yml,
# um container `backend`). Se o app for escalado para múltiplos processos/instâncias,
# os contadores de rate limit passam a ser por-processo, não globais — trocar
# storage_uri por um Redis compartilhado nesse cenário.
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
