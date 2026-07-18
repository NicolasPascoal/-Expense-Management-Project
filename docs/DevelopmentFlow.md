# Development Flow — Expense Management Project

## 1. Pré-requisitos

- Docker e Docker Compose (caminho recomendado, cobre banco + backend + frontend de uma vez).
- Alternativamente, para rodar sem Docker: Python 3.11+, Node.js 20+, e uma instância PostgreSQL 15 acessível.

## 2. Variáveis de ambiente

### 2.1 Backend (`back/.env`)

| Variável | Exemplo | Obrigatória? |
|---|---|---|
| `PGUSER` | `postgres` | Não (default `postgres`) |
| `PGPASSWORD` | — | Não (default `postgres`) |
| `PGHOST` | `localhost` / `db_postgres` (Docker) | Não (default `localhost`) |
| `PGPORT` | `5432` | Não (default `5432`) |
| `PGDATABASE` | `expense_management` | Não (default `expense_management`) |
| `JWT_SECRET_KEY` | — | **Sim** — a aplicação falha ao iniciar (`RuntimeError`) se ausente |
| `FLASK_DEBUG` | `True`/`False` | Não (default `False`) — controla se `main.py` usa o servidor de desenvolvimento do Flask (hot-reload) ou um servidor de produção |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Não (default `*`, aberto) |

### 2.2 Frontend (`front/.env`)

| Variável | Exemplo | Descrição |
|---|---|---|
| `VITE_API_URL` | `/api` | Base usada pelo client HTTP (`services/api.js`) |
| `VITE_API_PROXY_TARGET` | `http://127.0.0.1:5000` | Alvo do proxy de desenvolvimento do Vite (evita CORS em dev) |

**Observação importante (ver `Security.md`)**: os arquivos `back/.env` e `front/.env` estão, hoje, rastreados pelo Git no estado atual do repositório, contendo valores reais (não apenas exemplos) — incluindo segredos de produção. Isso é documentado como um risco de segurança, não como parte do fluxo recomendado de configuração.

## 3. Rodando com Docker Compose (fluxo principal)

```bash
docker compose up --build
```

Isso sobe, na ordem correta de dependência:
1. **`db_postgres`** — Postgres 15, com healthcheck (`pg_isready`) que os demais serviços aguardam antes de subir.
2. **`backend`** — build a partir de `back/Dockerfile`, executa `gunicorn -w 4 -b 0.0.0.0:5000 main:app`. Na inicialização do processo Flask (`create_app()`), `init_db()` roda automaticamente — não é necessário nenhum passo manual de "criar banco" antes do primeiro uso.
3. **`frontend`** — build multi-stage (`node:20-alpine` compila, `nginx:alpine` serve), expõe a porta `3050` (mapeada para a porta `80` do container Nginx).

Acesso, após subir:
- Frontend: `http://localhost:3050`
- Backend (direto, se necessário para debug): `http://localhost:5000/api/...`
- Postgres (direto, se necessário): `localhost:5432`

**Login inicial**: usuário seed `admin` / senha seed `admin` (criado automaticamente se a tabela `usuarios` estiver vazia — ver `Database.md`, seção 6).

## 4. Rodando sem Docker (desenvolvimento local)

### 4.1 Backend

```bash
cd back
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
# configurar back/.env com PGHOST=localhost e um Postgres já rodando localmente
python main.py
```

- Se `FLASK_DEBUG=True`: sobe com o servidor embutido do Flask (`app.run(debug=True, ...)`), com hot-reload, na porta 5000.
- Se `FLASK_DEBUG=False` (ou ausente): `main.py` importa e usa **Waitress** (não Gunicorn) como servidor — o comentário no próprio código (`"Servidor de produção no Windows"`) indica que esse caminho existe especificamente para permitir rodar em produção **em uma máquina Windows**, onde o Gunicorn (usado no Dockerfile) não é suportado nativamente.

### 4.2 Frontend

```bash
cd front
npm install
npm run dev
```

Sobe o Vite dev server (porta padrão 5173), com proxy de `/api` configurado em `vite.config.js` apontando para `VITE_API_PROXY_TARGET` (por padrão, `http://127.0.0.1:5000`, ou seja, o backend rodando localmente conforme seção 4.1).

