# Database — Expense Management Project

## 1. Motor de banco de dados

- **PostgreSQL 15** (imagem `postgres:15-alpine`, definida em `docker-compose.yml`).
- Driver de acesso: `psycopg2-binary==2.9.12` (Python).
- Não há ORM (SQLAlchemy, Tortoise, etc.) e não há ferramenta de migrations (Alembic, Flyway) — todo o schema é criado por código Python imperativo, executado a cada subida da aplicação (`init_db()`).

## 2. Histórico: origem em SQLite

Evidências no código confirmam que o projeto **nasceu usando SQLite** e foi migrado para PostgreSQL preservando o máximo possível do código original:

- Existe um script dedicado (`migrate_sqlite_to_postgres.py`) cuja única função é portar dados de um banco SQLite legado para o Postgres atual.
- A camada `app/database/db.py` implementa uma **camada de compatibilidade** (`PostgreSQLRow`, `PostgreSQLCursorWrapper`, `PostgreSQLConnectionWrapper`) cujo propósito exclusivo é fazer o driver do Postgres se comportar como o `sqlite3` nativo do Python — motivo detalhado na seção 4.
- O `.gitignore` do backend ainda lista `database.db` como arquivo a ignorar (resquício do tempo em que o projeto usava um arquivo SQLite local).

**Por que essa migração foi feita**: o roadmap do autor (`front/freatures.txt`) menciona explicitamente a intenção de "trocar banco de dados" para PostgreSQL, usar JSONB, ORM e migrations — indicando que a migração para Postgres é parte de uma estratégia deliberada de amadurecimento da infraestrutura, ainda em andamento (Postgres já está em produção, mas JSONB/ORM/migrations ainda não).

## 3. Estratégia de conexão

### 3.1 Configuração via variáveis de ambiente

```python
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASSWORD = os.getenv("PGPASSWORD", "postgres")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DATABASE = os.getenv("PGDATABASE", "expense_management")
```

Os valores padrão (`postgres`/`postgres`/`localhost`) são apenas fallback de desenvolvimento — em produção (Docker Compose), essas variáveis são injetadas explicitamente no serviço `backend`, apontando para o serviço `db_postgres` pela rede interna do Docker (`PGHOST=db_postgres`).

**Motivo**: uso de variáveis de ambiente para configuração de banco é a prática padrão (12-factor app) para permitir o mesmo código rodar em dev/produção sem alteração, apenas trocando o `.env`.

### 3.2 Pool de conexões

```python
_db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, ...)
```

- Instanciado **uma única vez por processo** (padrão singleton com inicialização preguiçosa — só cria o pool na primeira chamada a `get_db_connection()`).
- Limite de 1 a 20 conexões por processo.
- Cada `conn.close()` (no wrapper) **devolve** a conexão ao pool via `pool.putconn()`, em vez de fechar de fato a conexão TCP.

**Motivo**: evitar o custo de handshake TCP/autenticação a cada operação de banco, já que o padrão do código é "abrir conexão → executar → fechar" a cada função de controller (não há uma conexão única por request HTTP gerenciada pelo ciclo de vida do Flask).

**Observação sobre múltiplos processos**: o `Dockerfile` de produção roda `gunicorn -w 4`, ou seja, **4 processos** independentes, cada um com seu próprio pool de até 20 conexões — o limite real de conexões simultâneas ao Postgres em produção pode chegar a 80, o que deve ser confrontado com o `max_connections` configurado no Postgres (não definido explicitamente neste repositório, portanto usa o padrão da imagem `postgres:15-alpine`).

## 4. Camada de compatibilidade SQLite → PostgreSQL (`db.py`)

Esta é a peça mais particular da camada de dados. Como todo o código de `controller/` e `database/model*.py` foi escrito originalmente assumindo a API do `sqlite3` (placeholders `?`, `cursor.lastrowid`, `sqlite3.Row` para acesso por nome de coluna), a migração para `psycopg2` foi feita **sem reescrever essas chamadas** — em vez disso, três classes wrapper traduzem o comportamento:

