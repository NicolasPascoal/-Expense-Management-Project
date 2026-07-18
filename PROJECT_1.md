# PROJECT.md

Este arquivo descreve **como o sistema funciona** — arquitetura, banco de dados, armadilhas do código, roadmap e convenções. Para saber **como o Claude deve se comportar** ao trabalhar neste repositório (fluxo obrigatório, filosofia, definição de pronto), veja `CLAUDE.md`. Leia este arquivo antes de propor ou executar qualquer mudança.

---

## O que é este projeto

Sistema de **gestão financeira de obras de construção civil** ("Expense Management"). Hoje é uma ferramenta de uso interno de uma única construtora/obra; está em transformação deliberada para um **SaaS comercial multi-cliente** (ver seção "Roadmap" abaixo e `docs/Roadmap-SaaS-Construtoras.md`).

Stack: **Flask 3 (Python) + PostgreSQL** no backend, **React 19 + Vite** no frontend, orquestrados via **Docker Compose**.

## Mapa da documentação (`/docs`)

Documentação detalhada gerada por engenharia reversa. **Consulte antes de assumir qualquer comportamento do sistema** — leia só a seção relevante para a tarefa, não o conjunto inteiro:

| Dúvida sobre... | Consulte |
|---|---|
| Visão de produto/negócio | `docs/ProjectOverview.md` |
| Padrões arquiteturais e por quê | `docs/Architecture.md` |
| Onde fica cada coisa | `docs/FolderStructure.md` |
| Banco de dados, conexão, migrations | `docs/Database.md` |
| Tabelas, relacionamentos, ERD | `docs/Entities.md` |
| Contratos de endpoint | `docs/API.md` |
| Regras de negócio por módulo | `docs/BusinessRules.md` |
| Login/JWT/sessão | `docs/Authentication.md` |
| RBAC e lacunas de autorização | `docs/Authorization.md` |
| O que existe vs. roadmap | `docs/Features.md` |
| Dependências e motivo de cada uma | `docs/Dependencies.md` |
| Riscos de segurança conhecidos | `docs/Security.md` |
| Gargalos de performance | `docs/Performance.md` |
| Dívida técnica mapeada | `docs/TechDebt.md` |
| Como rodar o projeto (detalhado) | `docs/DevelopmentFlow.md` |
| Roadmap estratégico de SaaS (épicos/tarefas priorizadas) | `docs/Roadmap-SaaS-Construtoras.md` |
| Decisões técnicas travadas e decisões de negócio pendentes | `docs/Decisions.md` |
| Estado atual de cada tarefa do roadmap (feito/em andamento/bloqueado) | `STATUS.md` (raiz do projeto) |

**Se uma tarefa pedida se encaixa em algum item desses documentos, alinhe a implementação ao que já está descrito ali em vez de redescobrir do zero.** Antes de iniciar qualquer tarefa do roadmap, confira `STATUS.md` para não retrabalhar algo já feito, e `docs/Decisions.md` para não reabrir uma decisão já travada nem decidir sozinho algo marcado como pendente.

## Comandos

### Backend (`back/`)
```bash
cp back/.env.example back/.env    # preencher com valores reais locais — nunca commitar depois de preenchido
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # sempre usar --break-system-packages se fora de venv
python main.py                            # sobe em :5000 (Waitress se FLASK_DEBUG=False, Flask dev-server se True)
```
Scripts administrativos avulsos (executar manualmente, nunca são chamados pela aplicação):
```bash
python create_admin.py            # cria/atualiza um admin com credenciais fixas no arquivo — NÃO reutilizar em produção sem trocar as credenciais
python seed_db.py                 # popula a tabela legada 'lancamentos' a partir de front/src/data/data.json
python migrate_to_v2.py           # migra 'lancamentos' -> 'lancamentos_v2' (schema dinâmico)
python check_db.py / verify_db.py # diagnóstico manual (print no console, não são testes)
```

### Frontend (`front/`)
```bash
npm install
npm run dev       # Vite dev server, :5173, com proxy /api -> VITE_API_PROXY_TARGET
npm run lint      # única ferramenta de qualidade estática do repo (não há linter de backend)
npm run build
```

