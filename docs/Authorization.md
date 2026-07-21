# Authorization — Expense Management Project

## 1. Modelo de autorização adotado

O sistema usa um modelo simplificado de **RBAC (Role-Based Access Control)**, com apenas dois papéis efetivamente aplicados (`admin` e `prestador`), implementado através de dois mecanismos complementares:

1. **Decorators de rota** (`@token_required`, `@admin_required`) — controlam **quem pode acessar o endpoint como um todo**.
2. **Checagens manuais dentro do controller** — controlam regras mais finas, como "só o dono do recurso pode editá-lo" (aplicado apenas ao módulo de Tarefas, parcialmente ao de Requisições).

Não há uma biblioteca de autorização declarativa (como Flask-Principal, Casbin, ou políticas baseadas em atributos/ABAC) — toda a lógica é código imperativo, espalhado entre `utils/auth_middleware.py` e cada `controller`.

**Motivo provável dessa escolha**: dado o número pequeno de papéis (2) e de regras de propriedade (praticamente só tarefas), escrever a autorização "à mão" é mais simples do que introduzir uma biblioteca de políticas — o custo dessa simplicidade aparece quando o número de regras cresce (ver seção 5).

## 2. Os decorators em detalhe (unificados na Tarefa 1.3, 2026-07-20)

Desde a Tarefa 1.3 do roadmap SaaS, existe um **ponto único de autenticação**: a função interna `_autenticar()` em `utils/auth_middleware.py`, que decodifica o token uma única vez e popula `g.user` com o payload completo (`id`, `username`, `is_admin`, `role`, `empresa_id`). Todos os decorators são composições sobre ela — nenhum decodifica token por conta própria.

### 2.1 `@token_required`

- Exige apenas um JWT válido (assinatura correta, não expirado).
- **Popula `g.user`** com o payload completo do token.
- Cenários de erro: token ausente (`401`), expirado (`401`, "Token expirado!"), inválido/malformado (`401`, "Token inválido!"). Header `Bearer ` sem token também retorna `401` (antes estourava `IndexError`/500).

### 2.2 `@admin_required`

- Exige JWT válido **e** `is_admin` truthy no payload (`403` caso contrário).
- **Popula `g.user`** igual a `token_required` — mesmo contrato (unificado; a divergência histórica descrita no Problema 1 abaixo foi eliminada).

### 2.3 `@non_prestador_required`

- Aplicado **depois** de `@token_required`; retorna `403` para `role='prestador'`.
- Protege os módulos de dado financeiro (lançamentos, categorias, contas, orçamentos, entradas, auditoria).

## 3. Problemas de consistência identificados (apenas documentados)

### Problema 1 — `admin_required` não popula `g.user` — ✅ corrigido (Tarefas 1.1/1.3)
Histórico: rotas protegidas só por `admin_required` não tinham acesso a `g.user`. Desde a Tarefa 1.1 o decorator popula `g.user`, e desde a Tarefa 1.3 (2026-07-20) ambos os decorators compartilham o mesmo `_autenticar()` — o contrato é idêntico por construção, com teste de regressão em `back/tests/test_autorizacao.py` (`test_admin_required_popula_g_user_com_empresa_id`).

### Problema 2 — `except: pass` genérico mascara bugs — ✅ corrigido (Tarefa 1.3)
O `except:` genérico foi eliminado na unificação: só `jwt.ExpiredSignatureError` e `jwt.InvalidTokenError` são capturados (com mensagens distintas); qualquer outro erro sobe como 500 visível em vez de se disfarçar de "token inválido". O vazamento de detalhe interno (`str(e)` na resposta 401 do antigo `token_required`) também foi removido.

### Problema 3 — Falta de autorização por role nos módulos financeiros — ✅ corrigido em 2026-07-08
Os endpoints de **lançamentos, categorias e contas** usavam apenas `@token_required` — ou seja, aceitavam qualquer usuário autenticado, **incluindo usuários com `role='prestador'`**. Na interface (`App.jsx`), essas telas são simplesmente ocultadas para prestadores (`tabs` é filtrado conforme `user.role`), mas isso era uma barreira de **UX**, não de **segurança** — qualquer prestador que capturasse seu próprio token (via DevTools do navegador, por exemplo) e fizesse uma chamada direta com `curl`/Postman para `POST /api/lancamentos`, `DELETE /api/lancamentos/:id`, `POST /api/categorias`, etc., teria sucesso, porque o backend não validava o `role` nessas rotas.

**Correção**: todas as rotas de lançamentos/categorias/contas agora aplicam `@non_prestador_required` (além de `@token_required`), retornando `403` para `role='prestador'` em leitura e escrita. Continua não havendo checagem de propriedade de projeto (qualquer não-prestador ainda acessa qualquer projeto) — isso depende de multi-tenancy (Épico 1, ainda não implementado). O papel ambíguo `role='user'` (ver seção 5, Problema 5) **não** é bloqueado por essa correção, já que a checagem é especificamente `role == 'prestador'` — permanece com o mesmo comportamento (acidental) de "não-prestador" que já tinha antes.

### Problema 4 — Assimetria entre módulos quanto à granularidade de autorização
Comparando os quatro módulos que usam autorização mais que "qualquer autenticado":