| Classe | Função | Como funciona |
|---|---|---|
| `PostgreSQLRow` | Emular `sqlite3.Row` | Permite acessar uma linha por índice (`row[0]`) ou por nome de coluna (`row['nome']`), e oferece `.keys()`, `.items()`, suporte a `dict(row)` |
| `PostgreSQLCursorWrapper` | Emular o cursor do `sqlite3` | Traduz `sql.replace('?', '%s')` antes de executar; ignora comandos `PRAGMA` (usados no SQLite para configs específicas, inexistentes no Postgres); emula `lastrowid` executando `SELECT lastval()` logo após um `INSERT` (apenas se a query não especificar a coluna `id` explicitamente, para não abortar a transação em bancos onde `lastval()` falharia) |
| `PostgreSQLConnectionWrapper` | Emular a conexão do `sqlite3` | Expõe `.execute()` diretamente na conexão (como o `sqlite3.Connection` permite), delega `.cursor()` para retornar sempre um `PostgreSQLCursorWrapper` |

**Motivo desta decisão**: minimizar o esforço e o risco de reescrever dezenas de queries espalhadas por 5 controllers e 5 arquivos de modelo ao trocar de banco. Ao interceptar a tradução na camada mais baixa (o wrapper de cursor/conexão), o restante do código de aplicação continuou funcionando **sem alteração**. É uma estratégia válida para uma migração rápida e de baixo risco de regressão imediata, mas que **transfere o custo para a manutenção futura**: qualquer nova query precisa ser escrita "pensando em SQLite" (evitar `INSERT` com `id` explícito se depender de `lastrowid`, lembrar que `PRAGMA` é silenciosamente ignorado, etc.), e recursos específicos do Postgres (JSONB, window functions, `RETURNING`, CTEs) não são adotados porque quebrariam a compatibilidade da camada wrapper ou simplesmente não são necessários dado que o código ainda "pensa" em termos de SQLite.

## 5. Inicialização do schema (`init_db()`)

```python
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    create_empresas_tables(cursor)
    create_projetos_tables(cursor)
    create_usuarios_tables(cursor)
    create_categorias_tables(cursor)
    create_requisicoes_tables(cursor)
    create_tarefas_tables(cursor)
    conn.commit()
    conn.close()
```

Chamada **toda vez que a aplicação sobe** (dentro de `create_app()`), usando `CREATE TABLE IF NOT EXISTS` para ser idempotente — ou seja, não há uma etapa separada de "provisionamento" do banco: o próprio processo da API garante que as tabelas existem antes de aceitar requisições.

**Motivo**: simplicidade operacional — não é preciso rodar um comando de migração manualmente antes do primeiro deploy; a aplicação se "auto-provisiona". O custo é a ausência total de controle de versão de schema: não há histórico de "quais alterações de schema já foram aplicadas em qual ambiente", e qualquer alteração de coluna existente (não apenas criação de tabela nova) exigiria um script de migração manual à parte (como de fato acontece com `migrate_to_v2.py`), sem qualquer registro formal de que a migração já foi ou não executada em um ambiente específico além de checagens ad-hoc (`SELECT COUNT(*) ... IF 0`).

### 5.1 Ordem de criação e por que ela importa

A ordem (`empresas` → `projetos` → `usuarios` → `categorias` → `requisicoes` → `tarefas`) respeita a dependência de chaves estrangeiras: `projetos`/`usuarios` referenciam `empresas` (Tarefa 1.1 do roadmap SaaS); `categorias`/`contas` referenciam `projetos`; `requisicoes_materiais` e `tarefas` referenciam `usuarios`. Criar fora dessa ordem falharia com erro de FK inexistente.

## 6. Seeds automáticos na inicialização

Cada `create_*_tables()` também insere dados padrão **se a tabela estiver vazia**:

| Tabela | Seed | Observação |
|---|---|---|
| `empresas` | 1 empresa: `Obra Itanhaém` (id fixo 1) | Tenant seed que herda todo o histórico legado de instância única (Tarefa 1.1 do roadmap SaaS) |
| `projetos` | 1 projeto: `Obra Itanhaém` (id fixo 1), com um conjunto padrão de 10 colunas dinâmicas, vinculado a `empresa_id=1` | Também sincroniza a sequência (`setval`) para o próximo `id` gerado não colidir com o id fixo 1 |
| `usuarios` | 1 admin: `admin`/`admin` (senha com hash), vinculado a `empresa_id=1` | Ver `Security.md` — credencial previsível |
| `categorias` | 9 categorias fixas (`Documentação`, `Terraplanagem`, etc.), associadas ao primeiro projeto encontrado | |
| `contas` | 4 contas fixas (nomes reais de pessoas/empresas — ver `Entities.md`) | |
| `requisicoes_materiais` | Nenhum seed | Tabela criada vazia |
| `tarefas` | Nenhum seed | Tabela criada vazia |

