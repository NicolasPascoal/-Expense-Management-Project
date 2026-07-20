import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import pool
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

PG_USER = os.getenv("PGUSER", "postgres")
PG_PASSWORD = os.getenv("PGPASSWORD", "postgres")
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DATABASE = os.getenv("PGDATABASE", "expense_management")

class PostgreSQLRow:
    """
    Wrapper para emular perfeitamente o comportamento de sqlite3.Row,
    suportando acesso por chave (nome da coluna), índice (posição),
    iteração e conversão via dict().
    """
    def __init__(self, cursor, row_tuple):
        self._fields = [desc[0] for desc in cursor.description]
        self._data = row_tuple
        self._mapping = {field: val for field, val in zip(self._fields, row_tuple)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        return self._mapping[key]

    def keys(self):
        return self._fields

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def get(self, key, default=None):
        return self._mapping.get(key, default)

    def items(self):
        return self._mapping.items()

    def __repr__(self):
        return f"PostgreSQLRow {dict(self.items())}"

class PostgreSQLCursorWrapper:
    """
    Wrapper para o cursor do psycopg2.
    Traduz automaticamente placeholders ? do SQLite para %s do PostgreSQL,
    e emula a propriedade lastrowid do SQLite usando lastval() do PostgreSQL.
    """
    def __init__(self, cursor, conn_wrapper):
        self._cursor = cursor
        self._conn_wrapper = conn_wrapper
        self._lastrowid = None

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def execute(self, sql, params=None):
        # 1. Ignorar comandos PRAGMA específicos do SQLite
        if "PRAGMA" in sql.upper():
            return self

        # 2. Traduzir o placeholder "?" do SQLite para "%s" do PostgreSQL
        sql_pg = sql.replace('?', '%s')

        # 3. Executar a query
        try:
            if params:
                # Garante que os parâmetros sejam passados como tupla ou lista
                if not isinstance(params, (tuple, list)):
                    params = (params,)
                self._cursor.execute(sql_pg, params)
            else:
                self._cursor.execute(sql_pg)
        except Exception as e:
            print(f"\n[QUERY FAILED] {sql_pg} | Params: {params} | Error: {e}")
            raise e

        # 4. Capturar lastrowid para comandos INSERT usando a função lastval()
        # Apenas se o INSERT não especificar a coluna 'id' explicitamente (para evitar abortar a transação)
        stripped_sql = sql.strip().upper()
        if stripped_sql.startswith("INSERT"):
            has_explicit_id = False
            first_paren = stripped_sql.find("(")
            second_paren = stripped_sql.find(")")
            if first_paren != -1 and second_paren != -1:
                cols_part = stripped_sql[first_paren+1:second_paren]
                cols = [c.strip() for c in cols_part.split(",")]
                if "ID" in cols:
                    has_explicit_id = True
            
            if not has_explicit_id:
                try:
                    temp_cursor = self._conn_wrapper._conn.cursor()
                    temp_cursor.execute("SELECT lastval()")
                    self._lastrowid = temp_cursor.fetchone()[0]
                    temp_cursor.close()
                except Exception:
                    self._lastrowid = None

        return self

    def executemany(self, sql, seq_of_params):
        if "PRAGMA" in sql.upper():
            return self

        sql_pg = sql.replace('?', '%s')
        self._cursor.executemany(sql_pg, seq_of_params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None:
            return None
        return PostgreSQLRow(self._cursor, row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [PostgreSQLRow(self._cursor, row) for row in rows]

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return self

    def __next__(self):
        row = self._cursor.fetchone()
        if row is None:
            raise StopIteration
        return PostgreSQLRow(self._cursor, row)

class PostgreSQLConnectionWrapper:
    """
    Wrapper para a conexão do psycopg2 para emular comportamentos específicos do sqlite3,
    como o método .execute() diretamente na conexão.
    """
    def __init__(self, conn, db_pool=None):
        self._conn = conn
        self._pool = db_pool

    def cursor(self, *args, **kwargs):
        # Retorna o nosso CursorWrapper em vez do cursor cru do psycopg2
        return PostgreSQLCursorWrapper(self._conn.cursor(), self)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._pool:
            self._pool.putconn(self._conn)
        else:
            self._conn.close()

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

_db_pool = None

def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados PostgreSQL usando um pool e retorna o wrapper.
    """
    global _db_pool
    if _db_pool is None:
        _db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE
        )
    conn = _db_pool.getconn()
    return PostgreSQLConnectionWrapper(conn, _db_pool)

from app.database.modelEmpresas import create_empresas_tables
from app.database.modelProjetos import create_projetos_tables
from app.database.modelCategoria import create_categorias_tables
from app.database.modelUsuarios import create_usuarios_tables
from app.database.modelRequisicoes import create_requisicoes_tables
from app.database.modelTarefas import create_tarefas_tables
from app.database.modelOrcamentos import create_orcamentos_tables
from app.database.modelEntradas import create_entradas_tables
from app.database.modelAuditoria import create_auditoria_tables

def init_db():
    """
    Inicializa o schema do banco de dados PostgreSQL se as tabelas não existirem.
    Organizado por modelos em arquivos separados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Executa a criação de cada tabela na ordem de dependência correta
    create_empresas_tables(cursor)
    create_projetos_tables(cursor)
    create_usuarios_tables(cursor)
    create_categorias_tables(cursor)
    create_requisicoes_tables(cursor)
    create_tarefas_tables(cursor)
    create_orcamentos_tables(cursor)
    create_entradas_tables(cursor)
    create_auditoria_tables(cursor)

    conn.commit()
    conn.close()