## 5. Scripts administrativos (execução manual, fora do fluxo normal da aplicação)

Estes scripts **não** são chamados automaticamente — precisam ser executados manualmente com o ambiente Python do backend ativo e as variáveis de ambiente de conexão ao banco configuradas:

| Script | Quando usar | Comando |
|---|---|---|
| `seed_db.py` | Popular a tabela legada `lancamentos` a partir do dataset estático `front/src/data/data.json` | `python seed_db.py` |
| `migrate_to_v2.py` | Migrar dados da tabela `lancamentos` (schema fixo) para `lancamentos_v2` (schema dinâmico) | `python migrate_to_v2.py` |
| `migrate_sqlite_to_postgres.py` | Portar dados de um banco SQLite legado para o Postgres atual (cenário de migração única, histórica) | `python migrate_sqlite_to_postgres.py` |
| `create_admin.py` | Criar/atualizar um usuário administrativo com credenciais fixas no próprio script | `python create_admin.py` |
| `check_db.py` | Diagnóstico manual: lista projetos/usuários no console, valida se `colunas` é JSON válido | `python check_db.py` |
| `verify_db.py` | Diagnóstico manual: lista projetos com colunas parseadas e amostra de lançamentos v2 | `python verify_db.py` |

**Ordem recomendada para uma migração completa de um ambiente legado** (inferida da lógica dos scripts, não documentada explicitamente em lugar nenhum do repositório): `migrate_sqlite_to_postgres.py` (se partindo de SQLite) → `seed_db.py` (se necessário popular a tabela legada a partir do JSON estático) → `migrate_to_v2.py` (para levar os dados ao schema ativo `lancamentos_v2`).

## 6. Fluxo de build de produção (o que o Docker faz por trás)

### 6.1 Backend
```
FROM python:3.11-slim
apt-get install gcc libpq-dev      # dependências nativas para compilar psycopg2, se necessário
pip install -r requirements.txt
COPY . .
CMD gunicorn -w 4 -b 0.0.0.0:5000 main:app
```
4 workers Gunicorn, cada um com seu próprio pool de conexões ao banco (ver `Performance.md`, seção 5, para a implicação disso no número total de conexões simultâneas ao Postgres).

### 6.2 Frontend (build multi-stage)
```
Estágio 1 (node:20-alpine): npm install && npm run build   → gera /app/dist (estático)
Estágio 2 (nginx:alpine): copia /app/dist para /usr/share/nginx/html
                          copia front/nginx.conf para /etc/nginx/conf.d/default.conf
CMD nginx -g "daemon off;"
```
O Nginx final serve o SPA (`try_files $uri $uri/ /index.html` — necessário porque não há roteador real, mas ainda assim garante que qualquer rota "física" não encontrada caia no `index.html`, prática padrão para SPAs) e faz proxy reverso de `/api/` para o serviço `backend` pela rede interna do Docker Compose (`rede_projeto`).

## 7. Rede Docker

Todos os três serviços (`db_postgres`, `backend`, `frontend`) compartilham a rede `rede_projeto` (driver `bridge`), permitindo que se refiram uns aos outros pelo nome do serviço (`db_postgres`, `backend`) em vez de IPs fixos — é assim que `PGHOST=db_postgres` e `proxy_pass http://backend:5000/api/` funcionam dentro do ambiente Docker Compose.

## 8. O que não existe no fluxo atual de desenvolvimento (documentado, não corrigido)

- Não há comando único de "rodar testes" (não há testes).
- Não há comando de lint para o backend (só o frontend tem `npm run lint`, via `eslint.config.js`).
- Não há pipeline de CI que rode automaticamente ao abrir um Pull Request.
- Não há documentação de como popular dados de exemplo em um ambiente novo além dos scripts avulsos descritos na seção 5 (nenhum deles é mencionado em nenhum README).
- Não há `Makefile` ou script único (`./setup.sh`, `npm run docker:up`, etc.) que encapsule os passos acima — o desenvolvedor precisa conhecer os comandos individuais do Docker Compose, `pip`, e `npm` separadamente.
