import { useState } from "react";
import { fmt } from "../utils/format";
import { Trash2 } from "lucide-react";

export function FluxoCaixaTab({ entradas, criarEntrada, removerEntrada, totalGeral, totalEntradas, saldoCaixa, askConfirm, projetoAtivo }) {
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");
  const [data, setData] = useState("");

  const handleSalvar = () => {
    const num = parseFloat(valor);
    if (!descricao.trim() || !valor || isNaN(num) || num <= 0) return;
    criarEntrada(descricao.trim(), num, data);
    setDescricao("");
    setValor("");
    setData("");
  };

  const saldoStatus = saldoCaixa >= 0 ? "var(--ok)" : "var(--bad)";

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
        <div className="panel-tech">
          <div className="panel-body">
            <span className="mono" style={{ fontSize: 11, color: "var(--mut)", textTransform: "uppercase" }}>entradas</span>
            <div className="panel-value mono" style={{ color: "var(--ok)" }}>{fmt(totalEntradas)}</div>
          </div>
        </div>
        <div className="panel-tech">
          <div className="panel-body">
            <span className="mono" style={{ fontSize: 11, color: "var(--mut)", textTransform: "uppercase" }}>saídas</span>
            <div className="panel-value mono" style={{ color: "var(--bad)" }}>{fmt(totalGeral)}</div>
          </div>
        </div>
        <div className="panel-tech">
          <div className="panel-body">
            <span className="mono" style={{ fontSize: 11, color: "var(--mut)", textTransform: "uppercase" }}>saldo — {projetoAtivo?.nome || "obra"}</span>
            <div className="panel-value mono" style={{ color: saldoStatus }}>{fmt(saldoCaixa)}</div>
          </div>
        </div>
      </div>

      <div className="panel-tech">
        <div className="panel-bar">
          <div className="panel-bar-dots">
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
          </div>
          <span className="panel-bar-title mono">registrar entrada</span>
        </div>
        <div className="panel-body" style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ flex: "2 1 200px" }}>
            <label>Descrição</label>
            <input
              placeholder="Ex: aporte sócio, recebimento cliente"
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
            />
          </div>
          <div style={{ flex: "1 1 140px" }}>
            <label>Valor (R$)</label>
            <input type="number" min="0" step="0.01" value={valor} onChange={e => setValor(e.target.value)} />
          </div>
          <div style={{ flex: "1 1 140px" }}>
            <label>Data</label>
            <input type="date" value={data} onChange={e => setData(e.target.value)} />
          </div>
          <button className="btn-primary" onClick={handleSalvar}>Registrar</button>
        </div>
      </div>

      <div className="panel-tech">
        <div className="panel-bar">
          <div className="panel-bar-dots">
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
            <span className="panel-bar-dot"></span>
          </div>
          <span className="panel-bar-title mono">entradas registradas</span>
        </div>
        <div className="panel-body">
          {entradas.length === 0 ? (
            <p style={{ color: "var(--mut)", fontSize: 14, margin: 0 }}>
              Nenhuma entrada registrada ainda nesta obra. Registrar a primeira acima.
            </p>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {entradas.map(e => (
                <div key={e.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid var(--line-soft)" }}>
                  <div>
                    <div style={{ fontSize: 13.5, color: "var(--ink)" }}>{e.descricao}</div>
                    {e.data && <div className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>{e.data}</div>}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span className="mono" style={{ fontSize: 13.5, color: "var(--ok)" }}>{fmt(parseFloat(e.valor))}</span>
                    <button
                      onClick={() => askConfirm({
                        title: "Excluir entrada?",
                        message: `Remover "${e.descricao}" do fluxo de caixa?`,
                        confirmText: "Excluir",
                        onConfirm: () => removerEntrada(e.id)
                      })}
                      style={{ border: "none", background: "none", color: "var(--mut)", cursor: "pointer", display: "flex", alignItems: "center" }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
