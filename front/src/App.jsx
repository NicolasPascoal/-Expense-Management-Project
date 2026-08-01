import { useEffect, useState } from "react";
import { useExpenses } from "./hooks/useExpenses";
import { FormModal } from "./components/FormModal";
import { Login } from "./components/Login";
import { Signup } from "./components/Signup";
import { ConfirmModal } from "./components/ConfirmModal";
import { ProjectModal } from "./components/ProjectModal";
import { ProjectSelector } from "./components/ProjectSelector";
import { LancamentosTab } from "./components/LancamentosTab";
import { DashboardTab } from "./components/DashboardTab";
import { ContasTab } from "./components/ContasTab";
import { ServicosTab } from "./components/ServicosTab";
import { AdminTab } from "./components/AdminTab";
import { RequisicoesTab } from "./components/RequisicoesTab";
import { TarefasTab } from "./components/TarefasTab";
import { OrcamentoTab } from "./components/OrcamentoTab";
import { FluxoCaixaTab } from "./components/FluxoCaixaTab";
import { TimelineTab } from "./components/TimelineTab";
import {
  LayoutDashboard,
  ClipboardList,
  ClipboardCheck,
  Wallet,
  Wrench,
  ShieldCheck,
  Plus,
  FileDown,
  FileUp,
  LogOut,
  Construction,
  ListTodo,
  Target,
  Banknote,
  History
} from "lucide-react";

export default function App() {
  const expenses = useExpenses();
  const [authView, setAuthView] = useState("login");

  // Garantir que o prestador caia na aba correta se estiver em uma aba proibida
  useEffect(() => {
    if (expenses.user?.role === "prestador" && !expenses.user?.is_admin && expenses.tab !== "requisicoes" && expenses.tab !== "tarefas") {
      expenses.setTab("tarefas");
    }
  }, [expenses.user?.role, expenses.user?.is_admin, expenses.tab]);

  if (!expenses.token) {
    const entrar = (data) => {
      expenses.setToken(data.token);
      expenses.setUser(data.user);
    };

    if (authView === "signup") {
      return <Signup onSignup={entrar} onShowLogin={() => setAuthView("login")} />;
    }
    return <Login onLogin={entrar} onShowSignup={() => setAuthView("signup")} />;
  }

  const allTabs = [
    ["dashboard", "Dashboard", LayoutDashboard],
    ["lancamentos", "Lançamentos", ClipboardList],
    ["orcamento", "Orçamento", Target],
    ["fluxocaixa", "Fluxo de Caixa", Banknote],
    ["requisicoes", "Materiais", ClipboardCheck],
    ["tarefas", "Tarefas", ListTodo],
    ["contas", "Por Conta", Wallet],
    ["servicos", "Serviços", Wrench]
  ];

  // Filtra as abas baseado no papel do usuário
  let tabs = allTabs;
  if (expenses.user?.role === "prestador" && !expenses.user?.is_admin) {
    tabs = [
      ["tarefas", "Tarefas", ListTodo],
      ["requisicoes", "Materiais", ClipboardCheck]
    ];
  }

  if (expenses.user?.is_admin) {
    tabs.push(["timeline", "Timeline", History]);
    tabs.push(["admin", "Admin", ShieldCheck]);
  }

  return (
    <div className="app-container tech-grid">
      {/* Menu Lateral Fixo (Sidebar) */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo">
            <span className="mark"></span>
            Gabaro
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div className="sidebar-section-label mono">projeto ativo</div>
          <ProjectSelector {...expenses} />
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section-label mono">navegação</div>
          {tabs.map(([k, l, Icon]) => (
            <button 
              key={k} 
              onClick={() => expenses.setTab(k)} 
              className={`sidebar-tab-btn${expenses.tab === k ? " active" : ""}`}
            >
              <Icon size={16} /> {l}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="sidebar-username">{expenses.user?.username}</span>
            <span className="sidebar-role">{expenses.user?.role || "colaborador"}</span>
          </div>
          <button onClick={expenses.logout} className="btn-logout-sidebar">
            <LogOut size={13} /> Sair do sistema
          </button>
        </div>
      </aside>

      {/* Conteúdo Central */}
      <main className="main-content">
        <header className="workspace-header">
          <div className="workspace-breadcrumb mono">
            projetos / <span className="active-proj">{expenses.projetoAtivo?.nome || "nenhum projeto selecionado"}</span>
          </div>
          <div className="workspace-title-row">
            <h1 className="workspace-title display">
              {tabs.find(x => x[0] === expenses.tab)?.[1] || "Painel"}
            </h1>
            
            {/* Ações Rápidas (Ocultas para Prestadores) */}
            {(!expenses.user?.role || expenses.user?.role !== "prestador" || expenses.user?.is_admin) && (
              <div className="workspace-actions">
                <button
                  onClick={() => { expenses.setShowForm(true); expenses.setEditId(null); expenses.setForm({}); expenses.setTab("lancamentos"); }}
                  className="btn-primary"
                  style={{ display: "flex", alignItems: "center", gap: 6 }}
                >
                  <Plus size={16} /> Novo Lançamento
                </button>
                <button
                  onClick={expenses.exportCSV}
                  className="btn-secondary"
                >
                  Exportar CSV
                </button>
                <button
                  onClick={() => expenses.fileRef.current.click()}
                  className="btn-secondary"
                >
                  Importar CSV/XLSX
                </button>
                <input ref={expenses.fileRef} type="file" accept=".csv,.xlsx,.xls" onChange={expenses.importFile} style={{ display: "none" }} />
              </div>
            )}
          </div>
        </header>

        <div className="app-content">
          {expenses.showForm && <FormModal {...expenses} />}
          {expenses.showProjectModal && <ProjectModal {...expenses} />}
          {expenses.confirmConfig && (
            <ConfirmModal
              config={expenses.confirmConfig}
              onClose={() => expenses.setConfirmConfig(null)}
            />
          )}
          {expenses.tab === "dashboard" && <DashboardTab {...expenses} />}
          {expenses.tab === "lancamentos" && <LancamentosTab {...expenses} />}
          {expenses.tab === "orcamento" && <OrcamentoTab {...expenses} />}
          {expenses.tab === "fluxocaixa" && <FluxoCaixaTab {...expenses} />}
          {expenses.tab === "timeline" && <TimelineTab {...expenses} />}
          {expenses.tab === "requisicoes" && <RequisicoesTab {...expenses} />}
          {expenses.tab === "tarefas" && <TarefasTab {...expenses} />}
          {expenses.tab === "contas" && <ContasTab {...expenses} />}
          {expenses.tab === "servicos" && <ServicosTab {...expenses} />}
          {expenses.tab === "admin" && <AdminTab {...expenses} />}
        </div>
      </main>
    </div>
  );
}

