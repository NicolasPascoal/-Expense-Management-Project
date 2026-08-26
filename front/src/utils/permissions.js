// Papéis expandidos (Tarefa 6.1) — espelha back/app/utils/permissions.py.
// 'gestor_obra' não tem "acesso_financeiro" de propósito: a Tarefa 6.2 é quem
// vai restringir isso por obra gerenciada.
export const PERMISSOES_POR_PAPEL = {
  financeiro: new Set(["acesso_financeiro"]),
  gestor_obra: new Set(["aprovar_requisicoes", "gerenciar_tarefas"]),
  prestador: new Set(),
};

export function can(user, permissao) {
  if (user?.is_admin) return true;
  return (PERMISSOES_POR_PAPEL[user?.role] || new Set()).has(permissao);
}
