# Folder Structure — Expense Management Project

## 1. Árvore completa (com propósito de cada item)

```
Expense-Management-Project/
│
├── docker-compose.yml              # Orquestra os 3 serviços: db_postgres, backend, frontend
│
├── back/                           # API Flask
│   ├── Dockerfile                  # Imagem de produção do backend (Python 3.11-slim + gcc/libpq-dev p/ psycopg2)
│   ├── requirements.txt            # Dependências Python fixadas por versão exata
│   ├── main.py                     # Entrypoint: carrega .env, cria app, decide Flask dev-server vs. Waitress
│   ├── check_db.py                 # Script manual de diagnóstico: lista projetos/usuários e valida JSON de 'colunas'
│   ├── verify_db.py                # Script manual de diagnóstico: valida projetos e amostra de lançamentos v2
│   ├── seed_db.py                  # Script de importação: lê front/src/data/data.json e popula tabela legada 'lancamentos'
│   ├── create_admin.py             # Script standalone: cria/atualiza um usuário admin com credenciais fixas no código
│   ├── migrate_to_v2.py            # Script de migração: move dados de 'lancamentos' (schema fixo) para 'lancamentos_v2' (JSON dinâmico)
│   ├── migrate_sqlite_to_postgres.py  # Script de migração: portar dados de um banco SQLite legado para o Postgres atual
│   │
│   └── app/                        # Pacote principal da aplicação Flask
│       ├── __init__.py             # Application Factory: cria app, configura CORS, inicializa DB, registra blueprints
│       │
│       ├── controller/             # Regra de negócio + acesso a dados (SQL direto), 1 arquivo por domínio
│       │   ├── auth_controller.py       # Login: valida credenciais, emite JWT
│       │   ├── lancamentos_controller.py # CRUD de lançamentos (tabela lancamentos_v2, schema dinâmico em JSON)
│       │   ├── servicos_controller.py    # CRUD de categorias e contas (por projeto)
│       │   ├── tarefas_controller.py     # CRUD de tarefas com regra de autorização por dono (prestador)
│       │   └── usuarios_controller.py    # CRUD de usuários (listar, criar, deletar — uso restrito a admin)
│       │
│       ├── database/                # Conexão com banco + definição de schema (DDL) + seeds
│       │   ├── db.py                     # Pool de conexões + wrappers de compatibilidade SQLite→Postgres + init_db()
│       │   ├── modelProjetos.py          # DDL de 'projetos', 'lancamentos_v2' e 'lancamentos' (legada) + seed do projeto padrão
│       │   ├── modelCategoria.py         # DDL de 'categorias' e 'contas' + seeds iniciais (lista fixa de categorias/contas)
│       │   ├── modelUsuarios.py          # DDL de 'usuarios' + seed do admin padrão ('admin'/'admin')
│       │   ├── modelRequisicoes.py       # DDL de 'requisicoes_materiais'
│       │   └── modelTarefas.py           # DDL de 'tarefas'
│       │
│       ├── routes/                  # Blueprints Flask — 1 arquivo por domínio, define os endpoints HTTP
│       │   ├── auth_routes.py            # POST /login
│       │   ├── lancamentos_routes.py     # GET/POST/PUT/DELETE /lancamentos
│       │   ├── projeto_routes.py         # GET/POST/PUT/DELETE /projetos (acessa DB direto, sem controller dedicado)
│       │   ├── servicos_routes.py        # GET/POST/DELETE /categorias e /contas
│       │   ├── usuarios_routes.py        # GET/POST/DELETE /usuarios
│       │   ├── requisicao_routes.py      # GET/POST/PUT /requisicoes (acessa DB direto, sem controller dedicado)
│       │   └── tarefas_routes.py         # GET/POST/PUT/DELETE /tarefas
│       │
│       └── utils/
│           └── auth_middleware.py   # Decorators @token_required e @admin_required (validação de JWT)
│
└── front/                          # SPA React (Vite)
    ├── dockerfile                  # Build multi-stage: node:20-alpine (build) → nginx:alpine (serve estático)
    ├── nginx.conf                  # Config Nginx: serve SPA + proxy reverso /api/ → backend:5000
    ├── vite.config.js              # Config Vite: plugin React + proxy de dev para o backend local
    ├── eslint.config.js            # Regras de lint do frontend (única ferramenta de qualidade estática do repo)
    ├── index.html                  # HTML raiz da SPA
    ├── package.json / package-lock.json
    ├── README.md                   # README padrão gerado pelo template Vite (não customizado com docs do projeto)
    ├── freatures.txt               # Roadmap informal do autor (features futuras, ver ProjectOverview.md)
    │
    ├── public/                     # Assets estáticos servidos como estão
    │
    └── src/
        ├── main.jsx                 # Ponto de entrada React (ReactDOM.createRoot)
        ├── App.jsx                  # Componente raiz: layout, abas visíveis por papel, composição dos módulos
        ├── App.css / index.css      # Estilos globais
        │
        ├── assets/                  # Logo, imagens (hero.png, LogoEmpresa.png, ícones padrão do Vite/React)
        │
        ├── components/               # Componentes de UI, majoritariamente "burros" (recebem props)
        │   ├── AdminTab.jsx               # Gestão de usuários (criar/listar/remover)
        │   ├── Card.jsx                    # Componente de cartão genérico (dashboard)
        │   ├── ConfirmModal.jsx            # Modal de confirmação genérico (usado antes de ações destrutivas)
        │   ├── ContasTab.jsx               # Listagem/gestão de contas do projeto ativo
        │   ├── DashboardTab.jsx            # Totais e gráficos (Recharts) por categoria/conta
        │   ├── DeleteModal.jsx             # Modal específico de exclusão
        │   ├── FormModal.jsx               # Formulário dinâmico de lançamento (renderizado a partir de projetoAtivo.colunas)
        │   ├── LancamentosTab.jsx          # Tabela de lançamentos com filtros
        │   ├── Login.jsx                   # Tela de autenticação
        │   ├── ProjectModal.jsx            # Criação de novo projeto/obra
        │   ├── ProjectSelector.jsx         # Dropdown de troca de projeto ativo
        │   ├── RequisicoesTab.jsx          # Tela de requisições de material (criação e listagem/aprovação)
        │   ├── ServicosTab.jsx             # Gestão de categorias do projeto ativo
        │   └── TarefasTab.jsx              # Tela de tarefas (criação por admin, atualização por prestador)
        │
        ├── data/
        │   ├── constants.js          # Categorias/contas/formas de pagamento padrão, cores de gráfico, colunas padrão
        │   └── data.json             # Dataset histórico usado por seed_db.py para popular a tabela legada 'lancamentos'
        │
        ├── hooks/
        │   └── useExpenses.js        # "God hook": todo o estado e lógica de negócio do frontend (ver Architecture.md)
        │
        ├── services/
        │   └── api.js                # Client HTTP fino: monta headers (JWT), trata 401 globalmente, expõe métodos por endpoint
        │
        └── utils/
            ├── format.js             # Helpers de formatação (parseVal — conversão de string monetária p/ número, etc.)
            └── styles.js              # Helpers de estilo inline reutilizáveis (btnStyle, inputStyle)
```

