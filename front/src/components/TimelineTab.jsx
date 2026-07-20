const ENTIDADE_LABEL = {
  lancamento: "lançamento",
  requisicao: "pedido de material",
  tarefa: "tarefa"
};

const ACAO_LABEL = {
  criar: "criou",
  editar: "editou",
  excluir: "excluiu"
};

const ACAO_COLOR = {
  criar: "var(--ok)",
  editar: "var(--blue)",
  excluir: "var(--bad)"
};

function formatarData(iso) {
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function TimelineTab({ auditoria }) {
  return (
    <div className="panel-tech">
      <div className="panel-bar">
        <div className="panel-bar-dots">
          <span className="panel-bar-dot"></span>
          <span className="panel-bar-dot"></span>
          <span className="panel-bar-dot"></span>
        </div>
        <span className="panel-bar-title mono">timeline — últimos 100 eventos</span>
      </div>
      <div className="panel-body">
        {(!auditoria || auditoria.length === 0) ? (
          <p style={{ color: "var(--mut)", fontSize: 14, margin: 0 }}>
            Nenhuma ação registrada ainda nesta empresa.
          </p>
        ) : (
          <div style={{ display: "grid", gap: 2 }}>
            {auditoria.map(ev => (
              <div key={ev.id} style={{
                display: "flex",
                alignItems: "baseline",
                gap: 10,
                padding: "10px 0",
                borderBottom: "1px solid var(--line-soft)"
              }}>
                <span className="mono" style={{ fontSize: 11, color: "var(--mut)", minWidth: 110 }}>
                  {formatarData(ev.criado_em)}
                </span>
                <span style={{ fontSize: 13.5, color: "var(--ink)", flex: 1 }}>
                  <strong>{ev.usuario_nome}</strong>{" "}
                  <span style={{ color: ACAO_COLOR[ev.acao] || "var(--ink)" }}>
                    {ACAO_LABEL[ev.acao] || ev.acao}
                  </span>{" "}
                  {ENTIDADE_LABEL[ev.entidade] || ev.entidade}
                  {ev.detalhes ? <span className="mono" style={{ color: "var(--mut)" }}> — {ev.detalhes}</span> : null}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
