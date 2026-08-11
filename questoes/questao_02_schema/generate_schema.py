import csv
import os
import re
import glob
from datetime import datetime

# ---------- Configurações ----------
INPUT_DIR = "data/raw"
OUTPUT_FILE = "sql/schema.sql"

# Formatos de data/hora aceitos, do mais específico para o mais genérico
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
]
TIMESTAMP_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
]

BOOLEAN_VALUES = {"true", "false", "0", "1", "yes", "no", "t", "f"}

# Fragmentos de nome de coluna que indicam um identificador/documento,
# mesmo quando o conteúdo parece numérico (CPF, telefone, código de barras
# etc. podem ter zeros à esquerda e nunca são usados em cálculo, então
# devem ser tratados como texto, não como número).
IDENTIFIER_NAME_HINTS = {
    "cpf", "cnpj", "tax_id", "phone", "telefone", "barcode", "ean",
    "zip", "zipcode", "postal_code", "cep", "document", "documento",
    "nfe_access_key", "rg",
}

# Nomes de coluna considerados candidatos naturais a chave primária
PK_CANDIDATE_NAMES = {"id"}


def sanitize_identifier(name: str) -> str:
    """Normaliza nomes de coluna/tabela para o padrão do Postgres."""
    name = name.strip().lower()
    name = re.sub(r"[^\w]+", "_", name)   # espaços/símbolos -> underscore
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "col"
    if name[0].isdigit():                  # Postgres não aceita identificador iniciando com número
        name = f"col_{name}"
    return name


def is_identifier_like_name(column_name: str) -> bool:
    """Verifica se o NOME da coluna sugere um identificador/documento que
    deve ser tratado como texto, independente do conteúdo parecer numérico."""
    name = column_name.lower()
    return any(hint in name for hint in IDENTIFIER_NAME_HINTS)


def is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_boolean(value: str) -> bool:
    return value.strip().lower() in BOOLEAN_VALUES


def matches_date(value: str):
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def matches_timestamp(value: str):
    for fmt in TIMESTAMP_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def infer_column_type(column_name: str, values: list) -> str:
    """
    Recebe o nome da coluna e todos os seus valores (como string) e retorna
    o tipo de dado Postgres mais adequado.
    """
    non_empty = [v.strip() for v in values if v is not None and v.strip() != ""]

    if not non_empty:
        return "TEXT"  # coluna inteiramente vazia na amostra: fallback seguro

    # CORRECAO 1: identificadores/documentos (CPF, telefone, codigo de
    # barras etc.) sao tratados como texto mesmo quando o conteudo parece
    # numerico, pois podem ter zeros a esquerda e nao sao usados em calculo.
    if is_identifier_like_name(column_name):
        max_len = max(len(v) for v in non_empty)
        return "VARCHAR(255)" if max_len <= 255 else "TEXT"

    # CORRECAO 2: boolean e checado ANTES de int. Sem isso, colunas
    # booleanas representadas como "0"/"1" seriam classificadas como
    # INTEGER, ja que is_int("0") e is_int("1") tambem retornam True.
    if all(is_boolean(v) for v in non_empty):
        return "BOOLEAN"

    if all(is_int(v) for v in non_empty):
        max_abs = max(abs(int(v)) for v in non_empty)
        return "BIGINT" if max_abs > 2_147_483_647 else "INTEGER"

    if all(is_float(v) for v in non_empty):
        return "NUMERIC(18,4)"

    if all(matches_date(v) for v in non_empty):
        return "DATE"

    if all(matches_timestamp(v) for v in non_empty):
        return "TIMESTAMP"

    # Fallback: texto. Usa VARCHAR(255) se valores curtos, senao TEXT
    max_len = max(len(v) for v in non_empty)
    return "VARCHAR(255)" if max_len <= 255 else "TEXT"


def read_csv_full(filepath: str):
    """Lê o CSV inteiro (header + linhas) usando csv puro."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    return header, rows


def generate_create_table(table_name: str, header: list, rows: list) -> str:
    columns = [sanitize_identifier(col) for col in header]

    # Transpõe as linhas para ter, por coluna, a lista de valores
    col_values = {i: [] for i in range(len(columns))}
    for row in rows:
        for i in range(len(columns)):
            value = row[i] if i < len(row) else ""
            col_values[i].append(value)

    # CORRECAO 3: deteccao de PRIMARY KEY / NOT NULL.
    # Uma coluna e candidata a PK quando: o nome original e "id", todos os
    # valores sao preenchidos (sem vazios) e todos sao unicos.
    pk_index = None
    for i, original_name in enumerate(header):
        if original_name.strip().lower() in PK_CANDIDATE_NAMES:
            values = col_values[i]
            non_empty = [v.strip() for v in values if v.strip() != ""]
            has_no_nulls = len(non_empty) == len(values) and len(values) > 0
            is_unique = len(set(non_empty)) == len(non_empty)
            if has_no_nulls and is_unique:
                pk_index = i
                break

    col_definitions = []
    for i, col_name in enumerate(columns):
        col_type = infer_column_type(header[i], col_values[i])

        # NOT NULL: aplicado quando a coluna nao teve nenhum valor vazio
        # na amostra lida (alem de ser sempre aplicado a PK, abaixo)
        values = col_values[i]
        non_empty = [v for v in values if v.strip() != ""]
        has_no_nulls = len(non_empty) == len(values) and len(values) > 0

        if i == pk_index:
            col_definitions.append(f"    {col_name} {col_type} NOT NULL")
        elif has_no_nulls:
            col_definitions.append(f"    {col_name} {col_type} NOT NULL")
        else:
            col_definitions.append(f"    {col_name} {col_type}")

    if pk_index is not None:
        col_definitions.append(f"    PRIMARY KEY ({columns[pk_index]})")

    ddl = f"DROP TABLE IF EXISTS {table_name};\n"
    ddl += f"CREATE TABLE {table_name} (\n"
    ddl += ",\n".join(col_definitions)
    ddl += "\n);\n"
    return ddl


def main():
    csv_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.csv")))

    if not csv_files:
        print(f"Nenhum CSV encontrado em {INPUT_DIR}")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    all_ddls = [
        "-- Schema gerado automaticamente a partir dos CSVs de origem",
        f"-- Gerado em: {datetime.now().isoformat()}",
        "-- Banco de destino: PostgreSQL\n",
    ]

    for filepath in csv_files:
        table_name = sanitize_identifier(os.path.splitext(os.path.basename(filepath))[0])
        print(f"Processando {filepath} -> tabela '{table_name}'")

        header, rows = read_csv_full(filepath)
        ddl = generate_create_table(table_name, header, rows)
        all_ddls.append(ddl)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_ddls))

    print(f"\nSchema gerado com sucesso em: {OUTPUT_FILE}")
    print(f"Total de tabelas: {len(csv_files)}")


if __name__ == "__main__":
    main()
    