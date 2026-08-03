import { useState } from "react";
import { inputStyle } from "../utils/styles";
import {
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  AlertCircle,
  User,
  StickyNote,
  Save
} from "lucide-react";

const STATUS_TOKEN = {
  "Concluído": "var(--ok)",
  "Em Andamento": "var(--blue)",
  "Pendente": "var(--accent)"
};

export function TarefasTab({ user, tarefas, usuarios, createTarefa, updateTarefa, deleteTarefa, askConfirm }) {
  const [showAdd, setShowAdd] = useState(false);
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [prestadorId, setPrestadorId] = useState("");
  const [editStates, setEditStates] = useState({}); // Controla quais tarefas estão em modo edição para o prestador

  const isAdmin = user?.is_admin;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!titulo || !prestadorId) return alert("Preencha título e prestador");

    await createTarefa({
      titulo,
      descricao,
      prestador_id: parseInt(prestadorId),
      status: "Pendente"
    });

    setTitulo("");
    setDescricao("");
    setPrestadorId("");
    setShowAdd(false);
  };

  const handleUpdateStatus = async (tarefa, newStatus) => {
    await updateTarefa(tarefa.id, { status: newStatus });
  };

  const handleSaveObs = async (tarefa) => {
    const obs = editStates[tarefa.id]?.observacoes;
    await updateTarefa(tarefa.id, { observacoes: obs });
    setEditStates(prev => {
      const next = { ...prev };
      delete next[tarefa.id];
      return next;
    });
  };

  const getStatusColor = (status) => STATUS_TOKEN[status] || "var(--mut)";

  const getStatusIcon = (status) => {
    switch (status) {
      case "Concluído": return <CheckCircle2 size={16} />;
      case "Em Andamento": return <Clock size={16} />;
      case "Pendente": return <AlertCircle size={16} />;
      default: return null;
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* Header Admin */}
      {isAdmin && (
        <div style={{ marginBottom: 24 }}>
          {!showAdd ? (
            <button
              onClick={() => setShowAdd(true)}
              className="btn-primary"
              style={{ display: "flex", alignItems: "center", gap: 8 }}
            >
              <Plus size={18} /> Nova Tarefa
            </button>
          ) : (
            <div className="panel-tech">
              <div className="panel-bar">
                <div className="panel-bar-dots">
                  <span className="panel-bar-dot"></span>
                  <span className="panel-bar-dot"></span>
                  <span className="panel-bar-dot"></span>
                </div>
                <span className="panel-bar-title mono">criar nova tarefa</span>
              </div>
              <div className="panel-body">
                <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                    <div>
                      <label>Título</label>
                      <input
                        style={inputStyle}
                        value={titulo}
                        onChange={e => setTitulo(e.target.value)}
                        placeholder="Ex: Pintura da fachada"
                      />
                    </div>
                    <div>
                      <label>Responsável</label>
                      <select
                        style={inputStyle}
                        value={prestadorId}
                        onChange={e => setPrestadorId(e.target.value)}
                      >
                        <option value="">Selecione um prestador</option>
                        {usuarios.filter(u => u.role === "prestador" || u.is_admin).map(u => (
                          <option key={u.id} value={u.id}>{u.username}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label>Descrição</label>
                    <textarea
                      style={{ ...inputStyle, minHeight: 80, resize: "vertical" }}
                      value={descricao}
                      onChange={e => setDescricao(e.target.value)}
                      placeholder="Detalhes da tarefa..."
                    />
                  </div>
                  <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                    <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary">Cancelar</button>
                    <button type="submit" className="btn-primary">Criar Tarefa</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Lista de Tarefas */}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {tarefas.length === 0 && (
          <div className="panel-tech">
            <div className="panel-body" style={{ color: "var(--mut)", fontSize: 14 }}>
              Nenhuma tarefa encontrada.
            </div>
          </div>
        )}

        {tarefas.map(t => (
          <div key={t.id} className="panel-tech" style={{
            borderLeft: `3px solid ${getStatusColor(t.status)}`
          }}>
            <div className="panel-body">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <h4 style={{ margin: 0, fontSize: 16, color: "var(--ink)", fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, display: "flex", alignItems: "center", gap: 8 }}>
                  {t.titulo}
                  <span className="mono" style={{
                    fontSize: 10,
                    padding: "2px 8px",
                    borderRadius: 10,
                    background: `color-mix(in srgb, ${getStatusColor(t.status)} 15%, transparent)`,
                    color: getStatusColor(t.status),
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                    fontWeight: 500,
                    textTransform: "none"
                  }}>
                    {getStatusIcon(t.status)} {t.status}
                  </span>
                </h4>

                {isAdmin && (
                  <button
                    onClick={() => askConfirm({
                      title: "Excluir tarefa?",
                      message: `Deseja realmente excluir "${t.titulo}"?`,
                      confirmText: "Excluir",
                      onConfirm: () => deleteTarefa(t.id)
                    })}
                    style={{ border: "none", background: "none", color: "var(--mut)", cursor: "pointer", padding: 4, display: "flex", alignItems: "center" }}
                  >
                    <Trash2 size={18} />
                  </button>
                )}
              </div>

              <div className="mono" style={{ fontSize: 12, color: "var(--mut)", marginBottom: 12, display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <User size={12} /> {t.prestador_nome}
                </span>
                <span>{new Date(t.data_criacao).toLocaleDateString("pt-BR")}</span>
              </div>

              <p style={{ fontSize: 14, color: "var(--ink)", margin: "0 0 16px 0", lineHeight: 1.5 }}>
                {t.descricao || <i style={{ color: "var(--mut)" }}>Sem descrição.</i>}
              </p>

              {/* Seção de Observações / Update (Foco no Prestador) */}
              <div style={{ background: "var(--bg-alt)", borderRadius: 3, padding: 16, border: "1px solid var(--line-soft)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <label style={{ margin: 0, display: "flex", alignItems: "center", gap: 6 }}>
                    <StickyNote size={12} /> observações do prestador
                  </label>

                  {!isAdmin && !editStates[t.id] && (
                    <button
                      onClick={() => setEditStates(prev => ({ ...prev, [t.id]: { observacoes: t.observacoes || "" } }))}
                      style={{ border: "none", background: "none", color: "var(--blue)", fontSize: 12, fontWeight: 500, cursor: "pointer" }}
                    >
                      Editar
                    </button>
                  )}
                </div>

                {editStates[t.id] ? (
                  <div>
                    <textarea
                      style={{ ...inputStyle, minHeight: 60, fontSize: 13, marginBottom: 8 }}
                      value={editStates[t.id].observacoes}
                      onChange={e => setEditStates(prev => ({ ...prev, [t.id]: { ...prev[t.id], observacoes: e.target.value } }))}
                      placeholder="Adicione observações sobre o progresso..."
                    />
                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                      <button
                        onClick={() => setEditStates(prev => {
                          const next = { ...prev };
                          delete next[t.id];
                          return next;
                        })}
                        className="btn-secondary"
                        style={{ padding: "4px 12px", fontSize: 12 }}
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={() => handleSaveObs(t)}
                        className="btn-primary"
                        style={{ padding: "4px 12px", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}
                      >
                        <Save size={14} /> Salvar
                      </button>
                    </div>
                  </div>
                ) : (
                  <p style={{ fontSize: 13, color: "var(--mut)", margin: 0 }}>
                    {t.observacoes || <i>Nenhuma observação adicionada ainda.</i>}
                  </p>
                )}
              </div>

              {/* Ações de Status (Somente Prestador ou Admin) */}
              {(!isAdmin || (isAdmin && t.prestador_id === user.id)) && (
                <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {t.status !== "Pendente" && (
                    <button
                      onClick={() => handleUpdateStatus(t, "Pendente")}
                      className="btn-secondary"
                      style={{ padding: "6px 12px", fontSize: 12, color: "var(--accent)", borderColor: "var(--accent)" }}
                    >
                      Marcar como Pendente
                    </button>
                  )}
                  {t.status !== "Em Andamento" && (
                    <button
                      onClick={() => handleUpdateStatus(t, "Em Andamento")}
                      className="btn-secondary"
                      style={{ padding: "6px 12px", fontSize: 12, color: "var(--blue)", borderColor: "var(--blue)" }}
                    >
                      Em Andamento
                    </button>
                  )}
                  {t.status !== "Concluído" && (
                    <button
                      onClick={() => handleUpdateStatus(t, "Concluído")}
                      className="btn-secondary"
                      style={{ padding: "6px 12px", fontSize: 12, color: "var(--ok)", borderColor: "var(--ok)" }}
                    >
                      Concluído
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
