# Dependencies — Expense Management Project

## 1. Backend (`back/requirements.txt`)

Todas as dependências estão fixadas por versão exata (`==`), o que é uma boa prática para reprodutibilidade de builds — evita que uma atualização automática de dependência quebre o ambiente de produção sem aviso.

| Pacote | Versão | Propósito | Por que foi escolhido (inferido) |
|---|---|---|---|
| `Flask` | 3.0.3 | Framework web/HTTP | Framework minimalista, adequado para uma API pequena sem necessidade de "baterias inclusas" de um framework maior (ex.: Django); baixa curva de aprendizado, ecossistema maduro |
| `Flask-Cors` | 4.0.0 | Middleware de CORS | Necessário porque o frontend (SPA) e o backend rodam em origens diferentes durante o desenvolvimento (`localhost:5173` vs `localhost:5000`) e, mesmo em produção com Nginx fazendo proxy, oferece uma camada de controle explícito de quais origens podem consumir a API |
| `Werkzeug` | 3.1.8 | Utilitários HTTP/WSGI (dependência do Flask) e hashing de senha | Usado explicitamente para `generate_password_hash`/`check_password_hash` — reaproveita uma dependência que já viria transitivamente com o Flask, evitando adicionar uma lib de hashing dedicada |
| `PyJWT` | 2.8.0 | Geração/validação de JSON Web Tokens | Biblioteca padrão de mercado para JWT em Python; simples, sem dependências pesadas |
| `psycopg2-binary` | 2.9.12 | Driver de conexão com PostgreSQL | Driver mais usado para Postgres em Python; a variante `-binary` inclui os binários pré-compilados (libpq), simplificando a instalação sem precisar compilar a partir do código-fonte (o `Dockerfile`, porém, ainda instala `gcc`/`libpq-dev`, o que sugere que em algum momento a versão não-binary foi usada, ou é uma precaução para dependências que exigem compilação) |
| `python-dotenv` | 1.0.1 | Carregar variáveis de `.env` para `os.environ` | Padrão de mercado para gerenciar configuração local sem hardcode; permite usar o mesmo código em dev/produção trocando apenas o arquivo `.env` |
| `gunicorn` | 22.0.0 | Servidor WSGI de produção (Linux/Docker) | Servidor de produção padrão para apps Flask em ambiente Linux/Docker — usado no `Dockerfile` (`CMD ["gunicorn", "-w", "4", ...]`) |
| `waitress` | 3.0.2 | Servidor WSGI de produção (Windows) | Incluído porque o `main.py` detecta o modo de execução e usa Waitress como alternativa ao Gunicorn — provavelmente porque o Gunicorn **não tem suporte oficial ao Windows** (depende de `fork()`, indisponível nativamente no Windows), então Waitress cobre o cenário de alguém rodar o backend em produção diretamnte em uma máquina Windows, fora de containers Linux |

**Observação sobre ausências notáveis**: não há `pytest` (nem em `requirements.txt` nem em um `requirements-dev.txt` separado — não existe tal arquivo), não há `SQLAlchemy`/`Alembic` (embora sejam mencionados no roadmap `freatures.txt`), não há biblioteca de logging estruturado (`structlog`, etc.), não há biblioteca de validação de schema (`marshmallow`, `pydantic`).

## 2. Frontend (`front/package.json`)

### 2.1 Dependências de produção

| Pacote | Versão | Propósito | Por que foi escolhido (inferido) |
|---|---|---|---|
| `react` | ^19.2.5 | Biblioteca de UI | Versão recente do React (19.x) — indica um projeto iniciado/atualizado recentemente, aproveitando features modernas do React |
| `react-dom` | ^19.2.5 | Renderização DOM do React | Par obrigatório de `react` |
| `lucide-react` | ^1.14.0 | Biblioteca de ícones SVG | Usada extensivamente em `App.jsx` e nas abas (ícones de dashboard, tarefas, admin, etc.) — alternativa leve e moderna a `react-icons`/`font-awesome`, com ícones consistentes em estilo "outline" |
| `recharts` | ^3.8.1 | Biblioteca de gráficos | Usada no `DashboardTab.jsx` para os gráficos de totais por categoria/conta — escolha comum para gráficos declarativos em React, construída sobre D3 mas com API simplificada |

