import { fmt, parseVal } from "../utils/format";
import { inputStyle, btnStyle, td, catColor } from "../utils/styles";
import { Search, Pencil, Trash2 } from "lucide-react";

export function LancamentosTab({
  projetoAtivo,
  filtered,
  filtros,
  setFiltros,
  cats,
  contas,
  totalFiltrado,
  startEdit,
  askConfirm,
  setDados,
  dados
}) {
  if (!projetoAtivo) return null;

  const colunas = projetoAtivo.colunas || [];

  return (
    <>
      <div className="filtros-bar">
        <div className="filtro-item">
          <div className="filtro-label" style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <Search size={14} /> Buscar
          </div>
          <input value={filtros.busca} onChange={e=>setFiltros(f=>({...f,busca:e.target.value}))} placeholder="Busca geral..." style={{...inputStyle,margin:0}}/>
        </div>
        
        {/* Filtros fixos (Categoria, Conta, Forma) se existirem no projeto */}
        {colunas.some(c => c.name === 'categoria') && (
          <div className="filtro-item">
            <div className="filtro-label">Categoria</div>
            <select value={filtros.categoria} onChange={e=>setFiltros(f=>({...f,categoria:e.target.value}))} style={{...inputStyle,margin:0}}>
              <option value="">Todas</option>
              {cats.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
        )}

        {colunas.some(c => c.name === 'conta') && (
          <div className="filtro-item">
            <div className="filtro-label">Conta Pagadora</div>
            <select value={filtros.conta} onChange={e=>setFiltros(f=>({...f,conta:e.target.value}))} style={{...inputStyle,margin:0}}>
              <option value="">Todas</option>
              {contas.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
        )}

        <button onClick={()=>setFiltros({categoria:"",conta:"",forma:"",busca:""})} style={{...btnStyle("#64748b"),height:38}}>Limpar</button>
      </div>

      <div style={{background:"#1e3a5f",color:"#fff",borderRadius:10,padding:"12px 16px",marginBottom:12,display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:8}}>
        <span style={{fontSize:14}}>{filtered.length} registro(s) encontrado(s)</span>
        <span style={{fontWeight:700,fontSize:18}}>{fmt(totalFiltrado)}</span>
      </div>

      <div className="table-wrap">
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
          <thead>
            <tr style={{background:"#f8fafc",borderBottom:"2px solid #e2e8f0"}}>
              {colunas.map(col => (
                <th key={col.name} style={{padding:"10px 12px",textAlign:"left",whiteSpace:"nowrap",color:"#475569",fontWeight:600,fontSize:12}}>
                  {col.label}
                </th>
              ))}
              <th style={{padding:"10px 12px"}}></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length===0 && (
              <tr><td colSpan={colunas.length + 1} style={{textAlign:"center",padding:32,color:"#94a3b8"}}>Nenhum lançamento encontrado.</td></tr>
            )}
            {filtered.map((d,i)=>(
              <tr key={d.id} style={{borderBottom:"1px solid #f1f5f9",background:i%2===0?"#fff":"#f8fafc"}}>
                {colunas.map(col => {
                  const val = d[col.name];
                  
                  if (col.name === 'categoria') {
                    return (
                      <td key={col.name} style={td}>
                        <span style={{background:catColor(val)+"22",color:catColor(val),borderRadius:4,padding:"2px 7px",fontSize:11,fontWeight:600}}>
                          {val || "Outros"}
                        </span>
                      </td>
                    );
                  }

                  if (col.name === 'valor' || col.name === 'unitario') {
                    return (
                      <td key={col.name} style={{...td, fontWeight: col.name === 'valor' ? 600 : 400, color: col.name === 'valor' ? "#1e3a5f" : "inherit"}}>
                        {fmt(parseVal(val))}
                      </td>
                    );
                  }

                  return (
                    <td key={col.name} style={{...td, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis"}}>
                      {val}
                    </td>
                  );
                })}
                <td style={td}>
                  <div style={{display:"flex",gap:4}}>
                    <button onClick={()=>startEdit(d)} style={{border:"none",background:"#dbeafe",color:"#2563eb",borderRadius:4,padding:"4px",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center"}} title="Editar">
                      <Pencil size={14} />
                    </button>
                    <button onClick={() => {
                      askConfirm({
                        title: "Excluir lançamento?",
                        message: "Esta ação não pode ser desfeita.",
                        icon: <Trash2 size={20} color="#ef4444" />,
                        confirmText: "Excluir",
                        onConfirm: async () => {
                          try {
                            const { api } = await import("../services/api");
                            await api.deleteLancamento(d.id);
                            setDados(dados.filter(x => x.id !== d.id));
                          } catch {
                            alert("Erro ao excluir lançamento");
                          }
                        }
                      });
                    }} style={{border:"none",background:"#fee2e2",color:"#dc2626",borderRadius:4,padding:"4px",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center"}} title="Excluir">
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
