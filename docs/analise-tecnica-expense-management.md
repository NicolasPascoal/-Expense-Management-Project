# Engenharia Reversa — Expense Management Project

Repositório: `NicolasPascoal/Expense-Management-Project`
Análise realizada em: julho/2026 · Snapshot: 1 commit único (`d7273df`, "att") — histórico "achatado", sem rastro de evolução incremental.

> Documento somente de leitura/entendimento. Nenhum arquivo do repositório foi alterado. Onde havia dúvida de regra de negócio, isso está sinalizado explicitamente em vez de assumido (ver seção 12 — Perguntas em Aberto).

---

## 1. Visão Geral

Sistema de **gestão de despesas de obra** (construção civil), com:

- **Backend**: Python 3.11 + Flask 3 (API REST "pura", sem ORM), PostgreSQL como banco.
- **Frontend**: React 19 + Vite, SPA single-page sem roteador (`react-router` não é usado — a navegação é por estado local `tab`).
- **Auth**: JWT (PyJWT) com hash de senha via Werkzeug (`generate_password_hash`).
- **Deploy**: Docker Compose com 3 serviços — `db_postgres`, `backend` (Gunicorn), `frontend` (Nginx servindo o build + proxy reverso para `/api`).

Domínio central: um usuário (empresa/família) controla o fluxo financeiro de uma ou mais **obras** ("projetos"), registrando **lançamentos** (despesas), organizados por **categoria** e **conta pagadora**, além de um módulo de **requisições de material** e um módulo de **tarefas** para prestadores de serviço.

O arquivo `front/freatures.txt` (roadmap informal, aparentemente anotações do próprio autor) é uma peça-chave: mostra que o sistema está em transição deliberada (SQLite → Postgres já feita; RBAC granular, auditoria, orçamento vs. realizado, anexos, parcelamento — ainda **não implementados**). Uso isso como evidência de intenção declarada do produto, não como suposição minha.

---

## 2. Estrutura de Pastas

```
Expense-Management-Project/
├── docker-compose.yml
├── back/                          # API Flask
│   ├── main.py                    # entrypoint (dev: Flask run / prod: Waitress ou Gunicorn via Dockerfile)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── create_admin.py            # script standalone p/ criar admin "nicolas" ⚠️ credenciais hardcoded
│   ├── seed_db.py                 # importa front/src/data/data.json p/ tabela legada 'lancamentos'
│   ├── migrate_to_v2.py           # migra 'lancamentos' -> 'lancamentos_v2' (schema JSON dinâmico)
│   ├── migrate_sqlite_to_postgres.py
│   ├── check_db.py / verify_db.py # scripts de diagnóstico manual (não são testes automatizados)
│   └── app/
│       ├── __init__.py            # application factory, CORS, registro de blueprints
│       ├── controller/            # lógica de negócio + acesso a dados (sem camada "service" separada)
│       ├── database/              # conexão + criação de schema (não há migrations tool)
│       ├── routes/                # blueprints Flask (1 por domínio)
│       └── utils/auth_middleware.py
└── front/                         # SPA React (Vite)
    ├── nginx.conf, dockerfile
    └── src/
        ├── App.jsx                # composição de layout + regras de visibilidade de abas por role
        ├── hooks/useExpenses.js   # "God hook": todo o estado e toda a lógica de negócio do front
        ├── services/api.js        # client HTTP fino (fetch wrapper)
        ├── components/            # 14 componentes, majoritariamente "burros" (recebem tudo via props)
        ├── data/{constants.js,data.json}
        └── utils/{format.js,styles.js}
```

Não há: pasta de testes (`tests/`), pasta `migrations/`, TypeScript, linting de backend, CI/CD (nenhum `.github/workflows`).

---

## 3. Arquitetura

### 3.1 Backend — padrão "Controller-Route" em 2 camadas

```
Request → routes/*.py (Blueprint + decorators de auth)
        → controller/*.py (regras de negócio + SQL direto)
        → database/db.py (wrapper de conexão)
        → PostgreSQL
```

