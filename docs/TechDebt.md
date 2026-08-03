# Tech Debt — Expense Management Project

> Documento de inventário. Nenhum item foi corrigido ou refatorado nesta etapa.

## 1. Camada de compatibilidade SQLite→PostgreSQL (`app/database/db.py`)

**O que é**: três classes wrapper (`PostgreSQLRow`, `PostgreSQLCursorWrapper`, `PostgreSQLConnectionWrapper`) que traduzem, em tempo de execução, a sintaxe e o comportamento do `sqlite3` para o `psycopg2`.

**Por que é dívida técnica**: todo código novo de acesso a dados precisa "pensar em SQLite" (usar `?` como placeholder, evitar `INSERT` com `id` explícito se depender de `lastrowid`, lembrar que comandos `PRAGMA` são silenciosamente ignorados). Recursos nativos do Postgres — `RETURNING`, CTEs, window functions, `JSONB` com operadores, `UPSERT` (`ON CONFLICT`) — não são naturalmente adotados porque o código está estruturado em torno de uma abstração que "esconde" o Postgres por trás de uma API de SQLite. Qualquer desenvolvedor que só conheça Postgres (não SQLite) vai estranhar por que as queries usam `?` em vez de `%s`, e precisa entender essa camada de tradução antes de escrever uma query nova com segurança.

## 2. Ausência de ORM e de ferramenta de migrations

**O que é**: todo o schema é definido via `CREATE TABLE IF NOT EXISTS` espalhado em 5 arquivos `model*.py`, executado a cada subida do processo (`init_db()`). Alterações estruturais (adicionar coluna, mudar tipo, renomear tabela) exigem escrever um script Python avulso (como já ocorreu com `migrate_to_v2.py`).

**Por que é dívida técnica**: não há histórico de "quais alterações de schema já foram aplicadas em qual ambiente" — o controle é feito via checagens ad-hoc (`SELECT COUNT(*) ... IF 0`) dentro de cada script, sem uma tabela de controle de versão de schema (como o Alembic mantém). Não há rollback automatizado de uma alteração de schema. O roadmap do próprio autor (`freatures.txt`) já lista "usar ORM (SQLAlchemy)" e "preparar migrations (Alembic)" como item futuro, confirmando que esta lacuna já é conhecida.

## 3. JSON armazenado como `TEXT` em vez de `JSONB`

**O que é**: `projetos.colunas` e `lancamentos_v2.dados` são colunas `TEXT` contendo JSON serializado manualmente via `json.dumps`/`json.loads` em Python.

**Por que é dívida técnica**: o banco não valida que o conteúdo é JSON bem formado; não há como usar operadores nativos do Postgres (`->>`, `@>`, índices GIN) para consultar por conteúdo; toda agregação (soma por categoria, por conta) precisa ser feita fora do banco, trazendo todos os registros para a aplicação (ver `Performance.md`). Também listado no roadmap do autor como pendência ("usar JSONB para campos dinâmicos").

## 4. Ausência de validação de schema/tipos no backend

**O que é**: não há Marshmallow, Pydantic, ou qualquer biblioteca de validação de payload. Toda validação é manual, campo a campo (`if not campo: erro`), e cobre apenas presença/ausência — nunca tipo, formato ou tamanho.

**Por que é dívida técnica**: o schema dinâmico de `lancamentos_v2.dados` (definido por `projetos.colunas`) não é verificado contra o payload recebido — um cliente pode enviar qualquer estrutura de JSON, com campos faltando, extras, ou de tipo incorreto (ex.: uma string onde se esperava número), e o backend aceita e persiste sem erro. A responsabilidade de manter a consistência recai inteiramente sobre o frontend (que também não valida de forma completa — só o campo `data` é checado em `saveForm`).

## 5. Inconsistência arquitetural: nem todo domínio passa por `controller/`

**O que é**: `projeto_routes.py` e partes de `requisicao_routes.py` acessam `get_db_connection()` diretamente dentro do arquivo de rotas, enquanto `lancamentos`, `servicos` (categorias/contas), `usuarios` e `tarefas` centralizam a lógica em módulos de `controller/` dedicados.

**Por que é dívida técnica**: não há um padrão único e previsível de "onde a lógica de um domínio mora" — cada novo desenvolvedor precisa investigar caso a caso. Isso também dificulta testar a lógica de negócio isoladamente para os domínios que não têm controller (não há como importar e testar uma função de "criar projeto" sem simular uma requisição HTTP completa, já que a lógica está embutida na view).

## 6. "God Hook" no frontend (`useExpenses.js`)

**O que é**: um único hook customizado de ~570 linhas concentrando estado e lógica de negócio de 7+ domínios diferentes (autenticação, projetos, lançamentos, categorias, contas, requisições, tarefas, usuários, filtros, modais, import/export CSV).

