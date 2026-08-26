"""
Papéis expandidos (Tarefa 6.1, ver STATUS.md): cada papel não-admin tem um
conjunto explícito de permissões — substitui o antigo padrão "libera tudo
exceto prestador" por uma lista de permissão positiva, mais segura por
padrão (um papel desconhecido não ganha acesso nenhum).

'gestor_obra' não tem 'acesso_financeiro' de propósito: a Tarefa 6.2 (ainda
não implementada) é quem vai restringir esse acesso por obra gerenciada —
conceder acesso financeiro amplo agora teria que ser revogado depois.
"""

PERMISSOES_POR_PAPEL = {
    'financeiro': {'acesso_financeiro'},
    'gestor_obra': {'aprovar_requisicoes', 'gerenciar_tarefas'},
    'prestador': set(),
}


def tem_permissao(user, permissao):
    """is_admin sempre passa (autoridade máxima); caso contrário, checa o
    conjunto de permissões do papel. Papel desconhecido nunca tem permissão."""
    if user.get('is_admin'):
        return True
    return permissao in PERMISSOES_POR_PAPEL.get(user.get('role'), set())