- Não há camada de "repository" ou "service" separada — o controller mistura regra de negócio com SQL cru (queries inline, sem ORM/query builder).
- Não há camada de validação/serialização (não usa Marshmallow, Pydantic, etc.). Validação é manual e inconsistente (`if not campo: return erro`).
- Não há testes automatizados em nenhuma das duas aplicações.
- Alguns endpoints violam a separação: `projeto_routes.py` e `requisicao_routes.py` acessam `get_db_connection()` diretamente dentro da rota, sem passar por um controller — inconsistência arquitetural em relação aos demais módulos (lançamentos, tarefas, serviços, usuários), que centralizam a lógica em `controller/`.

### 3.2 Uma peculiaridade importante: `db.py` é uma camada de compatibilidade SQLite→Postgres

O arquivo `app/database/db.py` implementa **wrappers customizados** (`PostgreSQLRow`, `PostgreSQLCursorWrapper`, `PostgreSQLConnectionWrapper`) cujo único propósito é fazer o `psycopg2` **se comportar como o `sqlite3`** do código legado:

- Traduz automaticamente `?` → `%s` em toda query (`sql.replace('?', '%s')`).
- Emula `cursor.lastrowid` do SQLite chamando `SELECT lastval()` após cada `INSERT`.
- Ignora silenciosamente comandos `PRAGMA` (que não existem em Postgres).
- Emula `sqlite3.Row` (acesso por índice e por nome) via uma classe própria.

Isso indica que o projeto **nasceu em SQLite** e foi migrado para Postgres **sem reescrever a camada de acesso a dados** — uma decisão pragmática de curto prazo que gera uma dívida técnica relevante (ver seção 10).

### 3.3 Frontend — Hook único centralizando estado (padrão "God Hook")

`useExpenses.js` (570 linhas) concentra: autenticação, todos os fetches, todo o CRUD, filtros, cálculos de dashboard, exportação/importação de CSV, e todo o estado de UI (abrir modal, editar, etc.). É devolvido como um objeto gigante e espalhado via spread (`{...expenses}`) em quase todo componente.

- **Vantagem**: simplicidade inicial, fácil de rastrear "de onde vem o estado".
- **Custo**: qualquer componente pode, em teoria, ler/escrever qualquer parte do estado global — acoplamento alto, difícil de testar isoladamente, re-renders amplos (nenhum uso de `useCallback`/`useMemo` além de 3 pontos pontuais), e o hook cresce sem limite conforme features são adicionadas.
- Não há Context API, Redux, Zustand ou React Query — todo fetch é manual com `useEffect` + `useState`, sem cache, sem deduplicação, sem retry/backoff.

### 3.4 Fluxo de dados típico (exemplo: criar lançamento)

```
FormModal (input) → useExpenses.saveForm() → api.createLancamento()
  → fetch POST /api/lancamentos (com header Authorization: Bearer <jwt>)
  → lancamentos_routes.novo_lancamento() [@token_required]
  → controller.criar_lancamento(projeto_id, payload)
  → INSERT INTO lancamentos_v2 (projeto_id, dados) VALUES (?, json.dumps(payload))
  → retorna registro criado → front atualiza estado local `dados`
```

---

## 4. Modelo de Dados (schema efetivo, deduzido do código de criação de tabelas)

| Tabela | Colunas | Observação |
|---|---|---|
| `projetos` | id, nome, colunas (TEXT/JSON) | "colunas" define o **schema dinâmico** dos lançamentos daquele projeto (ver 4.1) |
| `lancamentos_v2` | id, projeto_id (FK), dados (TEXT/JSON) | Tabela ativa. Schema-less: tudo fica dentro do JSON `dados` |
| `lancamentos` | id, data, categoria, item, fornecedor, quantidade, unitario, valor, forma, conta, obs | **Legada**, mantida só por compatibilidade / seed inicial. Não tem `projeto_id` (não é filtrável por obra) |
| `categorias` | id, nome, projeto_id (FK) | Categorias de despesa, por projeto |
| `contas` | id, nome, projeto_id (FK) | Contas pagadoras, por projeto |
| `usuarios` | id, username (UNIQUE), password (hash), is_admin (int 0/1), role (varchar) | `role` e `is_admin` coexistem de forma redundante (ver 4.2) |
| `requisicoes_materiais` | id, usuario_id (FK), nome, funcao, material, status, data_criacao | Pedido de material feito por um prestador |
| `tarefas` | id, titulo, descricao, prestador_id (FK usuarios), status, observacoes, data_criacao | Tarefa atribuída a um prestador |

