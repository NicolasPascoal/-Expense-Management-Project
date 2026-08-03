# Architecture — Expense Management Project

## 1. Visão macro

```
┌─────────────────┐        HTTP/JSON (fetch + JWT Bearer)        ┌───────────────────┐
│   React SPA      │  ───────────────────────────────────────▶  │   Flask REST API   │
│  (Vite build,     │  ◀───────────────────────────────────────  │  (Blueprints por    │
│   servido via     │                                              │   domínio)          │
│   Nginx)          │                                              └─────────┬──────────┘
└─────────────────┘                                                          │
                                                                              │ psycopg2 (pool)
                                                                              ▼
                                                                    ┌───────────────────┐
                                                                    │   PostgreSQL 15     │
                                                                    └───────────────────┘
```

É uma arquitetura de **monolito simples em 2 serviços** (API + banco), com um **frontend SPA desacoplado** consumindo a API via REST/JSON. Não há gateway de API, service mesh, filas assíncronas, cache distribuído ou microsserviços — decisão coerente com o porte do sistema (gestão de obra, poucos usuários simultâneos).

## 2. Backend — arquitetura em camadas

### 2.1 Camadas identificadas

```
routes/        → Define endpoints HTTP (Blueprints Flask), aplica decorators de autenticação/autorização,
                  faz parsing básico do request (request.get_json(), query params) e delega ao controller.

controller/     → Concentra regra de negócio + acesso a dados. Não há separação entre "regra de negócio"
                  e "acesso a dados" (não existe camada de repository) — o controller monta e executa SQL
                  diretamente.

database/       → db.py: conexão/pool + wrappers de compatibilidade SQLite→Postgres.
                  model*.py: funções de criação de schema (DDL) e seed de dados iniciais,
                  uma por domínio (Projetos, Categoria, Usuarios, Requisicoes, Tarefas).

utils/          → auth_middleware.py: decorators @token_required e @admin_required.
```

**Por que essa camada existe (routes vs. controller) e por que é assim**: a divisão routes/controller é o padrão mais simples possível de separar "protocolo HTTP" de "regra de negócio" sem introduzir uma camada de serviço adicional. Para uma API pequena, com poucos endpoints por domínio, isso evita over-engineering. O custo dessa escolha é que o controller acumula duas responsabilidades (regra + SQL), o que cresce mal conforme a aplicação ganha complexidade (ver `TechDebt.md`).

### 2.2 Inconsistência de camada: nem tudo passa por `controller/`

Nem todos os domínios seguem o padrão routes→controller→database. **`projeto_routes.py` e as rotas de `requisicao_routes.py`** (exceto quando explicitamente delegado) acessam `get_db_connection()` **diretamente dentro do arquivo de rotas**, sem um módulo `controller` dedicado. Já `lancamentos`, `servicos` (categorias/contas), `usuarios` e `tarefas` têm controllers próprios em `app/controller/`.

Isso não parece uma decisão arquitetural deliberada, e sim uma **evolução orgânica do código** — provavelmente os módulos de projetos/requisições foram adicionados em momentos diferentes ou por critérios de "está funcionando, não vou tocar". O efeito prático é que qualquer pessoa que entre no projeto precisa checar **onde** a lógica de um domínio está antes de mexer nele — não há um lugar único e previsível.

### 2.3 Application Factory Pattern

`app/__init__.py` usa o padrão **Application Factory** (`create_app()`), que:
- Cria a instância Flask.
- Configura CORS de forma condicional (restrito se `CORS_ALLOWED_ORIGINS` estiver definida, aberto — `*` — caso contrário).
- Chama `init_db()` **na inicialização do processo**, garantindo que o schema exista antes de qualquer request ser aceito.
- Registra 7 blueprints, todos sob o prefixo `/api`.

**Motivo dessa escolha**: Application Factory é o padrão recomendado pelo próprio Flask para permitir múltiplas instâncias da app (ex.: uma para testes, outra para produção) e para evitar import circular entre módulos que dependem da instância `app`. Aqui, na prática, só é usada uma instância (não há suíte de testes que crie uma segunda instância), mas a estrutura já está pronta para isso.

### 2.4 Camada de compatibilidade SQLite→PostgreSQL (`db.py`)