### Tudo junto (Docker)
```bash
docker compose up --build     # sobe db_postgres, backend (:5000) e frontend (:3050)
```

### Testes
**Não existem testes automatizados neste repositório** (nem backend nem frontend). Se a tarefa envolve lógica de autorização, multi-tenancy ou cálculo financeiro, escreva testes ao mexer nesse código — não assuma que o comportamento atual está coberto por rede de segurança nenhuma.

## Arquitetura atual (estado real do código)

```
React SPA (Vite/Nginx) --fetch/JSON+JWT Bearer--> Flask (routes/ -> controller/ -> database/) --psycopg2--> PostgreSQL
```

- **Backend**: `routes/` (Blueprints, só HTTP + decorators) → `controller/` (regra de negócio + SQL direto, sem ORM, sem Services/Repositories ainda) → `database/` (conexão + DDL). **Nem todo módulo segue esse padrão**: `projeto_routes.py` e parte de `requisicao_routes.py` acessam o banco direto na rota, sem controller — ao mexer nesses arquivos, não assuma que a lógica está isolada em outro lugar.
- **Frontend**: um único hook (`hooks/useExpenses.js`, ~570 linhas) concentra todo o estado e lógica de negócio do app inteiro; componentes em `components/` são majoritariamente "burros" e recebem tudo via props espalhadas (`{...expenses}`). Não há Redux/Context/React Query/React Router/estrutura de Pages-Features ainda.
- Detalhes completos e o porquê de cada decisão: `docs/Architecture.md`.

## Arquitetura alvo (direção de evolução, não mandato de reescrita)

**Backend**
```
Routes
  ↓
Controllers
  ↓
Services
  ↓
Repositories
  ↓
Database
```

**Frontend**
```
Pages
  ↓
Features
  ↓
Components
  ↓
Hooks
  ↓
API
  ↓
Types
  ↓
Utils
```

Ao adicionar lógica de negócio nova relevante no backend, considere introduzir a camada de `Services` **apenas para o módulo em questão** — não force a criação de `Repositories` para uma tarefa que não precisa tocar acesso a dados de forma isolada. No frontend, ao adicionar uma feature nova, prefira criar um hook dedicado para aquele domínio em vez de inflar ainda mais `useExpenses.js`. Veja `CLAUDE.md` (seção "Filosofia") para a regra de como tratar essa direção durante uma tarefa pontual.

## Coisas que vão te confundir se você não souber de antemão