### 4.1 Padrão EAV / JSON dinâmico em `lancamentos_v2`

Em vez de colunas fixas, cada `projeto` define seu próprio schema em `projetos.colunas` (um array JSON de `{name, label, type, options?}`), e cada lançamento guarda um blob JSON (`dados`) com esses campos. O backend só faz `json.dumps`/`json.loads` — **não valida** que o `dados` enviado respeita o schema declarado em `colunas`.

Implicações:
- **Flexibilidade alta** (cada obra pode ter campos diferentes) às custas de **integridade zero** no nível de banco — não há constraints, tipos, nem obrigatoriedade reais; tudo é responsabilidade do front (que também não valida robustamente — só checa `data` no `saveForm`).
- Impossível fazer queries agregadas eficientes no banco (ex.: "soma de valor por categoria") — hoje isso é feito **no frontend**, iterando sobre todos os registros trazidos por `GET /lancamentos`. Não escala (ver seção 14).
- Coluna `TEXT` guardando JSON em vez de `JSONB` — perde indexação, operadores JSON nativos do Postgres e validação de formato pelo próprio banco.

### 4.2 Redundância `is_admin` vs `role`

`usuarios` tem **dois** campos de autorização: `is_admin` (0/1) e `role` (string livre: hoje só usa `admin`/`prestador`, mas o front (`AdminTab.jsx`) já permite criar um terceiro valor `'user'` que **não tem tratamento em lugar nenhum do backend** — nem em `auth_middleware`, nem nas telas do front, que só distinguem `prestador` vs. "não-prestador"). Isso é uma inconsistência de modelagem que vale esclarecer (ver seção 12, pergunta 1).

### 4.3 Diagrama de relacionamento (lógico)

```
usuarios 1───* tarefas (prestador_id)
usuarios 1───* requisicoes_materiais (usuario_id)

projetos 1───* categorias
projetos 1───* contas
projetos 1───* lancamentos_v2

lancamentos (legada) — órfã, sem FK para projetos
```

Não há relação entre `usuarios` e `projetos` — ou seja, **não existe controle de acesso por obra**. Qualquer usuário autenticado (mesmo não-admin, em rotas que só exigem `@token_required`) pode ler/criar/editar/excluir lançamentos, categorias e contas de **qualquer** projeto, sem checagem de "pertencimento". Isso é consistente com o roadmap (`freatures.txt` já lista "controle de acesso por obra" como pendência futura), mas é importante deixar registrado como estado atual.

---

## 5. Autenticação e Autorização

### 5.1 Autenticação
- Login: `POST /api/login` → valida usuário/senha (`check_password_hash`) → emite JWT (HS256) com payload `{id, username, is_admin, role, exp}`, validade **24h**.
- `JWT_SECRET_KEY` é obrigatório via variável de ambiente (o app falha ao subir se ausente — bom sinal defensivo), **mas** o valor real está commitado no arquivo `back/.env`, versionado no Git (ver seção 9 — Segurança).
- Frontend guarda token e user em `sessionStorage` (mais seguro que `localStorage` contra persistência entre sessões de aba, mas ainda vulnerável a XSS, pois não há `httpOnly` cookie).
- Logout "por inatividade": front implementa um timer de 15 minutos que desloga automaticamente (client-side apenas — o token JWT em si continua válido no backend até expirar, não há blacklist/revogação).

### 5.2 Autorização — dois mecanismos, aplicados de forma desigual

| Decorator | O que faz |
|---|---|
| `@token_required` | Exige JWT válido; popula `g.user` com o payload decodificado |
| `@admin_required` | Exige JWT válido **e** `is_admin` truthy; **não popula `g.user`** |