## 2. Observações sobre a organização

### 2.1 Separação backend/frontend é clara e correta
A raiz do repositório separa `back/` e `front/` de forma limpa, cada um com seu próprio `Dockerfile` e dependências — decisão correta e comum para permitir deploys/builds independentes, e é isso que o `docker-compose.yml` explora (`build: ./back`, `build: ./front`).

### 2.2 Scripts de manutenção ficam na raiz de `back/`, não em uma subpasta dedicada
`check_db.py`, `verify_db.py`, `seed_db.py`, `create_admin.py`, `migrate_to_v2.py` e `migrate_sqlite_to_postgres.py` estão todos soltos na raiz de `back/`, misturados com `main.py`. Não há uma pasta `scripts/` ou `management/` que os agrupe. Isso não impede o funcionamento, mas dificulta a distinção rápida entre "isto é a aplicação" e "isto é uma ferramenta administrativa de uso pontual" — alguém lendo `back/` pela primeira vez precisa abrir cada arquivo para entender se é parte do runtime da API ou uma ferramenta CLI avulsa.

### 2.3 `data.json` no frontend sendo consumido por um script Python do backend
`seed_db.py` (backend) lê o arquivo `front/src/data/data.json` (frontend) via caminho relativo (`os.path.join(os.path.dirname(BASE_DIR), 'front', 'src', 'data', 'data.json')`). Isso cria um **acoplamento estrutural entre as duas pastas** que normalmente seriam independentes: mover ou renomear a pasta `front/` quebra silenciosamente esse script. É um indício de que os dados originais do projeto nasceram como um dataset estático do frontend (antes de existir backend/banco de dados) e o script de seed foi escrito depois, aproveitando esse arquivo já existente, em vez de duplicar os dados para dentro de `back/`.

### 2.4 Ausência de pastas convencionais esperadas em projetos deste porte
- Não há `back/tests/` nem `front/src/__tests__` (ou equivalente) — nenhuma suíte de testes.
- Não há `back/migrations/` (Alembic ou similar) — o roadmap (`freatures.txt`) já lista isso como item futuro.
- Não há `docs/` (até a criação deste conjunto de documentos).
- Não há `.github/` — sem pipelines de CI/CD documentados no repositório.

### 2.5 `front/README.md` é o template padrão do Vite, não documentação do projeto
O README do frontend não foi customizado — é o texto genérico gerado pelo `create-vite` (fala sobre plugins oficiais do Vite e sobre o React Compiler), sem nenhuma instrução específica de como rodar, configurar `.env` ou entender as features deste projeto em particular. Não existe, em nenhum lugar do repositório, um README de alto nível na raiz explicando o projeto como um todo.