1. **`app/database/db.py` faz o Postgres fingir ser SQLite.** Toda query no código usa `?` como placeholder (não `%s`), depende de `cursor.lastrowid` (não `RETURNING`), e comandos `PRAGMA` são silenciosamente ignorados. Isso é proposital (herança de uma migração de SQLite→Postgres) — **se escrever uma query nova, siga esse padrão** até que a introdução de um ORM (item do roadmap) seja executada como tarefa própria.
2. **`lancamentos_v2.dados` e `projetos.colunas` são JSON dentro de uma coluna `TEXT`**, não `JSONB`. Cada projeto define seu próprio schema dinâmico de campos (`colunas`), e cada lançamento guarda seus valores serializados em `dados`. Não há validação de tipo/obrigatoriedade no banco nem no backend — se for adicionar uma validação, ela precisa ser escrita manualmente.
3. **Existem duas tabelas de lançamento**: `lancamentos` (legada, schema fixo, sem `projeto_id`, não usada por nenhuma rota ativa) e `lancamentos_v2` (ativa, schema dinâmico). Se a tarefa é sobre lançamentos, é quase certo que é sobre `lancamentos_v2`.
4. **`is_admin` (inteiro 0/1) e `role` (string) coexistem** na tabela `usuarios`, de forma parcialmente redundante. A autorização real hoje é decidida por `is_admin`, não por `role`. Existe um terceiro valor de `role` (`'user'`) alcançável pela UI de admin que **não tem nenhuma regra de autorização própria** no backend.
5. **Isolamento multi-tenant implementado desde a Tarefa 1.2 do roadmap SaaS.** Toda leitura (lançamentos, categorias, contas, projetos, tarefas, requisições, usuários) filtra por `empresa_id` do token; toda escrita/edição/exclusão por id valida posse antes de agir (`404` se o recurso é de outra empresa, `400` se a criação referencia um `projeto_id`/`prestador_id` de outra empresa). `categorias`/`contas`/`lancamentos_v2` chegam a `empresa_id` via join com `projetos`; `tarefas`/`requisicoes_materiais`, via join com `usuarios`. Isso **não** cobre a lacuna de autorização por role em lançamentos/categorias/contas (um `prestador` autenticado ainda pode alterar dados financeiros dentro da própria empresa) — isso é a Tarefa 1.3, ainda não implementada.
6. **Dois decorators de autorização, agora com contrato equivalente**: `@token_required` e `@admin_required` populam `g.user` com o payload completo do token (desde a Tarefa 1.1 do roadmap SaaS — antes, `@admin_required` só validava `is_admin` e descartava o payload; isso quebrava rotas que precisavam de `g.user['empresa_id']`, como criação de usuário/projeto). Continuam sendo dois decorators redundantes (cada um decodifica o token de novo, de forma independente) — unificá-los é escopo da Tarefa 1.3.
7. **Segredos reais estão (ou estiveram) commitados no histórico do Git** (`back/.env`, credenciais em `create_admin.py`). Ver `docs/Security.md`. Nunca reintroduza um segredo real em um arquivo versionado.
8. **`id=1` em `usuarios` é meta-protegido contra exclusão** em duas camadas (controller e UI) — não remova essa checagem sem que seja o objetivo explícito da tarefa.
9. **`ON DELETE CASCADE` é usado amplamente** (projeto → categorias/contas/lançamentos; usuário → tarefas/requisições). Excluir um projeto ou usuário é destrutivo e irreversível — não implemente exclusão sem confirmação explícita no fluxo, e considere se a tarefa pede soft-delete em vez de exclusão física.
10. **Sem paginação em nenhum endpoint de listagem**, e agregações financeiras (totais por categoria/conta) são calculadas inteiramente no frontend, iterando todos os registros. Ver `docs/Performance.md` antes de assumir que dá para simplesmente "adicionar mais um campo" sem pensar em custo de escala.

## Roadmap (resumo — ver `docs/Roadmap-SaaS-Construtoras.md` para o detalhamento completo)

O projeto está sendo transformado em SaaS comercial, em fases sequenciais:

- **Fase 0 (Fundação, P0)**: multi-tenancy real, remoção de segredos expostos, fechamento de lacunas de autorização, ORM/migrations, testes automatizados. Bloqueia qualquer venda para um segundo cliente.
- **Fase 1 (MVP Comercial)**: cobrança recorrente, planos, onboarding self-service.
- **Fase 2 (Diferenciação)**: RBAC granular por obra, orçado vs. realizado, fluxo de caixa, anexos, parcelamento, PWA para campo.
- **Fase 3 (Enterprise)**: white-label, SSO, observabilidade/SLA, portabilidade de dados.

Não implemente itens de uma fase posterior antes dos pré-requisitos da fase anterior estarem resolvidos, a menos que explicitamente instruído — consulte o arquivo completo para prioridade, dependências e critérios de aceite de cada tarefa.

## Convenções do código existente

- Nomes de domínio, mensagens de erro e comentários estão em **português** (`lançamentos`, `contas`, `categorias`, `prestador`, `erro`) — mantenha esse idioma em código novo do mesmo domínio, para consistência.
- Envelope de erro padrão da API: `{"erro": "mensagem"}`, HTTP status apropriado. Não introduza um formato de erro diferente sem que seja parte explícita do plano aprovado.
- Estilo React: componentes funcionais, estilos majoritariamente inline via objetos `style={{...}}` (não há Tailwind/CSS Modules consolidado) e helpers em `utils/styles.js` (`btnStyle`, `inputStyle`).
- Backend: sem type hints consistentes, sem docstrings padronizadas — funções curtas, um arquivo por domínio em `controller/`, `routes/`, `database/`.