Problemas identificados:
1. **Inconsistência de contrato**: rotas decoradas com `admin_required` (ex.: `requisicao_routes.atualizar_status`, `projeto_routes.*`) não têm `g.user` disponível, porque `admin_required` decodifica o token só para checar `is_admin` mas nunca faz `g.user = data`. Se uma rota futura precisar de `g.user.id` dentro de uma função protegida só por `admin_required`, vai quebrar com `AttributeError`. Hoje não quebra porque nenhuma rota faz isso, mas é uma armadilha para manutenção futura.
2. **`except: pass` genérico** em `admin_required` (linha `except: ... return jsonify(...)`) — captura qualquer exceção (inclusive bugs de programação) e responde sempre "Token inválido", dificultando debug e mascarando erros reais.
3. **Autorização por dono do recurso** só existe no módulo de **tarefas** (`atualizar_tarefa` compara `tarefa['prestador_id']` com `usuario_id` do token) e, parcialmente, em **requisições** (o `GET` filtra por dono se não-admin, mas o **preview de criação** não impõe limite de campos). Em **lançamentos, categorias e contas**, qualquer usuário autenticado — mesmo `role='prestador'` — pode chamar diretamente a API (fora da UI, via curl/Postman) e editar/apagar lançamentos de qualquer projeto, pois as rotas usam apenas `@token_required`, não checam role nem dono. A UI esconde essas ações para prestadores, mas **a API não impõe a mesma regra** — isso é uma falha de autorização no nível de backend (a UI não é uma barreira de segurança).
4. `deletar_usuario` protege só o id `1` contra remoção — qualquer outro admin criado pode ser deletado por qualquer outro admin, inclusive a si mesmo, potencialmente removendo o único admin restante além do id 1 (cenário de "self-lockout" parcial, mitigado pelo id 1 ser intocável).

---

## 6. Regras de Negócio Identificadas

1. Login exige usuário e senha; token válido por 24h.
2. Existe sempre um projeto seed (`Obra Itanhaém`, id fixo 1) e um admin seed (`admin`/`admin` — ver risco de segurança).
3. Cada projeto tem um schema de colunas próprio; lançamentos armazenam dados conforme esse schema, mas **sem validação de tipo/obrigatoriedade no backend**.
4. **Tarefas**: só admin cria; admin edita todos os campos; prestador só edita `status` e `observacoes`, e só de tarefas onde é o `prestador_id`; só admin exclui.
5. **Requisições de material**: qualquer usuário autenticado cria (associada automaticamente a si mesmo via `g.user['id']`); usuário comum só vê as próprias; admin vê todas e é o único que pode alterar `status`.
6. **Usuários**: só admin gerencia (listar/criar/excluir); usuário de `id=1` é meta-protegido contra exclusão em ambas as camadas (controller e front).
7. Import de CSV no frontend: se não existir projeto ativo, cria um projeto novo automaticamente a partir dos cabeçalhos do CSV; categorias/contas novas encontradas na coluna `categoria`/`conta` são criadas automaticamente no banco (side-effect não solicitado explicitamente pelo usuário a cada importação — pode gerar duplicatas semânticas, ex. "Mão de obra" vs "Mao de obra", que **já aparece na lista de constantes `CATEGORIAS`** como entrada duplicada, sinal de que isso já aconteceu na prática).
8. Cálculo de "valor" no formulário: se `quantidade` e `unitario` forem preenchidos, `valor` é recalculado automaticamente (`quantidade * unitario`) — mas o usuário pode digitar um valor manual que será sobrescrito silenciosamente se depois mexer em quantidade/unitário.

---

## 7. Validações

- **Backend**: validações mínimas e feitas manualmente por campo obrigatório (`if not x: return 400`). Não há validação de tipos (ex.: `quantidade` poderia receber uma string arbitrária no JSON dinâmico, já que não há schema enforcement), nem de tamanho de string, nem sanitização de HTML/script em campos de texto livre (`obs`, `descricao`, `material`) — relevante porque esse conteúdo é depois **renderizado no React** (que por padrão escapa JSX, então XSS armazenado é mitigado pelo React, mas não pela API — se o dado for consumido em outro client sem escaping, o risco reaparece).
- **Frontend**: validação pontual (`data` obrigatória em `saveForm`, `required` em inputs HTML). A validação de `required` do HTML é client-side apenas e não é reforçada no backend.
- Não há validação de formato de e-mail (não há e-mail em lugar nenhum, só `username` livre).
- Senhas: sem política mínima (tamanho, complexidade) em nenhuma camada.