**Por que é dívida técnica**: qualquer alteração nesse arquivo tem potencial de efeito colateral em partes não relacionadas do estado; o hook não pode ser testado unitariamente por domínio sem mockar o restante; o arquivo tende a crescer ainda mais conforme o roadmap de features avança (orçamento, parcelamento, anexos, etc. adicionariam ainda mais responsabilidades a este mesmo arquivo, seguindo o padrão atual).

## 7. Duas tabelas de lançamento coexistindo (`lancamentos` legada + `lancamentos_v2` ativa)

**O que é**: a tabela `lancamentos` (schema fixo, sem `projeto_id`) não é mais usada por nenhuma rota ativa da API, mas continua sendo criada em todo `init_db()` e populada apenas pelo script `seed_db.py`.

**Por que é dívida técnica**: qualquer pessoa nova no projeto encontra duas tabelas de "lançamento" e precisa investigar o histórico de migração (`migrate_to_v2.py`) para entender qual é a ativa. É uma fonte de confusão sem benefício funcional atual, mantida "por compatibilidade" segundo o próprio comentário no código.

## 8. Ausência total de testes automatizados

**O que é**: não há `pytest`, `unittest`, nem qualquer suíte de testes em backend ou frontend. Os únicos "testes" existentes são scripts de diagnóstico manual (`check_db.py`, `verify_db.py`), que imprimem informação no console para inspeção humana, não são testes automatizados com asserções.

**Por que é dívida técnica**: qualquer alteração de código (incluindo correções de bugs simples) não tem uma rede de segurança automatizada para detectar regressões. Isso aumenta o risco percebido de qualquer refatoração futura, especialmente na camada de compatibilidade SQLite→Postgres (item 1) e no "God Hook" (item 6), que são justamente os pontos mais frágeis a mexer sem cobertura de teste.

## 9. Ausência de CI/CD

**O que é**: não há `.github/workflows` nem qualquer outro pipeline de integração contínua configurado no repositório.

**Por que é dívida técnica**: não há verificação automática de lint, build ou (ausência de) testes a cada mudança — qualquer erro de sintaxe, import quebrado, ou regressão só é percebido manualmente, ao rodar a aplicação localmente ou em produção.

## 10. Duplicidade de dados de seed (categoria duplicada)

**O que é**: a constante `CATEGORIAS` em `front/src/data/constants.js` contém tanto `"Mão de obra"` quanto `"Mao de obra"` (sem acento) como entradas distintas.

**Por que é dívida técnica**: é sintoma direto da ausência de normalização/deduplicação no fluxo de importação de CSV (que cria categorias novas automaticamente a partir do texto encontrado no arquivo, sem normalizar acentuação/case antes de comparar com as já existentes) — um indício concreto, nos próprios dados, de que esse comportamento automático já gerou uma inconsistência real em uso.

## 11. Redundância de campos de autorização (`is_admin` + `role`)

**O que é**: a tabela `usuarios` mantém dois campos que se sobrepõem parcialmente — `is_admin` (inteiro 0/1) e `role` (string livre) — sincronizados manualmente via lógica de seed (`UPDATE usuarios SET role = 'admin' WHERE is_admin = 1`), mas não há garantia de consistência caso um dos dois seja alterado isoladamente por um novo endpoint futuro (hoje não existe um `PUT /usuarios/:id` que permita isso, mas a ausência desse endpoint também é, em si, uma limitação funcional, não uma proteção arquitetural deliberada).

**Por que é dívida técnica**: dois campos representando a mesma informação de formas diferentes é uma fonte clássica de bugs de sincronização caso a aplicação cresça e algum novo código atualize apenas um dos dois.

## 12. Scripts de manutenção sem padronização nem proteção

**O que é**: `create_admin.py`, `seed_db.py`, `migrate_to_v2.py`, `migrate_sqlite_to_postgres.py`, `check_db.py`, `verify_db.py` são scripts Python soltos na raiz de `back/`, executáveis diretamente, sem confirmação interativa, sem flag de "dry-run", e (no caso de `create_admin.py`) com credenciais hardcoded (ver também `Security.md`).

**Por que é dívida técnica**: não há um padrão de "comando de gerência" (como os `management commands` do Django, ou um CLI dedicado com Click/Typer) que centralize essas operações administrativas de forma mais seguras e documentadas — cada script é uma ilha com sua própria convenção.

## 13. README não customizado

**O que é**: `front/README.md` é o texto genérico gerado pelo template `create-vite`, sem qualquer informação específica deste projeto. Não existe um README de alto nível na raiz do repositório.

**Por que é dívida técnica**: qualquer pessoa nova precisa descobrir por conta própria como rodar o projeto, quais variáveis de ambiente são necessárias, e o que cada parte faz — informação que só está disponível, hoje, através da leitura direta do código-fonte (o que esta própria documentação busca suprir).
