import { fmt } from "../utils/format";

const STATUS_COLOR = {
  ok: "var(--ok)",
  atencao: "var(--blue)",
  estourado: "var(--bad)"
};

export function OrcamentoTab({ orcadoRealizado, projetoAtivo }) {
  if (!orcadoRealizado || orcadoRealizado.length === 0) {
    return (
      <div className="panel-tech">
        <div className="panel-bar">
          <div className="panel-bar-dots">
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
          </div>
          <span className="panel-bar-title mono">orçado × realizado</span>
        </div>
        <div className="panel-body">
          <p style={{ color: "var(--mut)", fontSize: 14, margin: 0 }}>
            Nenhum orçamento definido ainda para {projetoAtivo?.nome || "esta obra"}.
            Defina o valor orçado por categoria na aba Serviços.
          </p>
        </div>
      </div>
    );
  }

  const estouradas = orcadoRealizado.filter(o => o.status === "estourado");

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div className="panel-tech">
        <div className="panel-bar">
          <div className="panel-bar-dots">
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
          </div>
          <span className="panel-bar-title mono">orçado × realizado — por categoria</span>
        </div>
        <div className="panel-body">
          {orcadoRealizado.map(o => (
            <div key={o.categoriaId} className="bar-row">
              <div className="lbl">
                <span className="name">{o.categoria}</span>
                <span className="pct mono">{o.percentual.toFixed(0)}%</span>
              </div>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{
                    width: `${Math.min(o.percentual, 100)}%`,
                    background: STATUS_COLOR[o.status]
                  }}
                />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 12, color: "var(--mut)" }}>
                <span className="mono">{fmt(o.realizado)} de {fmt(o.orcado)}</span>
                <span className="mono">saldo {fmt(o.saldo)}</span>
              </div>
              {o.status === "estourado" && (
                <div className="flag">
                  <span>⚠</span>
                  <span>
                    <strong>{o.categoria}</strong> passou do orçado —{" "}
                    <span className="mono">+{(o.percentual - 100).toFixed(0)}%</span>
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {estouradas.length > 0 && (
        <div className="panel-tech">
          <div className="panel-bar">
            <div className="panel-bar-dots">
              <span className="panel-bar-dot"></span>
              <span className="panel-bar-dot"></span>
              <span className="panel-bar-dot"></span>
            </div>
            <span className="panel-bar-title mono">resumo</span>
          </div>
          <div className="panel-body">
            <p style={{ margin: 0, fontSize: 14, color: "var(--ink)" }}>
              {estouradas.length} {estouradas.length === 1 ? "categoria estourou" : "categorias estouraram"} o orçamento nesta obra.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