---

## 8. Tratamento de Erros e Logging

- **Logging**: não há um logger estruturado (`logging` module) em lugar nenhum do backend. O único "log" existente é um `print()` de debug dentro de `PostgreSQLCursorWrapper.execute()` quando uma query falha (`[QUERY FAILED] ...`), que **inclui a query SQL e os parâmetros** — em produção, isso pode vazar dados sensíveis no stdout/log do container caso alguma exceção seja gerada com dados de usuário.
- **Tratamento de erro no backend**: majoritariamente `try/except Exception as e: return {'erro': str(e)}` — expõe a mensagem de exceção crua (podendo incluir detalhes internos do Postgres) diretamente na resposta HTTP ao cliente. Não há um error handler global do Flask (`@app.errorhandler`), então erros não tratados explicitamente (ex.: um `KeyError` inesperado) provavelmente resultam em um 500 HTML padrão do Flask, não um JSON consistente — quebra de contrato de API.
- **Frontend**: erros de rede tratados com `alert()` do navegador (UX rudimentar, bloqueante) ou `console.error` silencioso (ex.: `fetchDados`, `fetchProjetos` — falha só aparece no console, o usuário não é avisado visualmente).
- Não há *retry*, *circuit breaker* ou *timeout* configurado nas chamadas `fetch`.

---

## 9. Segurança — Riscos Identificados (por severidade)

### 🔴 Crítico
1. **Segredos reais commitados no Git**: `back/.env` (rastreado por `git ls-files`, apesar de existir um `.gitignore` listando `.env`) contém a senha real do Postgres (`K33ps@f&`) e o `JWT_SECRET_KEY` real em produção/dev. Isso significa que **qualquer pessoa com acesso ao repositório (se for público, qualquer pessoa na internet) pode forjar tokens JWT válidos como admin** e/ou acessar o banco diretamente, se a porta 5432 estiver exposta. **Recomendação imediata, independente de qualquer outra melhoria: rotacionar a `JWT_SECRET_KEY` e a senha do Postgres, e remover `back/.env` do histórico do Git** (não basta apagar o arquivo — o segredo já está no histórico de commits).
2. **Credenciais de admin hardcoded em `create_admin.py`**: usuário `nicolas` / senha `nicolas12` commitados em texto plano no script. Qualquer pessoa que leia o repositório sabe um login admin válido (assumindo que o script já foi executado no ambiente de produção).
3. **Admin seed padrão previsível**: `admin`/`admin` é criado automaticamente por `modelUsuarios.py` sempre que a tabela está vazia — se alguém subir uma instância nova sem trocar essa senha imediatamente, é uma conta admin trivialmente adivinhável.

### 🟠 Alto
4. **Falta de autorização por role/dono em rotas sensíveis** (lançamentos, categorias, contas — ver seção 5.2, item 3): qualquer usuário autenticado, independente de role, pode manipular dados financeiros de qualquer projeto via chamada direta à API.
5. **CORS default aberto**: se `CORS_ALLOWED_ORIGINS` não estiver setada, o app libera `CORS(app)` sem restrição (`*`), embora o `.env` real do projeto já restrinja isso corretamente — o risco é para quem clonar o repo e não configurar o `.env`.
6. **Mensagens de erro vazam detalhes internos** (`str(e)` de exceções de banco devolvido ao cliente).

### 🟡 Médio
7. Sem *rate limiting* no `/login` — permite ataque de força bruta de senha sem throttling.
8. Sem HTTPS/HSTS configurado no Nginx (a configuração fornecida é só HTTP na porta 80 — presumivelmente há um proxy/TLS termination externo não presente no repo, mas isso não está documentado).
9. `except: pass` genérico em `admin_required` mascara erros de programação como "token inválido".
10. Log de query (`print`) pode vazar dados sensíveis em stdout de produção.

---

## 10. Dívida Técnica

