"""
Migração avulsa da Tarefa 1.1 (roadmap SaaS) para bancos que já existem
antes desta mudança (ex.: ambiente de desenvolvimento atual).

Em uma instalação nova, `init_db()` já cria `empresas` e a coluna
`empresa_id` em `usuarios`/`projetos` do zero — este script só é
necessário para adicionar a coluna e fazer o backfill em um banco que já
tinha dados sem ela.

Idempotente: pode ser executado mais de uma vez sem efeito colateral.
"""
from app.database.db import get_db_connection
from app.database.modelEmpresas import create_empresas_tables

EMPRESA_SEED_ID = 1


def migrate():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Garantir que a tabela empresas existe e tem a empresa seed
    create_empresas_tables(cursor)

    # 2. usuarios: adicionar coluna, fazer backfill, travar NOT NULL
    print("Adicionando empresa_id em 'usuarios'...")
    cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id)")
    cursor.execute("UPDATE usuarios SET empresa_id = ? WHERE empresa_id IS NULL", (EMPRESA_SEED_ID,))
    cursor.execute("ALTER TABLE usuarios ALTER COLUMN empresa_id SET NOT NULL")

    # 3. projetos: adicionar coluna, fazer backfill, travar NOT NULL
    print("Adicionando empresa_id em 'projetos'...")
    cursor.execute("ALTER TABLE projetos ADD COLUMN IF NOT EXISTS empresa_id INTEGER REFERENCES empresas(id)")
    cursor.execute("UPDATE projetos SET empresa_id = ? WHERE empresa_id IS NULL", (EMPRESA_SEED_ID,))
    cursor.execute("ALTER TABLE projetos ALTER COLUMN empresa_id SET NOT NULL")

    conn.commit()
    conn.close()
    print("Migração concluída: todos os usuários/projetos existentes foram vinculados à empresa seed "
          f"(id={EMPRESA_SEED_ID}, 'Obra Itanhaém').")


if __name__ == "__main__":
    migrate()
