export const CATEGORIAS = ["Documentação","Terraplanagem","Fundação","Ferramentas","Material de construção","Mão de obra","Mao de obra","Equipamentos/aluguel","Taxas e impostos","Radier Encanamento","Alvenaria","Laje","Telhado","Hidráulica","Elétrica","Encanamento","EPI","Madeireira","Contabilidade","Abertura Empresa","Portas e Batentes","Geral","Imposto","Diversos","Outros"];
export const CONTAS = ["FF Alves Construtora","Victor Praça Pascoal","Vanderlei Almeida Simões","SPE Luiz Pascoal"];
export const FORMAS = ["Pix","Crédito","Débito","Boleto","Dinheiro","Transferência","TED"];

export const EMPTY_FORM = {data:"",categoria:"",item:"",fornecedor:"",quantidade:1,unitario:"",valor:"",forma:"Pix",conta:"",obs:""};

export const CAT_COLORS = {"Documentação":"#7c3aed","Terraplanagem":"#d97706","Fundação":"#dc2626","Ferramentas":"#2563eb","Material de construção":"#16a34a","Mão de obra":"#0891b2","Equipamentos/aluguel":"#ea580c","Taxas e impostos":"#be185d","Outros":"#64748b"};

export const BAR_COLORS = ["#2563eb","#16a34a","#dc2626","#d97706","#7c3aed","#0891b2","#be185d","#65a30d","#ea580c"];

export const DEFAULT_COLUMNS = [
  { name: "data", label: "Data", type: "text" },
  { name: "categoria", label: "Categoria", type: "select", options: CATEGORIAS },
  { name: "item", label: "Item / Descrição", type: "text", fullWidth: true },
  { name: "fornecedor", label: "Fornecedor", type: "text", fullWidth: true },
  { name: "quantidade", label: "Qtd", type: "number" },
  { name: "unitario", label: "Unitário (R$)", type: "text" },
  { name: "valor", label: "Valor Pago (R$)", type: "text", fullWidth: true },
  { name: "forma", label: "Forma", type: "select", options: FORMAS },
  { name: "conta", label: "Conta", type: "select", options: CONTAS },
  { name: "obs", label: "Observações", type: "textarea", fullWidth: true }
];

