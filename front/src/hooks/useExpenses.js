import { useState, useMemo, useRef, useEffect } from "react";
import * as XLSX from "xlsx";
import { api } from "../services/api";
import { DEFAULT_COLUMNS } from "../data/constants";
import { parseVal } from "../utils/format";

export function useExpenses() {
  const [tab, setTab] = useState("dashboard");
  const [dados, setDados] = useState([]);
  const [form, setForm] = useState({});
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [filtros, setFiltros] = useState({categoria:"",conta:"",forma:"",busca:""});
  const [deleteId, setDeleteId] = useState(null);
  const [confirmConfig, setConfirmConfig] = useState(null);
  const fileRef = useRef();


  // Estados de Projeto
  const [projetos, setProjetos] = useState([]);
  const [projetoAtivo, setProjetoAtivo] = useState(null);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [token, setToken] = useState(sessionStorage.getItem("token"));
  const [user, setUser] = useState(JSON.parse(sessionStorage.getItem("user") || "null"));
  const [categoriasDb, setCategoriasDb] = useState([]);
  const [contasDb, setContasDb] = useState([]);
  const [requisicoes, setRequisicoes] = useState([]);
  const [tarefas, setTarefas] = useState([]);
  const [usuarios, setUsuarios] = useState([]);
  const [orcamentos, setOrcamentos] = useState([]);
  const [entradas, setEntradas] = useState([]);
  const [auditoria, setAuditoria] = useState([]);

  // Inatividade (15 minutos)
  const TIMEOUT_MS = 15 * 60 * 1000;

  useEffect(() => {
    if (!token) return;

    let timeout;
    
    const resetTimer = () => {
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(() => {
        logout();
        alert("Sessão expirada por inatividade. Faça login novamente.");
      }, TIMEOUT_MS);
    };

    const events = ["mousedown", "mousemove", "keypress", "scroll", "touchstart"];
    events.forEach(e => document.addEventListener(e, resetTimer));
    
    resetTimer();

    return () => {
      if (timeout) clearTimeout(timeout);
      events.forEach(e => document.removeEventListener(e, resetTimer));
    };
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchRequisicoes();
    }
  }, [token]);

  const fetchRequisicoes = async () => {
    try {
      const res = await api.getRequisicoes();
      setRequisicoes(res);
    } catch (e) {
      console.error("Erro ao buscar requisições:", e);
    }
  };

  const createRequisicao = async (dados) => {
    try {
      await api.createRequisicao(dados);
      fetchRequisicoes();
    } catch (e) {
      alert("Erro ao criar requisição: " + e.message);
    }
  };

  const updateRequisicaoStatus = async (id, status) => {
    try {
      await api.updateRequisicaoStatus(id, status);
      fetchRequisicoes();
    } catch (e) {
      alert("Erro ao atualizar status: " + e.message);
    }
  };

  const fetchTarefas = async () => {
    try {
      const res = await api.getTarefas();
      setTarefas(res);
    } catch (e) {
      console.error("Erro ao buscar tarefas:", e);
    }
  };

  const createTarefa = async (dados) => {
    try {
      await api.createTarefa(dados);
      fetchTarefas();
    } catch (e) {
      alert("Erro ao criar tarefa: " + e.message);
    }
  };

  const updateTarefa = async (id, dados) => {
    try {
      await api.updateTarefa(id, dados);
      fetchTarefas();
    } catch (e) {
      alert("Erro ao atualizar tarefa: " + e.message);
    }
  };

  const deleteTarefa = async (id) => {
    try {
      await api.deleteTarefa(id);
      fetchTarefas();
    } catch (e) {
      alert("Erro ao deletar tarefa: " + e.message);
    }
  };

  const fetchUsuarios = async () => {
    if (!user?.is_admin) return;
    try {
      const res = await api.getUsuarios();
      setUsuarios(res);
    } catch (e) {
      console.error("Erro ao buscar usuários:", e);
    }
  };

  const fetchAuditoria = async () => {
    try {
      const res = await api.getAuditoria();
      setAuditoria(res);
    } catch (e) {
      console.error("Erro ao buscar auditoria:", e);
    }
  };

  useEffect(() => {
    const handleAuthError = () => {
      setToken(null);
    };
    window.addEventListener("auth-error", handleAuthError);
    return () => window.removeEventListener("auth-error", handleAuthError);
  }, []);

  useEffect(() => {
    if (token) {
      fetchProjetos();
      fetchTarefas();
      fetchUsuarios();
      fetchAuditoria();
    }
  }, [token]);

  const logout = () => {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    if (token && projetoAtivo) {
      fetchServicos();
      fetchOrcamentos();
      fetchEntradas();
    }
  }, [projetoAtivo, token]);

  const fetchServicos = async () => {
    if (!projetoAtivo) return;
    try {
      const [cats, ctas] = await Promise.all([
        api.getCategorias(projetoAtivo.id),
        api.getContas(projetoAtivo.id)
      ]);
      setCategoriasDb(cats);
      setContasDb(ctas);
    } catch (err) {
      console.error("Erro ao buscar serviços:", err);
    }
  };

  const fetchOrcamentos = async () => {
    if (!projetoAtivo) return;
    try {
      const res = await api.getOrcamentos(projetoAtivo.id);
      setOrcamentos(res);
    } catch (err) {
      console.error("Erro ao buscar orçamentos:", err);
    }
  };

  const salvarOrcamento = async (categoriaId, valorOrcado) => {
    if (!projetoAtivo) return;
    try {
      await api.upsertOrcamento(projetoAtivo.id, categoriaId, valorOrcado);
      fetchOrcamentos();
    } catch (err) {
      alert("Erro ao salvar orçamento: " + err.message);
    }
  };

  const fetchEntradas = async () => {
    if (!projetoAtivo) return;
    try {
      const res = await api.getEntradas(projetoAtivo.id);
      setEntradas(res);
    } catch (err) {
      console.error("Erro ao buscar entradas:", err);
    }
  };

  const criarEntrada = async (descricao, valor, data) => {
    if (!projetoAtivo) return;
    try {
      await api.createEntrada(projetoAtivo.id, descricao, valor, data);
      fetchEntradas();
    } catch (err) {
      alert("Erro ao registrar entrada: " + err.message);
    }
  };

  const removerEntrada = async (id) => {
    try {
      await api.deleteEntrada(id);
      fetchEntradas();
    } catch (err) {
      alert("Erro ao remover entrada: " + err.message);
    }
  };

  const addCategoria = async (nome) => {
    if (!projetoAtivo) return;
    try {
      await api.createCategoria(nome, projetoAtivo.id);
      fetchServicos();
    } catch (err) {
      alert(err.message);
    }
  };

  const removeCategoria = async (id) => {
    try {
      await api.deleteCategoria(id);
      fetchServicos();
    } catch (err) {
      alert(err.message);
    }
  };

  const addConta = async (nome) => {
    if (!projetoAtivo) return;
    try {
      await api.createConta(nome, projetoAtivo.id);
      fetchServicos();
    } catch (err) {
      alert(err.message);
    }
  };

  useEffect(() => {
    if (projetoAtivo) {
      fetchDados();
    }
  }, [projetoAtivo]);

  const fetchProjetos = async () => {
    try {
      const res = await api.getProjetos();
      setProjetos(res);
      if (res.length > 0 && !projetoAtivo) {
        setProjetoAtivo(res[0]);
      }
    } catch (e) {
      console.error("Erro ao buscar projetos:", e);
    }
  };

  const fetchDados = async () => {
    if (!projetoAtivo) return;
    try {
      const res = await api.getLancamentos(projetoAtivo.id);
      setDados(res);
    } catch (e) {
      console.error("Erro ao buscar dados:", e);
    }
  };

  const createProject = async (nome, colunas = DEFAULT_COLUMNS) => {
    try {
      const novo = await api.createProjeto({ nome, colunas });
      setProjetos([...projetos, novo]);
      setProjetoAtivo(novo);
      setShowProjectModal(false);
    } catch {
      alert("Erro ao criar projeto");
    }
  };

  const deleteProject = async (id) => {
    try {
      await api.deleteProjeto(id);
      const novosProjetos = projetos.filter(p => p.id !== id);
      setProjetos(novosProjetos);
      setProjetoAtivo(novosProjetos.length > 0 ? novosProjetos[0] : null);
      if (novosProjetos.length === 0) setDados([]);
    } catch {
      alert("Erro ao excluir projeto");
    }
  };

  const filtered = useMemo(() => {
    return dados.filter(d => {
      if(filtros.categoria && d.categoria !== filtros.categoria) return false;
      if(filtros.conta && d.conta !== filtros.conta) return false;
      if(filtros.forma && d.forma !== filtros.forma) return false;
      if(filtros.busca) {
        const b = filtros.busca.toLowerCase();
        // Busca em todos os campos do objeto
        return Object.values(d).some(v => (v||"").toString().toLowerCase().includes(b));
      }
      return true;
    });
  }, [dados, filtros]);

  const totalFiltrado = filtered.reduce((a,d)=>a+parseVal(d.valor),0);

  const porCategoria = useMemo(()=>{
    const m={};
    dados.forEach(d=>{
      const cat = d.categoria || "Outros";
      const v=parseVal(d.valor); 
      m[cat]=(m[cat]||0)+v;
    });
    return Object.entries(m).sort((a,b)=>b[1]-a[1]);
  },[dados]);

  const orcadoRealizado = useMemo(() => {
    const realizadoPorCategoria = Object.fromEntries(porCategoria);
    return orcamentos.map(o => {
      const realizado = realizadoPorCategoria[o.categoria_nome] || 0;
      const orcado = parseVal(o.valor_orcado);
      const percentual = orcado > 0 ? (realizado / orcado) * 100 : 0;
      const status = percentual > 100 ? "estourado" : percentual >= 90 ? "atencao" : "ok";
      return {
        categoriaId: o.categoria_id,
        categoria: o.categoria_nome,
        orcado,
        realizado,
        saldo: orcado - realizado,
        percentual,
        status
      };
    }).sort((a, b) => b.percentual - a.percentual);
  }, [orcamentos, porCategoria]);

  const porConta = useMemo(()=>{
    const m={};
    dados.forEach(d=>{
      const conta = d.conta || "N/A";
      const v=parseVal(d.valor); 
      m[conta]=(m[conta]||0)+v;
    });
    return Object.entries(m).sort((a,b)=>b[1]-a[1]);
  },[dados]);

  const totalGeral = dados.reduce((a,d)=>a+parseVal(d.valor),0);

  const totalEntradas = entradas.reduce((a,e)=>a+parseVal(e.valor),0);
  const saldoCaixa = totalEntradas - totalGeral;

  const handleForm = e => {
    const {name,value} = e.target;
    setForm(f=>{
      const nf = {...f,[name]:value};
      if(name==="quantidade"||name==="unitario"){
        const q=parseFloat(nf.quantidade)||0;
        const u=parseVal(nf.unitario)||0;
        nf.valor = q&&u ? (q*u).toFixed(2) : nf.valor;
      }
      return nf;
    });
  };

  const saveForm = async () => {
    if (!projetoAtivo) return;
    
    // Validação básica se as colunas padrão existirem
    if(projetoAtivo.colunas.some(c => c.name === 'data') && !form.data) {
        return alert("O campo Data é obrigatório.");
    }
    
    try {
      if(editId) {
        const updated = await api.updateLancamento(editId, {
          ...form,
          valor: parseVal(form.valor),
          unitario: parseVal(form.unitario)
        });
        setDados(dados.map(x => x.id === editId ? updated : x));
        setEditId(null);
      } else {
        const novo = await api.createLancamento({
          ...form,
          projeto_id: projetoAtivo.id,
          valor: parseVal(form.valor),
          unitario: parseVal(form.unitario)
        });
        setDados([...dados, novo]);
      }
      setForm({});
      setShowForm(false);
    } catch {
      alert("Erro ao salvar lançamento");
    }
  };

  const startEdit = row => {
    setForm({...row});
    setEditId(row.id);
    setShowForm(true);
    setTab("lancamentos");
  };

  const askConfirm = (config) => {
    setConfirmConfig(config);
  };

  const exportCSV = () => {
    if (!projetoAtivo) return;
    const cols = projetoAtivo.colunas.map(c => c.label);
    const names = projetoAtivo.colunas.map(c => c.name);
    
    const rows = filtered.map(d => names.map(n => {
        let v = d[n] || "";
        if (n === 'valor' || n === 'unitario') v = parseVal(v).toLocaleString("pt-BR",{style:"currency",currency:"BRL"});
        return `"${v}"`;
    }).join(";"));

    const csv="\uFEFF"+[cols.join(";"),...rows].join("\n");
    const a=document.createElement("a");
    a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
    a.download=`despesas_${projetoAtivo.nome.toLowerCase().replace(/ /g,"_")}.csv`;
    a.click();
  };



  const removeConta = async (id) => {
    try {
      await api.deleteConta(id);
      fetchServicos();
    } catch (err) {
      alert(err.message);
    }
  };

  const parseCSV = (content) => {
    const semBom = content.replace(/^\uFEFF/, '');
    const separator = (semBom.split('\n')[0] || "").includes(";") ? ";" : ",";

    const lines = semBom.split(/\r?\n/);
    return lines.map(line => {
      const result = [];
      let current = "";
      let inQuotes = false;
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        const nextChar = line[i+1];
        if (char === '"') {
          if (inQuotes && nextChar === '"') {
            current += '"';
            i++;
          } else {
            inQuotes = !inQuotes;
          }
        } else if (char === separator && !inQuotes) {
          result.push(current.trim().replace(/^"|"$/g, ""));
          current = "";
        } else {
          current += char;
        }
      }
      result.push(current.trim().replace(/^"|"$/g, ""));
      return result;
    }).filter(row => row.some(cell => cell.replace(/[,;]/g, "").trim().length > 0));
  };

  const parseXLSX = (arrayBuffer) => {
    const workbook = XLSX.read(arrayBuffer, { type: "array", cellDates: true });
    const primeiraAba = workbook.Sheets[workbook.SheetNames[0]];
    // raw:true pega o valor NUM\u00C9RICO bruto da c\u00E9lula, sem passar pela formata\u00E7\u00E3o de exibi\u00E7\u00E3o do
    // SheetJS \u2014 que usa v\u00EDrgula como separador de milhar (padr\u00E3o internacional) e conflita com o
    // parseVal do app, que assume formato BR (v\u00EDrgula = decimal). Com raw:false, um valor como
    // 2375 virava a string "2,375", que o parseVal lia como 2.375 (dividido por mil).
    // defval:"" garante c\u00E9lula vazia = "" (n\u00E3o undefined) \u2014 undefined quebraria o hasData abaixo.
    const linhas = XLSX.utils.sheet_to_json(primeiraAba, { header: 1, raw: true, defval: "" });
    return linhas
      .map(row => row.map(cell => {
        if (cell instanceof Date) {
          const dia = String(cell.getDate()).padStart(2, "0");
          const mes = String(cell.getMonth() + 1).padStart(2, "0");
          return `${dia}/${mes}/${cell.getFullYear()}`;
        }
        // Number vira string via String() puro \u2014 sem separador de milhar (ex: 2375, n\u00E3o "2,375") \u2014
        // formato que o parseVal (ramo sem v\u00EDrgula) interpreta corretamente via parseFloat direto.
        return String(cell ?? "").trim();
      }))
      .filter(row => row.some(cell => cell.length > 0));
  };

  const processarLinhasImportadas = async (parsedRows, file) => {
      if (parsedRows.length === 0) return;

      const headers = parsedRows[0].map(h => h.toLowerCase());
      
      let targetProjeto = projetoAtivo;
      
      if (!targetProjeto) {
        // Criar projeto automático baseado nos cabeçalhos
        const colunas = headers.map(h => ({
            name: h.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "_"),
            label: h.charAt(0).toUpperCase() + h.slice(1),
            type: "text"
        }));
        const nome = file.name.split(".")[0];
        try {
            targetProjeto = await api.createProjeto({ nome, colunas });
            setProjetos(prev => [...prev, targetProjeto]);
            setProjetoAtivo(targetProjeto);
        } catch {
            return alert("Erro ao criar projeto automático");
        }
      }

      // Get existing categories/accounts to avoid duplicates
      let existingCats = categoriasDb.map(c => c.nome.toLowerCase());
      let existingCtas = contasDb.map(c => c.nome.toLowerCase());
      const newCatsCreated = new Set();
      const newCtasCreated = new Set();

      let count = 0;
      for(let i = 1; i < parsedRows.length; i++){
        const vals = parsedRows[i];
        const payload = {};
        let hasData = false;
        
        // Mapeamento inteligente: tenta encontrar a coluna pelo nome ou pelo índice
        targetProjeto.colunas.forEach((col, j) => {
            // Tenta encontrar o índice da coluna no CSV pelo nome ou label
            const csvIndex = headers.findIndex(h => 
              h === col.name.toLowerCase() || 
              h === col.label.toLowerCase()
            );
            
            const indexToUse = csvIndex !== -1 ? csvIndex : j;
            const rawVal = vals[indexToUse] || "";
            let val = rawVal;
            if (col.name === 'valor' || col.name === 'unitario') {
              val = parseVal(rawVal);
            }
            payload[col.name] = val;

            // hasData usa o valor BRUTO da célula — parseVal("") vira 0, e "0" não é vazio,
            // então checar o valor já convertido fazia linha em branco (valor/unitário vazios) contar como preenchida.
            if (String(rawVal).trim().length > 0) {
              hasData = true;

              // Auto-criar categorias novas encontradas no CSV
              if (col.name === 'categoria') {
                const name = val.trim();
                if (!existingCats.includes(name.toLowerCase())) {
                  newCatsCreated.add(name);
                  existingCats.push(name.toLowerCase());
                }
              }
              // Auto-criar contas novas encontradas no CSV
              if (col.name === 'conta') {
                const name = val.trim();
                if (!existingCtas.includes(name.toLowerCase())) {
                  newCtasCreated.add(name);
                  existingCtas.push(name.toLowerCase());
                }
              }
            }
        });

        if (!hasData) continue; // Pula se a linha não tiver nenhum dado real

        try {
          await api.createLancamento({ ...payload, projeto_id: targetProjeto.id });
          count++;
        } catch (e) {
          console.error("Erro ao importar linha", i, e);
        }
      }

      // Sincroniza as novas categorias e contas com o banco de dados
      const creations = [];
      newCatsCreated.forEach(cat => creations.push(api.createCategoria(cat, targetProjeto.id)));
      newCtasCreated.forEach(cta => creations.push(api.createConta(cta, targetProjeto.id)));
      
      if (creations.length > 0) {
        await Promise.allSettled(creations);
        fetchServicos();
      }

      fetchDados();
      alert(`${count} registros importados com sucesso!${newCatsCreated.size > 0 ? `\n${newCatsCreated.size} novas categorias criadas.` : ""}`);
  };

  const importFile = e => {
    const file = e.target.files[0]; if(!file) return;
    const ehXlsx = /\.xlsx?$/i.test(file.name);
    const reader = new FileReader();

    reader.onload = async ev => {
      try {
        const parsedRows = ehXlsx ? parseXLSX(ev.target.result) : parseCSV(ev.target.result);
        await processarLinhasImportadas(parsedRows, file);
      } catch (err) {
        console.error("Erro ao importar arquivo:", err);
        alert("Erro ao ler o arquivo. Confira se o formato é CSV ou XLSX válido.");
      }
    };

    if (ehXlsx) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file, "UTF-8");
    }
    e.target.value = "";
  };

  const cats = [...new Set(dados.map(d=>d.categoria || "Outros"))].sort();
  const contas = [...new Set(dados.map(d=>d.conta || "N/A"))].sort();

  return {
    tab, setTab,
    dados, setDados,
    form, setForm,
    showForm, setShowForm,
    editId, setEditId,
    filtros, setFiltros,
    deleteId, setDeleteId,
    fileRef,
    projetos, setProjetos,
    projetoAtivo, setProjetoAtivo,
    showProjectModal, setShowProjectModal,
    createProject,
    deleteProject,
    filtered,
    totalFiltrado,
    porCategoria,
    porConta,
    totalGeral,
    cats,
    contas,
    categoriasDb,
    contasDb,
    addCategoria,
    removeCategoria,
    addConta,
    removeConta,
    fetchServicos,
    requisicoes,
    fetchRequisicoes,
    createRequisicao,
    updateRequisicaoStatus,
    tarefas,
    fetchTarefas,
    createTarefa,
    updateTarefa,
    deleteTarefa,
    usuarios,
    fetchUsuarios,
    orcamentos,
    fetchOrcamentos,
    salvarOrcamento,
    orcadoRealizado,
    entradas,
    fetchEntradas,
    criarEntrada,
    removerEntrada,
    totalEntradas,
    saldoCaixa,
    auditoria,
    fetchAuditoria,
    token,
    setToken,
    logout,
    user,
    setUser,
    confirmConfig, setConfirmConfig,
    askConfirm,
    handleForm,
    saveForm,
    startEdit,
    exportCSV,
    importFile
  };
}
