import logging

from app.database.db import get_db_connection

logger = logging.getLogger(__name__)


def log_auditoria(empresa_id, usuario_id, entidade, entidade_id, acao, detalhes=""):
    """Grava um evento de auditoria. Falha silenciosa não deve derrubar a ação principal
    que originou o log — auditoria é acessória, não pode ser o motivo de uma requisição falhar."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO auditoria (empresa_id, usuario_id, entidade, entidade_id, acao, detalhes) VALUES (?, ?, ?, ?, ?, ?)",
            (empresa_id, usuario_id, entidade, entidade_id, acao, detalhes)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(
            "Falha ao gravar log de auditoria",
            exc_info=e,
            extra={"empresa_id": empresa_id, "usuario_id": usuario_id, "entidade": entidade, "acao": acao},
        )