### 6.1 Multi-tenancy (Tarefa 1.1 do roadmap SaaS) — estado atual

`usuarios.empresa_id` e `projetos.empresa_id` (`NOT NULL REFERENCES empresas(id)`) existem desde esta tarefa, e o JWT emitido no login passa a incluir `empresa_id` (ver `Authentication.md`). **Isso ainda não implica isolamento entre empresas**: nenhuma query de leitura hoje filtra por `empresa_id` — essa é a Tarefa 1.2 (middleware de isolamento), ainda não implementada. Ver `STATUS.md` e `docs/Roadmap-SaaS-Construtoras.md`.

Para bancos que já existiam antes desta tarefa (ex.: ambiente de desenvolvimento atual), rodar `back/migrate_add_empresas.py` uma vez para fazer o backfill de `empresa_id` nos dados existentes — instalações novas já nascem com o schema correto via `init_db()`.

**Motivo**: garantir que uma instância recém-criada do sistema já tenha dados mínimos utilizáveis (projeto padrão, categorias, contas, um usuário para login inicial), sem exigir um passo manual de setup. O efeito colateral é que os nomes de contas/projeto seed são específicos de um caso de uso real (não genéricos), reforçando que este sistema foi construído para uma necessidade concreta e não abstraída como "produto" genérico desde o início.

## 7. Scripts de manutenção e migração (fora do runtime da API)

Esses scripts não são chamados pela aplicação — são executados manualmente (`python nome_do_script.py`) por um operador humano:

| Script | Propósito |
|---|---|
| `seed_db.py` | Lê `front/src/data/data.json` e insere na tabela **legada** `lancamentos` (schema fixo, sem `projeto_id`) |
| `migrate_to_v2.py` | Cria as tabelas `projetos`/`lancamentos_v2` se não existirem, cria o projeto padrão `Obra Itanhaém` se necessário, e migra os registros de `lancamentos` (schema fixo) para `lancamentos_v2` (schema dinâmico em JSON), evitando duplicar se já migrado |
| `migrate_sqlite_to_postgres.py` | Move dados de um banco SQLite legado para o Postgres atual |
| `create_admin.py` | Cria/atualiza um usuário `nicolas` com senha fixa no código, marcando-o como admin |
| `check_db.py` | Diagnóstico manual: imprime projetos e usuários no console, valida se `colunas` é um JSON válido |
| `verify_db.py` | Diagnóstico manual: imprime projetos com suas colunas parseadas e uma amostra dos primeiros 5 lançamentos v2 |

**Por que esses scripts existem fora de um framework de migrations**: sem Alembic (ou equivalente), qualquer alteração estrutural relevante (como a introdução do schema dinâmico `lancamentos_v2`) precisa de um script Python avulso, escrito sob medida, executado manualmente e sem rollback automatizado — reflexo direto da ausência de ORM/migrations mencionada na seção 1 e detalhada em `TechDebt.md`.

## 8. Tipo de dado usado para conteúdo dinâmico: `TEXT` em vez de `JSONB`

Tanto `projetos.colunas` quanto `lancamentos_v2.dados` são colunas `TEXT`, contendo uma string serializada via `json.dumps()`/`json.loads()` manual em Python — não `JSONB`, o tipo nativo do Postgres para dados semiestruturados.

**Consequência técnica**: o banco não valida que o conteúdo é um JSON bem formado (um `UPDATE` manual poderia gravar uma string qualquer sem erro), não é possível usar operadores nativos do Postgres (`->>`, `@>`, índices GIN) para consultar ou filtrar pelo conteúdo do JSON diretamente em SQL, e toda leitura/escrita desses campos depende inteiramente da aplicação fazer o parse corretamente (com tratamento de exceção manual em cada leitura — ver `lancamentos_controller.py`, que usa `try/except json.JSONDecodeError: pass` a cada linha lida).

**Motivo provável**: a escolha por `TEXT` + `json.dumps` manual é consistente com a origem em SQLite (que não tem tipo `JSON`/`JSONB` nativo — no SQLite, JSON também é guardado como texto). Ao migrar para Postgres, essa parte específica **não foi atualizada** para aproveitar `JSONB`, o que já está listado como pendência conhecida no roadmap do autor (`freatures.txt`: "usar JSONB para campos dinâmicos").