| Módulo | Granularidade de autorização |
|---|---|
| Usuários | Binária: só admin (via decorator) |
| Projetos | Binária: só admin (via decorator) |
| Requisições | Mista: qualquer autenticado cria/lê as próprias; só admin altera status (via decorator no endpoint de status) |
| Tarefas | Mais fina: qualquer autenticado lê/edita, mas o **controller** aplica regra de propriedade (`prestador_id == usuario_id`) e diferencia quais campos cada papel pode alterar |
| Lançamentos/Categorias/Contas | **Nenhuma** granularidade além de "autenticado" |

Essa inconsistência sugere que a autorização foi implementada **módulo a módulo, conforme a necessidade percebida no momento**, sem um padrão único aplicado a todo o sistema — o módulo de Tarefas (o mais recente, aparentemente, dado o nível de sofisticação) tem a autorização mais completa; os módulos mais antigos (Lançamentos, Categorias, Contas) nunca foram atualizados para acompanhar esse padrão.

### Problema 5 — Papel `role='user'` sem qualquer regra de autorização
Como mencionado em `BusinessRules.md`, a tela de administração permite criar um usuário com `role='user'` (quando nem "Admin" nem "Prestador" são marcados), mas nenhuma rota do backend trata esse valor de forma diferente de qualquer outro usuário não-admin — na prática, esse usuário teria acesso a **todas as abas não-administrativas** (porque o filtro do frontend só verifica `role === 'prestador'` para restringir, e um `role='user'` não bate nessa condição), incluindo lançamentos financeiros, o que pode ou não ser a intenção original (ver `BusinessRules.md`, seção "Regras Ambíguas").

## 4. Autorização por propriedade de recurso (Tarefas) — o caso mais completo do sistema

```python
def atualizar_tarefa(tarefa_id, dados, usuario_id, is_admin):
    tarefa = ...  # busca a tarefa
    if not is_admin and tarefa['prestador_id'] != usuario_id:
        return 403  # "Acesso negado"
    if is_admin:
        # pode alterar qualquer campo enviado
    else:
        # só pode alterar status e observacoes
```

Este é o único módulo do sistema que combina **três níveis de controle** ao mesmo tempo: (1) autenticação, (2) papel do usuário, e (3) propriedade do recurso específico sendo acessado. É o padrão mais próximo de um controle de acesso "correto" para este tipo de sistema, e serve como referência do nível de granularidade que os demais módulos financeiros **não têm**.

## 5. Controle de acesso por empresa (tenant) — ✅ implementado; por obra — pendente

Desde a Tarefa 1.2 (2026-07-17), a unidade de autorização é **a empresa (tenant)**: toda leitura filtra por `empresa_id` do token e toda escrita valida posse do recurso antes de agir (ver `docs/Database.md` e `back/app/utils/tenant.py`). Um usuário nunca lê/edita dado de outra empresa, mesmo via chamada direta à API.

O que **ainda não existe** é granularidade por **obra dentro da mesma empresa**: qualquer não-prestador da empresa acessa qualquer projeto dela. Isso é a Tarefa 6.2 do roadmap (usuário↔obra com papel por vínculo), dependente dos papéis expandidos da Tarefa 6.1.

## 6. Matriz de autorização efetiva (estado atual do código — testada em `back/tests/test_autorizacao.py` e `test_tenant_isolation.py`)

Todas as rotas autenticadas também aplicam **isolamento por tenant** (Tarefa 1.2): leitura filtrada por `empresa_id` do token; escrita valida posse do recurso (404/400 para recurso de outra empresa).

| Endpoint | Decorator | Checagem adicional |
|---|---|---|
| `POST /login` | Nenhum (público) | — |
| `GET/POST/PUT/DELETE /lancamentos*` | `token_required` + `non_prestador_required` | Posse do `projeto_id` na criação |
| `GET/POST/DELETE /categorias*`, `/contas*` | `token_required` + `non_prestador_required` | Posse do `projeto_id` na criação |
| `GET/POST/DELETE /orcamentos*` | `token_required` + `non_prestador_required` | Posse do `projeto_id` + categoria pertence ao projeto |
| `GET/POST/DELETE /entradas*` | `token_required` + `non_prestador_required` | Posse do `projeto_id`; valor > 0 |
| `GET /auditoria` | `token_required` + `non_prestador_required` | Filtra por `empresa_id` (últimos 100) |
| `GET /projetos` | `token_required` | Filtra por `empresa_id` |
| `POST/PUT/DELETE /projetos*` | `admin_required` | Posse do projeto em PUT/DELETE |
| `GET/POST/DELETE /usuarios*` | `admin_required` | Alvo da exclusão pertence à empresa; proteção do `id=1` |
| `GET /requisicoes` | `token_required` | Admin: filtra por empresa; não-admin: filtra por dono |
| `POST /requisicoes` | `token_required` | Usuário só cria para si mesmo, por design |
| `PUT /requisicoes/:id/status` | `admin_required` | Requisição pertence à empresa |
| `GET /tarefas` | `token_required` | Admin: filtra por empresa; não-admin: filtra por dono |
| `POST /tarefas` | `token_required` | `is_admin` manual na rota; `prestador_id` pertence à empresa |
| `PUT /tarefas/:id` | `token_required` | Dono (`prestador_id == usuario_id`) se não-admin; campos por papel; tarefa pertence à empresa |
| `DELETE /tarefas/:id` | `token_required` | `is_admin` no controller; tarefa pertence à empresa |

**Papéis efetivos**: `admin` (tudo na própria empresa), `prestador` (só tarefas próprias e requisições), `user` (comporta-se como não-prestador não-admin — acessa dado financeiro; sem regra própria, ver Problema 5; papéis expandidos são o Épico 6).