1. **Wrapper de compatibilidade SQLite→Postgres em `db.py`**: solução funcional, mas cara de manter — qualquer query nova precisa "pensar em SQLite" (usar `?`, evitar `INSERT` com coluna `id` explícita para não quebrar o `lastval()`, etc.), e any deviation entre bancos (ex. tipos, funções específicas do Postgres) vira uma armadilha silenciosa.
2. **Tabela `lancamentos` legada e não utilizada pelas rotas ativas** (só existe para o script `seed_db.py` e para leitura histórica via `migrate_to_v2.py`) — candidata a ser removida ou arquivada, hoje é confusão pura para quem entra no projeto (2 tabelas de lançamento, uma delas "morta").
3. **Sem ORM/migrations**: todo o DDL está espalhado em funções Python (`create_*_tables`) chamadas na inicialização (`init_db()`), sem versionamento de schema. Qualquer alteração de schema em produção depende de rodar scripts manuais (`migrate_to_v2.py`) na ordem certa, sem rollback.
4. **God Hook no frontend** (`useExpenses.js`): 570 linhas, sem separação por domínio — mistura autenticação, lançamentos, tarefas, requisições, projetos, import/export CSV. Deveria estar particionado (ex.: `useAuth`, `useLancamentos`, `useTarefas`, `useProjetos`), especialmente porque o roadmap (`freatures.txt`) prevê ainda mais funcionalidades (orçamento, parcelamento, anexos) — o hook vai crescer ainda mais nesse padrão.
5. **Sem testes automatizados** em nenhuma das duas aplicações — qualquer refactor é arriscado sem uma rede de segurança.
6. **Estilos inline em quase todos os componentes React** em vez de CSS modules/Tailwind consistente (há um `App.css`/`index.css`, mas a maior parte da estilização é feita via objetos `style={{...}}` inline, dificultando reuso e consistência visual).
7. **JSON armazenado como `TEXT`** em vez de `JSONB` no Postgres — perde recursos nativos do banco (indexação parcial, operadores `->>`, validação).
8. **Categoria duplicada nos dados** (`"Mão de obra"` e `"Mao de obra"` na constante `CATEGORIAS`) — sintoma de falta de normalização/deduplicação no fluxo de import de CSV.
9. **Scripts de diagnóstico (`check_db.py`, `verify_db.py`) fora de qualquer framework de teste** — são scripts ad-hoc de depuração manual, não testes de fato.

---

## 11. Riscos, Gargalos e Escalabilidade

- **Modelo EAV sem agregação no banco**: `GET /lancamentos` sempre retorna **todos** os lançamentos do projeto (sem paginação), e todo cálculo (`totalGeral`, `porCategoria`, `porConta`, filtro por busca textual) é feito **no cliente**, iterando `Object.values(d)` por linha. Para uma obra pequena isso é irrelevante; para milhares de lançamentos (ou múltiplas obras grandes), isso degrada tanto o tempo de resposta da API (sem paginação) quanto a performance de renderização do front (sem virtualização de lista).
- **Connection pool fixo** (`SimpleConnectionPool(1, 20)`) global por processo — com Gunicorn `-w 4` (4 workers), cada worker abre seu próprio pool, então na prática o limite real é 4×20 = até 80 conexões simultâneas ao Postgres; isso deve ser validado contra o `max_connections` configurado no Postgres do ambiente de produção (não está no repo).
- **Sem cache** (nem HTTP cache-control, nem cache de aplicação) — toda navegação refaz fetch completo.
- **Sem índices explícitos** além das PKs/FKs — filtros por `projeto_id` em `lancamentos_v2`, `categorias`, `contas` não têm índice dedicado (dependem apenas do índice implícito de FK, que o Postgres cria automaticamente só se declarado — vale confirmar com `\d` no banco real).
- **CSV import é sequencial e "um request por linha"** (`await api.createLancamento(...)` dentro de um loop `for`) — para arquivos grandes, isso é lento (N round-trips HTTP) e sem transação atômica (se falhar na linha 50 de 200, as 49 anteriores já foram persistidas — estado parcialmente importado, sem rollback).

---

## 12. Perguntas em Aberto (não assumi respostas)

Preciso desses esclarecimentos antes de qualquer proposta de melhoria, para não desenhar algo desalinhado com sua intenção real de produto:

