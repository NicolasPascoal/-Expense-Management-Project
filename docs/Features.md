# Features — Expense Management Project

Este documento inventaria o que está **efetivamente implementado** no código hoje, módulo a módulo, e cruza com o roadmap declarado pelo próprio autor (`front/freatures.txt`) para deixar explícito o que já existe versus o que é intenção futura conhecida.

## 1. Autenticação e Sessão

| Feature | Status |
|---|---|
| Login com usuário/senha | ✅ Implementado |
| Token JWT com expiração de 24h | ✅ Implementado |
| Logout manual | ✅ Implementado |
| Logout automático por inatividade (15 min) | ✅ Implementado (client-side) |
| Redirecionamento automático ao expirar token (401) | ✅ Implementado |
| Recuperação de senha ("esqueci minha senha") | ❌ Não implementado |
| Autenticação multifator (2FA) | ❌ Não implementado |
| Login social/SSO | ❌ Não implementado (fora de escopo aparente) |

## 2. Gestão de Usuários e Permissões

| Feature | Status |
|---|---|
| CRUD básico de usuário (criar, listar, excluir) | ✅ Implementado |
| Dois papéis funcionais: admin e prestador | ✅ Implementado |
| Proteção do usuário `id=1` contra exclusão | ✅ Implementado |
| Sistema de permissões granular (admin, gestor de obra, financeiro, pedreiro) | ⚠️ Parcial/roadmap — hoje só existem `admin` e `prestador`; `freatures.txt` lista os quatro papéis como objetivo futuro |
| Permissões por ação (não só por tipo de usuário) | ❌ Não implementado — roadmap declarado |
| Edição de usuário existente (trocar senha, promover/rebaixar) | ❌ Não implementado — só criar e excluir; não há endpoint de `PUT /usuarios/:id` |

## 3. Projetos / Obras

| Feature | Status |
|---|---|
| Múltiplos projetos simultâneos | ✅ Implementado |
| Schema de campos dinâmico por projeto | ✅ Implementado (via `colunas` em JSON) |
| Seletor de projeto ativo na UI | ✅ Implementado |
| Criação de projeto automática a partir de import de CSV | ✅ Implementado |
| Controle de acesso por obra (usuário só vê as obras dele) | ❌ Não implementado — roadmap declarado ("controle de acesso por obra") |
| Orçamento por obra (valor orçado) | ❌ Não implementado — roadmap declarado |
| Comparação orçado vs. realizado | ❌ Não implementado — roadmap declarado |
| Alerta de estouro de orçamento | ❌ Não implementado — roadmap declarado |

## 4. Lançamentos Financeiros

| Feature | Status |
|---|---|
| CRUD de lançamentos | ✅ Implementado |
| Filtro por categoria/conta/forma/busca textual | ✅ Implementado (client-side) |
| Cálculo automático de valor (quantidade × unitário) | ✅ Implementado |
| Exportação para CSV | ✅ Implementado |
| Importação de CSV (com criação automática de categorias/contas/projeto) | ✅ Implementado |
| Dashboard com totais por categoria/conta (gráficos) | ✅ Implementado (via Recharts, cálculo client-side) |
| Anexar recibos/imagens ao lançamento | ❌ Não implementado — roadmap declarado |
| Histórico de edição / auditoria (quem criou, quem editou) | ❌ Não implementado — roadmap declarado |
| Parcelamento (dividir pagamento em parcelas) | ❌ Não implementado — roadmap declarado |
| Controle de parcelas (pendente/pago/atrasado) | ❌ Não implementado — roadmap declarado |
| Fluxo de caixa (entradas, saídas, saldo por obra e geral) | ❌ Não implementado — roadmap declarado (o sistema atual só rastreia saídas/despesas, não há conceito de "entrada" de caixa) |
| Relatório comparativo entre obras | ❌ Não implementado — roadmap declarado |
| Relatório de evolução de gastos no tempo | ⚠️ Parcial — o dashboard mostra totais agregados atuais, mas não uma série temporal explícita de evolução |

## 5. Categorias e Contas

| Feature | Status |
|---|---|
| CRUD de categorias por projeto | ✅ Implementado |
| CRUD de contas pagadoras por projeto | ✅ Implementado |
| Conta pagadora / forma de pagamento / centro de custo (=obra) | ✅ Implementado — o próprio `projeto_id` já funciona como "centro de custo" |

