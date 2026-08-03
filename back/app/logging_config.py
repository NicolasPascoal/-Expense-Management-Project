import json
import logging
import sys
from datetime import datetime, timezone

# Atributos padrão de um logging.LogRecord — qualquer chave além dessas em
# record.__dict__ veio de um `extra={...}` do chamador e deve virar campo
# estruturado no JSON (request_id, empresa_id, usuario_id, sql, params, etc.).
_ATRIBUTOS_PADRAO = {
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
    'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
    'processName', 'process', 'message', 'taskName',
}


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for chave, valor in record.__dict__.items():
            if chave not in _ATRIBUTOS_PADRAO and not chave.startswith("_"):
                payload[chave] = valor
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging():
    """Configura o logger raiz com saída JSON estruturada em stdout.
    Idempotente — chamar mais de uma vez (ex.: hot-reload do Flask debug) não duplica handlers."""
    root = logging.getLogger()
    if root.handlers:
        return

    # Força UTF-8 no stdout mesmo quando o console usa outra codepage (ex.: cp850
    # no `cmd`/PowerShell do Windows) — sem isso, acentos gravam bytes inválidos
    # no log, quebrando qualquer parser JSON que espere UTF-8 (Docker roda em Linux
    # com UTF-8 por padrão, mas o servidor também roda em Windows via Waitress).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
