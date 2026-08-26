import { useState, useEffect } from "react";
import { api } from "../services/api";
import { btnStyle, inputStyle } from "../utils/styles";

const PAPEIS = [
  { valor: "admin", label: "Admin" },
  { valor: "gestor_obra", label: "Gestor de Obra" },
  { valor: "financeiro", label: "Financeiro" },
  { valor: "prestador", label: "Prestador" },
];

export function AdminTab({ askConfirm, usuarios, fetchUsuarios }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("prestador");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // Sincroniza usuários ao abrir a aba
    fetchUsuarios();
  }, []);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const isAdmin = role === "admin";
      await api.createUsuario(username, password, isAdmin, role);
      setUsername("");
      setPassword("");
      setRole("prestador");
      fetchUsuarios();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = (id, name) => {
    if (id === 1) return alert("Não é possível remover o administrador principal.");

    askConfirm({
      title: `Remover acesso de "${name}"?`,
      message: "Este usuário não poderá mais acessar o sistema.",
      icon: "👤",
      confirmText: "Remover",
      onConfirm: async () => {
        try {
          await api.deleteUsuario(id);
          fetchUsuarios();
        } catch (err) {
          alert(err.message);
        }
      }
    });
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <div style={{ background: "#fff", padding: 24, borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)", marginBottom: 24 }}>
        <h2 style={{ margin: "0 0 16px 0", fontSize: 18 }}>Gestão de Acessos</h2>

        <form onSubmit={handleCreateUser} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div>
            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Usuário</label>
            <input
              style={{ ...inputStyle, margin: 0 }}
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Senha</label>
            <input
              type="password"
              style={{ ...inputStyle, margin: 0 }}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <div>
            <label style={{ fontSize: 12, color: "#64748b", display: "block", marginBottom: 4 }}>Papel</label>
            <select
              style={{ ...inputStyle, margin: 0 }}
              value={role}
              onChange={e => setRole(e.target.value)}
            >
              {PAPEIS.map(p => (
                <option key={p.valor} value={p.valor}>{p.label}</option>
              ))}
            </select>
          </div>
          <button type="submit" disabled={loading} style={btnStyle("#2563eb")}>
            {loading ? "..." : "Criar Usuário"}
          </button>
        </form>
        {error && <div style={{ color: "#ef4444", fontSize: 13, marginTop: 12 }}>{error}</div>}
      </div>

      <div style={{ background: "#fff", borderRadius: 12, boxShadow: "0 1px 3px rgba(0,0,0,0.1)", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0" }}>
              <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 13, color: "#64748b" }}>Usuário</th>
              <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 13, color: "#64748b" }}>Permissão / Role</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}></th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map(u => (
              <tr key={u.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                <td style={{ padding: "12px 16px", fontWeight: 500 }}>{u.username}</td>
                <td style={{ padding: "12px 16px", display: "flex", gap: 8 }}>
                  {u.is_admin ? (
                    <span style={{
                      background: "#dcfce7",
                      color: "#166534",
                      padding: "2px 8px",
                      borderRadius: 4,
                      fontSize: 11,
                      fontWeight: 600
                    }}>
                      ADMINISTRADOR
                    </span>
                  ) : null}
                  <span style={{
                    background: u.role === "prestador" ? "#dbeafe" : "#f1f5f9",
                    color: u.role === "prestador" ? "#1e40af" : "#475569",
                    padding: "2px 8px",
                    borderRadius: 4,
                    fontSize: 11,
                    fontWeight: 600,
                    textTransform: "uppercase"
                  }}>
                    {PAPEIS.find(p => p.valor === u.role)?.label || u.role || "USUÁRIO"}
                  </span>
                </td>
                <td style={{ padding: "12px 16px", textAlign: "right" }}>
                  {u.id !== 1 && (
                    <button
                      onClick={() => handleDeleteUser(u.id, u.username)}
                      style={{ border: "none", background: "none", color: "#ef4444", cursor: "pointer", fontSize: 12 }}
                    >
                      Remover Acesso
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