Esta é a decisão arquitetural mais incomum do projeto. Em vez de reescrever todo o código de acesso a dados para usar a sintaxe nativa do `psycopg2` (placeholders `%s`, `cursor.description`, etc.) quando o projeto migrou de SQLite para Postgres, foi criada uma camada de **wrappers** que faz o driver do Postgres "fingir" ser o `sqlite3`:

- `PostgreSQLRow`: emula `sqlite3.Row` (acesso por índice **e** por nome de coluna).
- `PostgreSQLCursorWrapper`: traduz `?` → `%s` em toda query, emula `cursor.lastrowid` via `SELECT lastval()`, ignora comandos `PRAGMA` (inexistentes em Postgres).
- `PostgreSQLConnectionWrapper`: emula o método `.execute()` diretamente na conexão (comportamento do `sqlite3.Connection`).

**Motivo provável dessa decisão**: minimizar o esforço de migração — todo o código de `controller/` e `database/model*.py` foi escrito originalmente pensando em SQLite (`?` como placeholder, `cursor.lastrowid`, etc.) e, ao trocar o banco, manter esse código inalterado e "traduzir" na camada de conexão é mais rápido do que reescrever cada query. É uma decisão pragmática de curto prazo, com custo de manutenção de longo prazo (ver `TechDebt.md` para os detalhes do custo).

### 2.5 Pool de conexões

`get_db_connection()` usa `psycopg2.pool.SimpleConnectionPool(1, 20)`, instanciado **uma única vez por processo** (variável de módulo `_db_pool`, padrão *singleton lazily initialized*). Cada chamada a `get_db_connection()` pega uma conexão do pool e cada `.close()` do wrapper **devolve** a conexão ao pool (não a fecha de fato), desde que o pool exista.

**Motivo**: evitar o custo de abrir uma conexão TCP nova a cada request — importante em uma API que abre/fecha conexão a cada função de controller (não há uma conexão por request, gerenciada via `before_request`/`teardown_request` do Flask, e sim uma conexão por chamada individual a `get_db_connection()`, o que pode significar múltiplas idas ao pool dentro do mesmo request se o controller chamar mais de uma função de acesso a dados).

## 3. Frontend — arquitetura de estado centralizado

### 3.1 Padrão "Container/Presentational" informal

- `App.jsx` funciona como componente-container: decide quais abas mostrar (baseado no papel do usuário), gerencia navegação por estado local (`tab`) e repassa **todo** o objeto retornado por `useExpenses()` para os componentes filhos via spread (`{...expenses}`).
- Os componentes em `src/components/` são majoritariamente "burros" (recebem dados e callbacks via props e não têm fetch próprio — exceção: `AdminTab.jsx` e alguns outros chamam `api.*` diretamente para ações pontuais, misturando um pouco o padrão).

### 3.2 "God Hook" (`useExpenses.js`)

Todo o estado da aplicação (autenticação, projetos, lançamentos, categorias, contas, requisições, tarefas, usuários, filtros, modais) e toda a lógica de negócio do frontend (cálculos de dashboard, import/export CSV, timers de sessão) vivem em um único hook customizado de ~570 linhas.

**Motivo provável dessa decisão**: simplicidade inicial — para uma SPA pequena, um hook único evita a complexidade de configurar um gerenciador de estado global (Redux, Zustand, Context API) e permite que qualquer componente acesse qualquer parte do estado apenas chamando `useExpenses()` uma vez em `App.jsx` e espalhando via props. É a abordagem "mais rápida de escrever" para uma aplicação com poucos desenvolvedores e sem necessidade inicial de compartilhar estado entre árvores de componentes distantes.

**Trade-off**: conforme mais features são adicionadas (o hook já mistura 6+ domínios diferentes), a manutenibilidade cai — qualquer alteração de uma função nesse hook arrisca efeitos colaterais em partes não relacionadas do estado, e o hook não pode ser testado unitariamente por domínio sem mockar tudo (ver `TechDebt.md`).

### 3.3 Ausência de camada de cache/data-fetching

Não há React Query, SWR, Apollo Client ou qualquer biblioteca de data-fetching com cache. Todo fetch é feito manualmente via `useEffect` + `useState`, com re-fetch completo sempre que a dependência do efeito muda (ex.: trocar de projeto ativo dispara um novo `fetchDados()` e `fetchServicos()` completos).