1. **O valor `role = 'user'`** aparece no `AdminTab.jsx` (checkbox "Prestador" desmarcado gera `role: 'user'`), mas nenhuma rota do backend trata esse valor de forma diferente de "não-admin genérico". Esse terceiro papel é intencional (ex.: um "financeiro" futuro, como sugere `freatures.txt`) ou é resíduo de uma versão anterior da UI?
2. **Autorização por projeto**: hoje qualquer usuário autenticado pode ler/escrever lançamentos de qualquer obra via API direta. Isso é um risco aceito conscientemente nesta fase (uso interno, poucos usuários confiáveis) ou é uma lacuna que deveria ser tratada com prioridade alta, antes de outras features?
3. **Tabela `lancamentos` legada**: ainda há algum consumidor real dela em produção (algum relatório, script de terceiros, ou é usada só por `seed_db.py`), ou pode ser considerada morta com segurança?
4. **Os segredos em `back/.env`/`create_admin.py` já vazados no Git são os mesmos em uso em produção hoje**, ou o repositório público/compartilhado usa segredos diferentes dos de produção? Isso muda a urgência da rotação de credenciais.
5. **Import de CSV**: a criação automática de categorias/contas novas a partir do arquivo é um comportamento desejado (auto-cadastro) ou deveria pedir confirmação explícita do usuário antes de gravar no banco?

---

## 13. Inventário de Endpoints (para referência rápida)

| Método | Rota | Proteção | Controller |
|---|---|---|---|
| POST | /api/login | — (pública) | auth_controller.login_usuario |
| GET/POST | /api/lancamentos | token_required | lancamentos_controller |
| GET/PUT/DELETE | /api/lancamentos/:id | token_required | lancamentos_controller |
| GET | /api/projetos | token_required | inline na rota |
| POST/PUT/DELETE | /api/projetos(/:id) | admin_required | inline na rota |
| GET/POST | /api/categorias | token_required | servicos_controller |
| DELETE | /api/categorias/:id | token_required | servicos_controller |
| GET/POST | /api/contas | token_required | servicos_controller |
| DELETE | /api/contas/:id | token_required | servicos_controller |
| GET | /api/usuarios | admin_required | usuarios_controller |
| POST | /api/usuarios | admin_required | usuarios_controller |
| DELETE | /api/usuarios/:id | admin_required | usuarios_controller |
| GET/POST | /api/requisicoes | token_required | inline na rota |
| PUT | /api/requisicoes/:id/status | admin_required | inline na rota |
| GET/PUT/DELETE | /api/tarefas | token_required (+ regra de dono no controller) | tarefas_controller |
| POST | /api/tarefas | token_required + checagem manual `is_admin` na rota | tarefas_controller |

---

## 14. Resumo Executivo (TL;DR)

- Projeto funcional, pragmático, com arquitetura simples de 2 camadas (routes/controllers) e um frontend React centrado em um único hook de estado.
- **Achado mais crítico, para agir já, independente de qualquer roadmap**: segredos reais (senha de banco, chave JWT, credenciais de admin) estão commitados no Git. Isso deveria ser corrigido antes de qualquer outra prioridade.
- **Segunda prioridade**: a API não impõe as mesmas regras de autorização que a UI esconde — módulos financeiros (lançamentos/categorias/contas) são acessíveis a qualquer usuário autenticado, sem checagem de role ou de propriedade do projeto.
- Dívida técnica principal: camada de compatibilidade SQLite→Postgres, ausência de ORM/migrations, ausência de testes, "God Hook" no front, e um modelo de dados schema-less (JSON em TEXT) sem validação de servidor.
- O arquivo `freatures.txt` já documenta boa parte dessas lacunas como trabalho futuro conhecido pelo autor — o que é positivo: mostra que não são "surpresas", e sim itens de roadmap já mapeados, faltando priorização e execução.

Fico à disposição para aprofundar qualquer seção específica (ex.: simular os cenários de autorização, mapear cada componente React em detalhe, ou desenhar um plano de correção de segurança priorizado) — mas, como combinado, nenhuma mudança de código será feita até você validar as respostas da seção 12 e definir a prioridade dos próximos passos.
