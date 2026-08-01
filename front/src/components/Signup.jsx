import { useState } from "react";
import { api } from "../services/api";
import { btnStyle } from "../utils/styles";
import { DEFAULT_COLUMNS } from "../data/constants";
import { Construction } from "lucide-react";

const inputStyle = {
  width: "100%",
  padding: "12px 16px",
  borderRadius: 10,
  border: "1px solid #e2e8f0",
  fontSize: 14,
  outline: "none"
};

const labelStyle = { display: "block", fontSize: 13, fontWeight: 600, color: "#475569", marginBottom: 6 };

export function Signup({ onSignup, onShowLogin }) {
  const [nomeEmpresa, setNomeEmpresa] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmarSenha, setConfirmarSenha] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmarSenha) {
      setError("As senhas não coincidem");
      return;
    }

    setLoading(true);
    try {
      const data = await api.signup(nomeEmpresa, username, password, DEFAULT_COLUMNS);
      onSignup(data);
    } catch (err) {
      setError(err.message || "Não foi possível criar a conta");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)",
      padding: 20
    }}>
      <div style={{
        background: "#fff",
        padding: "40px",
        borderRadius: 20,
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
        width: "100%",
        maxWidth: 400,
        textAlign: "center"
      }}>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
          <div style={{ background: "#f1f5f9", padding: 16, borderRadius: "50%", color: "#1e3a5f" }}>
            <Construction size={48} />
          </div>
        </div>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "#1e293b" }}>Criar conta</h1>
        <p style={{ color: "#64748b", marginTop: 8, marginBottom: 32 }}>Comece a usar o Gabaro na sua construtora</p>

        <form onSubmit={handleSubmit} style={{ textAlign: "left" }}>
          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Nome da construtora</label>
            <input
              type="text"
              value={nomeEmpresa}
              onChange={e => setNomeEmpresa(e.target.value)}
              placeholder="Ex: Construtora Silva"
              style={inputStyle}
              required
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Usuário (admin)</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Ex: admin"
              style={inputStyle}
              required
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Senha</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={inputStyle}
              required
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={labelStyle}>Confirmar senha</label>
            <input
              type="password"
              value={confirmarSenha}
              onChange={e => setConfirmarSenha(e.target.value)}
              placeholder="••••••••"
              style={inputStyle}
              required
            />
          </div>

          {error && (
            <div style={{
              background: "#fee2e2",
              color: "#dc2626",
              padding: "12px",
              borderRadius: 8,
              fontSize: 13,
              marginBottom: 20,
              textAlign: "center",
              fontWeight: 500
            }}>
              ⚠️ {error}
            </div>
          )}

          <button
            disabled={loading}
            style={{
              ...btnStyle("#2563eb"),
              width: "100%",
              padding: "14px",
              fontSize: 16,
              fontWeight: 600,
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? "Criando conta..." : "Criar conta"}
          </button>
        </form>

        <p style={{ marginTop: 24, fontSize: 13, color: "#64748b" }}>
          Já tem uma conta?{" "}
          <button
            type="button"
            onClick={onShowLogin}
            style={{ background: "none", border: "none", color: "#2563eb", fontWeight: 600, cursor: "pointer", fontSize: 13, padding: 0 }}
          >
            Entrar
          </button>
        </p>
      </div>
    </div>
  );
}