## 6. Requisições de Material

| Feature | Status |
|---|---|
| Criação de pedido (nome, função, material) | ✅ Implementado |
| Consulta de status do próprio pedido | ✅ Implementado |
| Histórico de pedidos (do próprio usuário) | ✅ Implementado |
| Aprovação/recusa por gestor/admin | ⚠️ Parcial — existe alteração de `status` livre (qualquer string), mas não há um fluxo estruturado com valores fixos "aprovado"/"recusado" impostos pelo backend, nem transições de estado validadas |
| Anexar foto ao pedido | ❌ Não implementado — roadmap declarado |
| Gerar lançamento financeiro automático ao aprovar | ❌ Não implementado — roadmap declarado |
| Vincular pedido a uma obra específica | ❌ Não implementado — roadmap declarado (requisições não têm `projeto_id`) |
| Fluxo dedicado e restrito para "pedreiro" (acesso só à tela de pedidos) | ⚠️ Parcial — o papel `prestador` já tem acesso restrito a Tarefas + Requisições, mas o roadmap fala especificamente de um papel "pedreiro" dentro de um sistema de 4 papéis, que ainda não existe como tal |

## 7. Tarefas

| Feature | Status |
|---|---|
| Criação de tarefa por admin, atribuída a um prestador | ✅ Implementado |
| Visualização de tarefas próprias (prestador) / todas (admin) | ✅ Implementado |
| Atualização de status/observações pelo prestador dono | ✅ Implementado |
| Edição completa pelo admin | ✅ Implementado |
| Exclusão de tarefa (admin) | ✅ Implementado |
| Notificações (ex.: avisar prestador de nova tarefa) | ❌ Não implementado |

## 8. Infraestrutura e Banco de Dados

| Feature | Status |
|---|---|
| PostgreSQL como banco principal | ✅ Implementado |
| JSONB para campos dinâmicos | ❌ Não implementado — hoje usa `TEXT` com `json.dumps` manual (roadmap declarado: "usar JSONB") |
| ORM (SQLAlchemy) | ❌ Não implementado — roadmap declarado |
| Migrations versionadas (Alembic) | ❌ Não implementado — roadmap declarado; hoje só scripts avulsos (`migrate_to_v2.py`, etc.) |
| Banco gerenciado (Supabase/Railway) | ⚠️ Não verificável a partir do repositório — o `docker-compose.yml` sobe um Postgres local em container; se há um banco gerenciado em produção real, isso está fora do escopo do que este repositório documenta |
| Backup automático | ❌ Não implementado/não documentado no repositório |
| Containerização (Docker Compose) | ✅ Implementado — backend, frontend e banco |

## 9. Segurança (itens do roadmap do autor)

| Feature | Status |
|---|---|
| Controle de acesso por obra | ❌ Não implementado — roadmap declarado |
| Permissões por ação | ❌ Não implementado — roadmap declarado |
| Log de ações / auditoria completa | ❌ Não implementado — roadmap declarado |
| Segredos fora do controle de versão | ❌ Não implementado — ver `Security.md` (segredos reais commitados no Git) |

## 10. Resumo quantitativo

- **Módulos com CRUD completo e funcional**: Lançamentos, Projetos, Categorias, Contas, Usuários, Tarefas, Requisições (7 módulos).
- **Itens do roadmap do autor (`freatures.txt`) já concluídos**: migração para PostgreSQL (parcial — sem JSONB/ORM/migrations).
- **Itens do roadmap do autor ainda não iniciados**: sistema de permissões de 4 papéis, geração automática de lançamento a partir de requisição aprovada, anexos de recibo/foto, auditoria/histórico de edição, parcelamento, orçamento vs. realizado, fluxo de caixa (entradas), relatórios comparativos entre obras, controle de acesso por obra, JSONB, ORM, migrations, banco gerenciado com backup automático.

Esse cruzamento demonstra que a maior parte das lacunas de features encontradas nesta documentação **já é de conhecimento do autor**, documentada por ele mesmo como trabalho futuro — o valor deste documento é consolidar isso de forma estruturada e verificável contra o estado real do código, não apontar problemas desconhecidos.