**Motivo provável**: novamente, simplicidade — para uma aplicação de uso interno com poucos usuários, o custo de não ter cache é aceitável na maior parte do tempo, mas isso é um ponto de atenção para escalabilidade (ver `Performance.md`).

### 3.4 Ausência de roteador (React Router)

A navegação entre "abas" (`dashboard`, `lancamentos`, `requisicoes`, `tarefas`, `contas`, `servicos`, `admin`) é feita por uma variável de estado (`tab`) e renderização condicional, **não** por URLs distintas. Isso significa que:
- Não há deep-linking (não é possível compartilhar um link direto para uma aba específica).
- O botão "voltar" do navegador não navega entre abas da aplicação.
- Um F5 (refresh) sempre volta para a aba padrão (`dashboard`, ou `tarefas` para prestadores).

**Motivo provável**: a aplicação foi concebida como um painel único de uso interno, onde a navegação por URL não era um requisito percebido como necessário no momento da construção inicial.

## 4. Comunicação Frontend ↔ Backend

- **Protocolo**: HTTP/JSON puro (`fetch` nativo do browser), sem GraphQL, sem WebSocket.
- **Autenticação por requisição**: header `Authorization: Bearer <jwt>`, injetado por `services/api.js` em toda chamada (`getHeaders()`).
- **Dev**: proxy do Vite (`vite.config.js`) redireciona `/api` para `http://127.0.0.1:5000` (ou o que estiver em `VITE_API_PROXY_TARGET`), evitando problemas de CORS em desenvolvimento.
- **Produção**: Nginx (`front/nginx.conf`) serve os arquivos estáticos do build e faz proxy reverso de `/api/` para o serviço `backend:5000/api/` dentro da rede Docker interna (`rede_projeto`).

**Motivo da escolha REST simples**: dado o tamanho do domínio (poucas entidades, sem necessidade de queries agregadas complexas do lado do cliente), REST/JSON é suficiente e mais simples de depurar do que GraphQL, sem custo de setup de schema/resolvers.

## 5. Padrões de projeto observados (e sua ausência)

| Padrão | Presente? | Onde / Observação |
|---|---|---|
| Application Factory | ✅ | `app/__init__.py` |
| Blueprint (modularização de rotas) | ✅ | `app/routes/*.py` |
| Decorator (cross-cutting concerns) | ✅ | `@token_required`, `@admin_required` |
| Repository / Data Access Object | ❌ | Controllers acessam SQL diretamente |
| Service Layer | ❌ | Lógica de negócio misturada ao controller |
| DTO / Schema de validação (Marshmallow, Pydantic) | ❌ | Validação manual campo a campo |
| ORM | ❌ | SQL cru via `psycopg2` |
| Adapter (compatibilidade de driver) | ✅ | `PostgreSQLRow`/`PostgreSQLCursorWrapper` emulando `sqlite3` |
| Singleton (pool de conexão) | ✅ | `_db_pool` global, lazy-initialized |
| EAV (Entity-Attribute-Value) | ✅ (parcial) | `lancamentos_v2.dados` (JSON dinâmico por schema de projeto) |
| Container/Presentational (frontend) | ✅ (informal) | `App.jsx` + hook único vs. componentes de apresentação |
| Gerenciador de estado global explícito (Redux/Zustand/Context) | ❌ | Susbstituído por um hook único devolvido via props |
| Client de data-fetching com cache (React Query/SWR) | ❌ | `fetch` manual em `useEffect` |

## 6. Por que não há testes, CI/CD ou linters de backend

Não há indício de suíte de testes (`pytest`, `unittest`), nem de pipeline de CI (`.github/workflows` ausente), nem de linter configurado no backend (existe apenas `eslint.config.js` no frontend). O histórico do Git tem **um único commit** (squashed), o que sugere que o repositório foi enviado ao GitHub como um snapshot do estado atual, sem preservar o histórico incremental de desenvolvimento — isso é consistente com um projeto ainda em estágio inicial/pessoal, sem processo de entrega formalizado (não há evidência de branch strategy, PRs ou revisão de código no que foi disponibilizado).
