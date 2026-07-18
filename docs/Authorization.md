# Authorization — Expense Management Project

## 1. Modelo de autorização adotado

O sistema usa um modelo simplificado de **RBAC (Role-Based Access Control)**, com apenas dois papéis efetivamente aplicados (`admin` e `prestador`), implementado através de dois mecanismos complementares:

1. **Decorators de rota** (`@token_required`, `@admin_required`) — controlam **quem pode acessar o endpoint como um todo**.
2. **Checagens manuais dentro do controller** — controlam regras mais finas, como "só o dono do recurso pode editá-lo" (aplicado apenas ao módulo de Tarefas, parcialmente ao de Requisições).

Não há uma biblioteca de autorização declarativa (como Flask-Principal, Casbin, ou políticas baseadas em atributos/ABAC) — toda a lógica é código imperativo, espalhado entre `utils/auth_middleware.py` e cada `controller`.

**Motivo provável dessa escolha**: dado o número pequeno de papéis (2) e de regras de propriedade (praticamente só tarefas), escrever a autorização "à mão" é mais simples do que introduzir uma biblioteca de políticas — o custo dessa simplicidade aparece quando o número de regras cresce (ver seção 5).

## 2. Os dois decorators em detalhe

### 2.1 `@token_required`

```python
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token: return 401
        # remove "Bearer " se presente
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        g.user = data   # <- disponibiliza o payload do token para a view
        return f(*args, **kwargs)
    return decorated
```

- Exige apenas um JWT válido (assinatura correta, não expirado).
- **Popula `g.user`** com o payload completo do token (`id`, `username`, `is_admin`, `role`), disponível para a função de rota decorada.
- Trata três cenários de erro distintos: token ausente (`401`), expirado (`401`, mensagem específica "Token expirado!"), e inválido/malformado (`401`, mensagem específica "Token inválido!").

### 2.2 `@admin_required`

```python
def admin_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token: return 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if not data.get('is_admin'):
                return 403
        except:
            return 401
        return f(*args, **kwargs)
    return decorated
```

- Exige JWT válido **e** que `is_admin` seja truthy no payload.
- **Não popula `g.user`** — diferença de contrato importante em relação a `token_required` (ver seção 3, Problema #1).
- Usa um `except:` genérico (sem especificar o tipo de exceção), que captura **qualquer** erro — inclusive bugs de programação não relacionados a JWT — e responde sempre como se fosse um token inválido.

## 3. Problemas de consistência identificados (apenas documentados)

### Problema 1 — `admin_required` não popula `g.user`
Rotas protegidas só por `admin_required` (ex.: `projeto_routes.py`, `requisicao_routes.atualizar_status`) não têm acesso a `g.user` dentro da view, porque o decorator decodifica o token apenas para checar `is_admin`, sem armazenar o payload em `g`. Hoje isso não causa erro porque nenhuma dessas rotas atualmente precisa saber "quem" é o admin que fez a chamada — mas é uma armadilha para qualquer desenvolvimento futuro: se alguém adicionar, por exemplo, um campo de auditoria "aprovado por" em `atualizar_status`, tentar usar `g.user['id']` ali vai gerar um `AttributeError` em tempo de execução, não detectável estaticamente.

### Problema 2 — `except: pass` genérico mascara bugs
O bloco `except:` sem tipo específico em `admin_required` significa que, se o código de validação tiver um bug (ex.: uma variável não definida, um erro de tipo), o usuário recebe a mesma mensagem de "token inválido" que receberia por um JWT realmente malformado — dificultando diagnosticar a causa raiz em produção.

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

## 5. Ausência de controle de acesso por projeto/obra

Não existe, em nenhuma tabela do banco, uma relação entre `usuarios` e `projetos`. Isso significa que a unidade de autorização hoje é **o sistema inteiro**, não **a obra específica** — um usuário autenticado (mesmo não-admin, nos módulos sem checagem de role) pode, em tese, ler e escrever dados de **qualquer** projeto cadastrado, não apenas do projeto ao qual deveria ter acesso.

Esta lacuna já está mapeada como trabalho futuro pelo próprio autor no roadmap (`front/freatures.txt`: "controle de acesso por obra", "permissões por ação (não só tipo de usuário)"), o que indica que é uma limitação conhecida e não uma "descoberta" desta análise — mas seu impacto prático (qualquer usuário lendo/editando dados financeiros de qualquer obra) é relevante o suficiente para ser destacado com prioridade neste documento.

## 6. Resumo da matriz de autorização efetiva (estado atual do código)

| Endpoint | Decorator | Checagem adicional no controller |
|---|---|---|
| `POST /login` | Nenhum (público) | — |
| `GET/POST/PUT/DELETE /lancamentos*` | `token_required` + `non_prestador_required` | Nenhuma checagem de propriedade de projeto |
| `GET/POST/DELETE /categorias*`, `/contas*` | `token_required` + `non_prestador_required` | Nenhuma checagem de propriedade de projeto |
| `GET /projetos` | `token_required` | Nenhuma |
| `POST/PUT/DELETE /projetos*` | `admin_required` | Nenhuma |
| `GET/POST/DELETE /usuarios*` | `admin_required` | Proteção adicional contra exclusão do `id=1` |
| `GET /requisicoes` | `token_required` | Filtra por dono se não-admin |
| `POST /requisicoes` | `token_required` | Nenhuma (usuário só cria para si mesmo, por design) |
| `PUT /requisicoes/:id/status` | `admin_required` | Nenhuma |
| `GET /tarefas` | `token_required` | Filtra por dono se não-admin |
| `POST /tarefas` | `token_required` | Checagem manual de `is_admin` na própria rota |
| `PUT /tarefas/:id` | `token_required` | Checagem de dono (`prestador_id == usuario_id`) se não-admin; campos permitidos variam por papel |
| `DELETE /tarefas/:id` | `token_required` | Checagem manual de `is_admin` no controller |
