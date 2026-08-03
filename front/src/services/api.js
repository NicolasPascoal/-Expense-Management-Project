const API_URL = import.meta.env.VITE_API_URL || '/api';

const getHeaders = () => {
  const token = sessionStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
};

async function callApi(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { ...getHeaders(), ...options.headers }
  });

  if (response.status === 401) {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    window.dispatchEvent(new Event('auth-error'));
    throw new Error('Sessão expirada. Faça login novamente.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.erro || `Erro na requisição: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth
  async login(username, password) {
    const data = await callApi(`${API_URL}/login`, {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    sessionStorage.setItem('token', data.token);
    sessionStorage.setItem('user', JSON.stringify(data.user));
    return data;
  },

  async signup(nomeEmpresa, username, password, colunas) {
    const data = await callApi(`${API_URL}/signup`, {
      method: 'POST',
      body: JSON.stringify({ nome_empresa: nomeEmpresa, username, password, colunas })
    });
    sessionStorage.setItem('token', data.token);
    sessionStorage.setItem('user', JSON.stringify(data.user));
    return data;
  },

  // Lançamentos
  async getLancamentos(projetoId) {
    const url = projetoId ? `${API_URL}/lancamentos?projeto_id=${projetoId}` : `${API_URL}/lancamentos`;
    return callApi(url);
  },

  async createLancamento(dados) {
    return callApi(`${API_URL}/lancamentos`, {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },

  async updateLancamento(id, dados) {
    return callApi(`${API_URL}/lancamentos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados)
    });
  },

  async deleteLancamento(id) {
    return callApi(`${API_URL}/lancamentos/${id}`, {
      method: 'DELETE'
    });
  },

  // Projetos
  async getProjetos() {
    return callApi(`${API_URL}/projetos`);
  },

  async createProjeto(dados) {
    return callApi(`${API_URL}/projetos`, {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },

  async updateProjeto(id, dados) {
    return callApi(`${API_URL}/projetos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados)
    });
  },

  async deleteProjeto(id) {
    return callApi(`${API_URL}/projetos/${id}`, {
      method: 'DELETE'
    });
  },

  // Categorias
  async getCategorias(projetoId) {
    const url = projetoId ? `${API_URL}/categorias?projeto_id=${projetoId}` : `${API_URL}/categorias`;
    return callApi(url);
  },

  async createCategoria(nome, projetoId) {
    return callApi(`${API_URL}/categorias`, {
      method: 'POST',
      body: JSON.stringify({ nome, projeto_id: projetoId })
    });
  },

  async deleteCategoria(id) {
    return callApi(`${API_URL}/categorias/${id}`, {
      method: 'DELETE'
    });
  },

  // Contas
  async getContas(projetoId) {
    const url = projetoId ? `${API_URL}/contas?projeto_id=${projetoId}` : `${API_URL}/contas`;
    return callApi(url);
  },

  async createConta(nome, projetoId) {
    return callApi(`${API_URL}/contas`, {
      method: 'POST',
      body: JSON.stringify({ nome, projeto_id: projetoId })
    });
  },

  async deleteConta(id) {
    return callApi(`${API_URL}/contas/${id}`, {
      method: 'DELETE'
    });
  },

  // Usuários (Admin)
  async getUsuarios() {
    return callApi(`${API_URL}/usuarios`);
  },

  async createUsuario(username, password, is_admin, role = 'prestador') {
    return callApi(`${API_URL}/usuarios`, {
      method: 'POST',
      body: JSON.stringify({ username, password, is_admin, role })
    });
  },

  async deleteUsuario(id) {
    return callApi(`${API_URL}/usuarios/${id}`, {
      method: 'DELETE'
    });
  },

  // Requisições de Materiais
  async getRequisicoes() {
    return callApi(`${API_URL}/requisicoes`);
  },

  async createRequisicao(dados) {
    return callApi(`${API_URL}/requisicoes`, {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },

  async updateRequisicaoStatus(id, status) {
    return callApi(`${API_URL}/requisicoes/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status })
    });
  },

  // Tarefas
  async getTarefas() {
    return callApi(`${API_URL}/tarefas`);
  },

  async createTarefa(dados) {
    return callApi(`${API_URL}/tarefas`, {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },

  async updateTarefa(id, dados) {
    return callApi(`${API_URL}/tarefas/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dados)
    });
  },

  async deleteTarefa(id) {
    return callApi(`${API_URL}/tarefas/${id}`, {
      method: 'DELETE'
    });
  },

  // Orçamentos
  async getOrcamentos(projetoId) {
    const url = projetoId ? `${API_URL}/orcamentos?projeto_id=${projetoId}` : `${API_URL}/orcamentos`;
    return callApi(url);
  },

  async upsertOrcamento(projetoId, categoriaId, valorOrcado) {
    return callApi(`${API_URL}/orcamentos`, {
      method: 'POST',
      body: JSON.stringify({ projeto_id: projetoId, categoria_id: categoriaId, valor_orcado: valorOrcado })
    });
  },

  async deleteOrcamento(id) {
    return callApi(`${API_URL}/orcamentos/${id}`, {
      method: 'DELETE'
    });
  },

  // Fluxo de Caixa (Entradas)
  async getEntradas(projetoId) {
    const url = projetoId ? `${API_URL}/entradas?projeto_id=${projetoId}` : `${API_URL}/entradas`;
    return callApi(url);
  },

  async createEntrada(projetoId, descricao, valor, data) {
    return callApi(`${API_URL}/entradas`, {
      method: 'POST',
      body: JSON.stringify({ projeto_id: projetoId, descricao, valor, data })
    });
  },

  async deleteEntrada(id) {
    return callApi(`${API_URL}/entradas/${id}`, {
      method: 'DELETE'
    });
  },

  // Auditoria
  async getAuditoria() {
    return callApi(`${API_URL}/auditoria`);
  }
};
