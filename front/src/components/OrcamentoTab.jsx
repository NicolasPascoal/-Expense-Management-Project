import { useState } from "react";
import { fmt } from "../utils/format";

const STATUS_COLOR = {
  ok: "var(--ok)",
  atencao: "var(--blue)",
  estourado: "var(--bad)"
};

function DefinirOrcamento({ categoriasDb, orcamentos, salvarOrcamento }) {
  const [categoriaId, setCategoriaId] = useState("");
  const [valor, setValor] = useState("");

  const orcamentoAtual = (categoriaId) =>
    (orcamentos || []).find(o => o.categoria_id === Number(categoriaId));

  const handleSelecionar = (id) => {
    setCategoriaId(id);
    const existente = orcamentoAtual(id);
    setValor(existente ? existente.valor_orcado : "");
  };

  const handleSalvar = () => {
    const num = parseFloat(valor);
    if (!categoriaId || !valor || isNaN(num) || num < 0) return;
    salvarOrcamento(Number(categoriaId), num);
    setCategoriaId("");
    setValor("");
  };

  return (
    <div className="panel-tech">
      <div className="panel-bar">
        <div className="panel-bar-dots">
          <span className="panel-bar-dot"></span>
          <span className="panel-bar-dot"></span>
          <span className="panel-bar-dot"></span>
        </div>
        <span className="panel-bar-title mono">definir orçamento</span>
      </div>
      <div className="panel-body" style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <select
          value={categoriaId}
          onChange={e => handleSelecionar(e.target.value)}
          style={{ flex: "1 1 220px" }}
        >
          <option value="">Selecione uma categoria...</option>
          {(categoriasDb || []).map(cat => (
            <option key={cat.id} value={cat.id}>
              {cat.nome}{orcamentoAtual(cat.id) ? ` (orçado: ${fmt(parseFloat(orcamentoAtual(cat.id).valor_orcado))})` : ""}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="0"
          step="0.01"
          placeholder="Valor orçado (R$)"
          value={valor}
          onChange={e => setValor(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSalvar()}
          style={{ width: 160 }}
        />
        <button className="btn-primary" onClick={handleSalvar}>
          Salvar
        </button>
      </div>
    </div>
  );
}

export function OrcamentoTab({ orcadoRealizado, projetoAtivo, categoriasDb, orcamentos, salvarOrcamento }) {
  const estouradas = (orcadoRealizado || []).filter(o => o.status === "estourado");

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <DefinirOrcamento categoriasDb={categoriasDb} orcamentos={orcamentos} salvarOrcamento={salvarOrcamento} />

      {(!orcadoRealizado || orcadoRealizado.length === 0) ? (
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
              Defina o valor orçado por categoria acima.
            </p>
          </div>
        </div>
      ) : (
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
      )}

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