### 2.2 Dependências de desenvolvimento

| Pacote | Versão | Propósito |
|---|---|---|
| `vite` | ^8.0.10 | Build tool e dev server | Escolhido no lugar do Create React App (hoje descontinuado) — build mais rápido via ESBuild/Rollup, HMR instantâneo |
| `@vitejs/plugin-react` | ^6.0.1 | Plugin do Vite para suporte a JSX/Fast Refresh | Necessário para o Vite processar arquivos `.jsx` |
| `eslint` + `@eslint/js` | ^10.2.1 / ^10.0.1 | Linter de JavaScript | Única ferramenta de qualidade estática de código presente em todo o repositório (o backend não tem equivalente, ex.: `flake8`/`ruff`/`black`) |
| `eslint-plugin-react-hooks` | ^7.1.1 | Regras de lint específicas para hooks do React | Ajuda a evitar bugs comuns de dependências de `useEffect`/`useMemo` — relevante dado o uso intenso de hooks customizados (`useExpenses.js`) |
| `eslint-plugin-react-refresh` | ^0.5.2 | Regras de lint para compatibilidade com Fast Refresh do Vite | Garante que os componentes sigam convenções que não quebrem o hot-reload |
| `globals` | ^17.5.0 | Definições de variáveis globais para o ESLint | Configuração auxiliar do ESLint |
| `@types/react`, `@types/react-dom` | ^19.2.14 / ^19.2.3 | Tipos TypeScript para React | Presentes mesmo o projeto **não usando TypeScript** (não há arquivos `.ts`/`.tsx` no repositório) — provavelmente mantidos apenas para que o editor (VS Code, etc.) ofereça autocomplete/IntelliSense mais preciso sobre a API do React, um padrão comum mesmo em projetos JS puro |

**Observação sobre ausências notáveis**: não há biblioteca de roteamento (`react-router-dom`), não há gerenciador de estado global dedicado (`redux`, `zustand`, `jotai`), não há biblioteca de data-fetching com cache (`@tanstack/react-query`, `swr`), não há biblioteca de formulários (`react-hook-form`, `formik`) — todos esses papéis são cobertos por código próprio dentro do "God Hook" (`useExpenses.js`) e por `useState`/`useEffect` nativos.

## 3. Infraestrutura (imagens Docker)

| Imagem | Onde é usada | Propósito |
|---|---|---|
| `python:3.11-slim` | `back/Dockerfile` (estágio único) | Base enxuta do Python para produção; `slim` reduz o tamanho da imagem final comparado à imagem `python:3.11` completa |
| `postgres:15-alpine` | `docker-compose.yml` (serviço `db_postgres`) | Postgres 15, variante Alpine (menor footprint) |
| `node:20-alpine` | `front/dockerfile` (estágio de build) | Node 20 para compilar o build de produção do Vite; Alpine reduz o tamanho da imagem intermediária |
| `nginx:alpine` | `front/dockerfile` (estágio final) | Serve os arquivos estáticos gerados pelo build e faz proxy reverso para o backend — build multi-stage (Node só é necessário para compilar, não para servir) |

**Motivo do build multi-stage no frontend**: separar a imagem que **compila** o React (que precisa de Node, `npm install`, etc. — pesada) da imagem que **serve** o resultado (que só precisa de um servidor HTTP estático — leve). Isso reduz drasticamente o tamanho final da imagem de produção do frontend, já que o Node e todas as `devDependencies` não vão para a imagem final.

## 4. Ferramentas de banco de dados adicionais instaladas via SO (não via `requirements.txt`)

O `Dockerfile` do backend instala, via `apt-get`, os pacotes de sistema `gcc` e `libpq-dev` antes de instalar as dependências Python — necessários para compilar extensões nativas que dependem da biblioteca cliente do Postgres (`libpq`), mesmo usando `psycopg2-binary` (que teoricamente já vem pré-compilado). Isso sugere uma abordagem defensiva/redundante do autor (garantir que a compilação funcione mesmo se, por algum motivo, o wheel binário não for compatível com a plataforma-alvo).
