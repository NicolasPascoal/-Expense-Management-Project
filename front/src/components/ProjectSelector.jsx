import { btnStyle, inputStyle } from "../utils/styles";
import { Plus, Trash2, AlertTriangle } from "lucide-react";

export function ProjectSelector({ 
  projetos, 
  projetoAtivo, 
  setProjetoAtivo, 
  setShowProjectModal,
  deleteProject,
  user,
  askConfirm
}) {
  return (
    <div style={{
      display: "flex", 
      flexDirection: "column",
      gap: 8, 
      width: "100%"
    }}>
      <select 
        value={projetoAtivo?.id || ""} 
        onChange={(e) => {
          const p = projetos.find(x => x.id === parseInt(e.target.value));
          setProjetoAtivo(p);
        }}
        style={{ 
          ...inputStyle, 
          width: "100%", 
          margin: 0, 
          fontWeight: 500,
          color: "var(--ink)",
          borderColor: "var(--line)",
          fontFamily: "'Inter', sans-serif"
        }}
      >
        {projetos.map(p => (
          <option key={p.id} value={p.id}>{p.nome}</option>
        ))}
      </select>
      
      {user?.is_admin && (
        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button 
            onClick={() => setShowProjectModal(true)} 
            style={{ 
              background: "transparent",
              color: "var(--mut)",
              border: "none",
              padding: "2px 0",
              cursor: "pointer",
              fontSize: "11px",
              fontFamily: "'IBM Plex Mono', monospace",
              display: "flex",
              alignItems: "center",
              gap: 4
            }}
          >
            <Plus size={12} /> novo projeto
          </button>
          {projetoAtivo && (
            <button 
              onClick={() => {
                askConfirm({
                  title: `Excluir projeto "${projetoAtivo.nome}"?`,
                  message: "TODOS os lançamentos, categorias e contas deste projeto serão excluídos permanentemente.",
                  icon: <AlertTriangle size={36} color="var(--bad)" />,
                  confirmText: "Excluir Tudo",
                  onConfirm: () => deleteProject(projetoAtivo.id)
                });
              }} 
              style={{ 
                background: "transparent",
                color: "var(--bad)",
                border: "none",
                padding: "2px 0",
                cursor: "pointer",
                fontSize: "11px",
                fontFamily: "'IBM Plex Mono', monospace",
                display: "flex",
                alignItems: "center",
                gap: 4,
                marginLeft: "auto"
              }}
            >
              <Trash2 size={12} /> excluir
            </button>
          )}
        </div>
      )}
    </div>
  );
}
