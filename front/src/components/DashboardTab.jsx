import { useState } from "react";
import { Card } from "./Card";
import { fmt, parseVal } from "../utils/format";
import { BAR_COLORS } from "../data/constants";
import { DollarSign, ClipboardList, Tag, Users, BarChart3, PieChart as PieChartIcon } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Label } from "recharts";

export function DashboardTab({ totalGeral, dados, porCategoria, porConta }) {
  const [chartType, setChartType] = useState("pie");

  const chartData = porCategoria.map(([name, value]) => ({
    name,
    value: parseVal(value)
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ background: "#fff", padding: "10px", border: "1px solid #ccc", borderRadius: 8, boxShadow: "0 2px 4px rgba(0,0,0,0.1)" }}>
          <p style={{ margin: 0, fontWeight: 700, fontSize: 13 }}>{payload[0].name}</p>
          <p style={{ margin: 0, color: "#1e3a5f", fontSize: 14 }}>{fmt(payload[0].value)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{display:"grid",gap:16}}>
      <div className="cards-grid">
        <Card title="Total Geral" value={fmt(totalGeral)} icon={<DollarSign size={20} />} color="#1e3a5f"/>
        <Card title="Lançamentos" value={dados.length} icon={<ClipboardList size={20} />} color="#2563eb"/>
        <Card title="Categorias" value={porCategoria.length} icon={<Tag size={20} />} color="#16a34a"/>
        <Card title="Contas" value={porConta.length} icon={<Users size={20} />} color="#7c3aed"/>
      </div>

      <div style={{background:"#fff",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,.08)"}}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
          <b style={{fontSize:15, display: "flex", alignItems: "center", gap: 8 }}>
            {chartType === "bar" ? <BarChart3 size={18} /> : <PieChartIcon size={18} />} 
            Gastos por Categoria
          </b>
          
          <div style={{ display: "flex", background: "#f1f5f9", padding: 4, borderRadius: 8 }}>
            <button 
              onClick={() => setChartType("bar")}
              style={{
                border: "none",
                background: chartType === "bar" ? "#fff" : "transparent",
                color: chartType === "bar" ? "#1e3a5f" : "#64748b",
                padding: "6px 12px",
                borderRadius: 6,
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                boxShadow: chartType === "bar" ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
                transition: "all 0.2s"
              }}
            >
              <BarChart3 size={14} /> Barras
            </button>
            <button 
              onClick={() => setChartType("pie")}
              style={{
                border: "none",
                background: chartType === "pie" ? "#fff" : "transparent",
                color: chartType === "pie" ? "#1e3a5f" : "#64748b",
                padding: "6px 12px",
                borderRadius: 6,
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                boxShadow: chartType === "pie" ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
                transition: "all 0.2s"
              }}
            >
              <PieChartIcon size={14} /> Pizza
            </button>
          </div>
        </div>

        <div style={{ 
          display: "grid", 
          gridTemplateColumns: chartType === "pie" ? "repeat(auto-fit, minmax(400px, 1fr))" : "1fr", 
          gap: 32, 
          alignItems: "center" 
        }}>
          {chartType === "pie" && (
            <div style={{ height: 500, minHeight: 500, width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={100}
                    outerRadius={180}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                    ))}
                    <Label 
                      value={fmt(totalGeral)} 
                      position="center" 
                      style={{ fontSize: '20px', fontWeight: 'bold', fill: '#1e3a5f', fontFamily: 'system-ui' }} 
                    />
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          <div 
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 12, 
              flex: 1,
              maxHeight: 500,
              overflowY: "auto",
              paddingRight: 8
            }}
            className="custom-scrollbar"
          >
            {porCategoria.map(([cat,val],i)=>{
              const pct = totalGeral>0?val/totalGeral*100:0;
              return (
                <div key={cat} style={{ 
                  background: chartType === "pie" ? "#f8fafc" : "transparent", 
                  padding: chartType === "pie" ? "10px 14px" : 0, 
                  borderRadius: 8,
                  border: chartType === "pie" ? "1px solid #f1f5f9" : "none"
                }}>
                  <div style={{display:"flex",justifyContent:"space-between",fontSize:13,marginBottom:6,flexWrap:"wrap",gap:4, alignItems: "center"}}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {chartType === "pie" && <div style={{ width: 10, height: 10, borderRadius: "50%", background: BAR_COLORS[i % BAR_COLORS.length] }} />}
                      <span style={{fontWeight: 600, color: "#334155"}}>{cat}</span>
                    </div>
                    <span style={{color:"#1e3a5f",fontWeight:700}}>{fmt(val)} <span style={{color:"#94a3b8",fontWeight:400, fontSize: 11}}>({pct.toFixed(1)}%)</span></span>
                  </div>
                  <div style={{background:"#f1f5f9",borderRadius:999,height: chartType === "pie" ? 6 : 10}}>
                    <div style={{background:BAR_COLORS[i%BAR_COLORS.length],width:pct+"%",height:"100%",borderRadius:999,transition:"width .4s"}}/>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
