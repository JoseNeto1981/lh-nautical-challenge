import os
import re
import sys
import glob
import psycopg2

# ---------- Configurações ----------
# Mesmo diretório de origem usado na Questão 2, para manter consistência
# entre o schema gerado e os dados carregados.
INPUT_DIR = "data/raw"

# Parâmetros de conexão. Podem ser sobrescritos por variáveis de ambiente,
# para não deixar credenciais fixas no código-fonte.
DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "lh_nautical"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}


def sanitize_identifier(name: str) -> str:
    """Normaliza nomes de tabela para o padrão do Postgres.

    Mantida IDÊNTICA à função usada em gerar_schema.py (Questão 2), para
    garantir que o nome da tabela derivado do CSV seja exatamente o mesmo
    nome já criado no banco pelo schema.sql.
    """
    name = name.strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "col"
    if name[0].isdigit():
        name = f"col_{name}"
    return name


def get_csv_files(input_dir: str):
    return sorted(glob.glob(os.path.join(input_dir, "*.csv")))


def load_csv(cursor, filepath: str):
    """Carrega um único CSV na tabela correspondente via COPY nativo do
    Postgres. Nenhuma transformação é aplicada aos dados: o COPY lê o
    arquivo linha a linha e insere exatamente o que está no CSV, respeitando
    os tipos já definidos pelo schema (a conversão de tipo é feita pelo
    próprio Postgres a partir do texto do CSV, não pelo script)."""

    table_name = sanitize_identifier(os.path.splitext(os.path.basename(filepath))[0])
    print(f"Carregando {filepath} -> tabela '{table_name}'...")

    # TRUNCATE antes da carga: torna o script reexecutável sem violar a
    # PRIMARY KEY em uma segunda execução. Não é "tratamento de dado" --
    # apenas garante idempotência do carregamento em si.
    cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")

    with open(filepath, "r", encoding="utf-8") as f:
        copy_sql = f"""
            COPY {table_name} FROM STDIN WITH (
                FORMAT csv,
                HEADER true,
                DELIMITER ',',
                NULL ''
            )
        """
        cursor.copy_expert(copy_sql, f)

    print(f"  -> {cursor.rowcount} linhas carregadas.")


def main():
    input_dir = sys.argv[1] if len(sys.argv) > 1 else INPUT_DIR

    csv_files = get_csv_files(input_dir)
    if not csv_files:
        print(f"Nenhum CSV encontrado em {input_dir}")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            for filepath in csv_files:
                load_csv(cur, filepath)
        conn.commit()
        print(f"\nCarregamento concluido com sucesso. Total de arquivos: {len(csv_files)}")
    except Exception as e:
        conn.rollback()
        print(f"\nErro durante o carregamento -- rollback aplicado. Detalhe: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()    
    