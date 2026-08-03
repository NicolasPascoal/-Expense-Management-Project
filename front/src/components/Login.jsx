import { useState } from "react";
import { api } from "../services/api";
import { btnStyle } from "../utils/styles";
import { Construction } from "lucide-react";

export function Login({ onLogin, onShowSignup }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await api.login(username, password);
      onLogin(data);
    } catch (err) {
      setError(err.message || "Usuário ou senha incorretos");
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
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "#1e293b" }}>Gabaro</h1>
        <p style={{ color: "#64748b", marginTop: 8, marginBottom: 32 }}>Faça login para acessar o painel</p>

        <form onSubmit={handleSubmit} style={{ textAlign: "left" }}>
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#475569", marginBottom: 6 }}>Usuário</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Ex: admin"
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: 10,
                border: "1px solid #e2e8f0",
                fontSize: 14,
                outline: "none"
              }}
              required
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#475569", marginBottom: 6 }}>Senha</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: 10,
                border: "1px solid #e2e8f0",
                fontSize: 14,
                outline: "none"
              }}
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
            {loading ? "Entrando..." : "Acessar Sistema"}
          </button>
        </form>
        
        <p style={{ marginTop: 24, fontSize: 13, color: "#64748b" }}>
          Ainda não tem conta?{" "}
          <button
            type="button"
            onClick={onShowSignup}
            style={{ background: "none", border: "none", color: "#2563eb", fontWeight: 600, cursor: "pointer", fontSize: 13, padding: 0 }}
          >
            Criar conta
          </button>
        </p>
      </div>
    </div>
  );
}
