import { useState } from "react";
import { inputStyle, btnStyle, td } from "../utils/styles";
import { ClipboardCheck, Package, Clock, Truck, CheckCircle, XCircle } from "lucide-react";
import { can } from "../utils/permissions";

export function RequisicoesTab({ 
  user, 
  requisicoes, 
  createRequisicao, 
  updateRequisicaoStatus 
}) {
  const [nome, setNome] = useState(user?.username || "");
  const [funcao, setFuncao] = useState("");
  const [funcaoOutra, setFuncaoOutra] = useState("");
  const [material, setMaterial] = useState("");

  const funcoes = [
    "Mestre de obra",
    "Pedreiro",
    "Eletricista",
    "Marceneiro",
    "Pintor",
    "Encanador",
    "Servente",
    "Outro"
  ];

  const statusColors = {
    "Pendente": { bg: "#fef9c3", text: "#854d0e", icon: <Clock size={14} /> },
    "A caminho": { bg: "#dbeafe", text: "#1e40af", icon: <Truck size={14} /> },
    "Comprado": { bg: "#dcfce7", text: "#166534", icon: <CheckCircle size={14} /> },
    "Cancelado": { bg: "#fee2e2", text: "#991b1b", icon: <XCircle size={14} /> }
  };

  const handleCreate = (e) => {
    e.preventDefault();
    const finalFuncao = funcao === "Outro" ? funcaoOutra : funcao;
    createRequisicao({ nome, funcao: finalFuncao, material });
    setMaterial("");
  };

  return (
    <div style={{ display: "grid", gap: 24 }}>
      {/* Form de Criação (Para prestadores de serviço ou Admin) */}
      {(user?.role === "prestador" || user?.is_admin) && (
        <div style={{ background: "#fff", padding: 24, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
          <h2 style={{ margin: "0 0 16px 0", fontSize: 18, display: "flex", alignItems: "center", gap: 8 }}>
            <ClipboardCheck size={20} color="#2563eb" /> Nova Requisição de Materiais
          </h2>
          <form onSubmit={handleCreate} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
            <div>
              <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Nome do Solicitante</label>
              <input value={nome} onChange={e => setNome(e.target.value)} required style={inputStyle} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Função</label>
              <select value={funcao} onChange={e => setFuncao(e.target.value)} required style={inputStyle}>
                <option value="">Selecione...</option>
                {funcoes.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            </div>
            {funcao === "Outro" && (
              <div>
                <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Digite sua função</label>
                <input value={funcaoOutra} onChange={e => setFuncaoOutra(e.target.value)} required style={inputStyle} />
              </div>
            )}
            <div style={{ gridColumn: "1 / -1" }}>
              <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Material requisitado</label>
              <textarea value={material} onChange={e => setMaterial(e.target.value)} required style={{ ...inputStyle, minHeight: 80 }} placeholder="Descreva os materiais e quantidades..." />
            </div>
            <div style={{ gridColumn: "1 / -1" }}>
              <button type="submit" style={btnStyle("#2563eb")}>Enviar Requisição</button>
            </div>
          </form>
        </div>
      )}

      {/* Listagem */}
      <div style={{ background: "#fff", padding: 24, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
        <h2 style={{ margin: "0 0 20px 0", fontSize: 18, display: "flex", alignItems: "center", gap: 8 }}>
          <Package size={20} color="#16a34a" /> 
          {can(user, "aprovar_requisicoes") ? "Gerenciamento de Requisições" : "Minhas Requisições"}
        </h2>
        
        <div className="table-wrap">
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "#f8fafc", borderBottom: "2px solid #e2e8f0" }}>
                <th style={{ ...td, textAlign: "left" }}>Data</th>
                <th style={{ ...td, textAlign: "left" }}>Solicitante</th>
                <th style={{ ...td, textAlign: "left" }}>Função</th>
                <th style={{ ...td, textAlign: "left" }}>Material</th>
                <th style={{ ...td, textAlign: "left" }}>Status</th>
                {can(user, "aprovar_requisicoes") && <th style={{ ...td, textAlign: "right" }}>Ações</th>}
              </tr>
            </thead>
            <tbody>
              {requisicoes.map(r => (
                <tr key={r.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={td}>{new Date(r.data_criacao).toLocaleDateString()}</td>
                  <td style={td}><b>{r.nome}</b></td>
                  <td style={td}>{r.funcao}</td>
                  <td style={td}>{r.material}</td>
                  <td style={td}>
                    <span style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      padding: "4px 8px",
                      borderRadius: 6,
                      fontSize: 11,
                      fontWeight: 600,
                      background: statusColors[r.status]?.bg || "#f1f5f9",
                      color: statusColors[r.status]?.text || "#475569"
                    }}>
                      {statusColors[r.status]?.icon} {r.status}
                    </span>
                  </td>
                  {can(user, "aprovar_requisicoes") && (
                    <td style={{ ...td, textAlign: "right" }}>
                      <select 
                        value={r.status} 
                        onChange={(e) => updateRequisicaoStatus(r.id, e.target.value)}
                        style={{ ...inputStyle, fontSize: 11, padding: "4px 8px", margin: 0, width: "auto" }}
                      >
                        {Object.keys(statusColors).map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                  )}
                </tr>
              ))}
              {requisicoes.length === 0 && (
                <tr>
                  <td colSpan={can(user, "aprovar_requisicoes") ? 6 : 5} style={{ padding: 40, textAlign: "center", color: "#94a3b8" }}>
                    Nenhuma requisição encontrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
