import os

import pandas as pd
import numpy as np
import psycopg2
from sklearn.metrics.pairwise import cosine_similarity

# ---------- Configurações ----------
PRODUTO_REFERENCIA = "Motor de Popa 1949"
TOP_N = 5

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "lh_nautical"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}


# ---------------------------------------------------------------------------
# Etapa 1: matriz de interacao Usuario x Produto
# ---------------------------------------------------------------------------

def carregar_pares_cliente_produto(conn) -> pd.DataFrame:
    """Traz do banco todos os pares (customer_id, product_id, product_name)
    distintos em que o cliente comprou o produto pelo menos uma vez.

    DISTINCT ja garante presenca/ausencia (ignora quantidade e numero de
    pedidos repetidos), atendendo a regra "1 se comprou ao menos uma vez".
    """
    query = """
        SELECT DISTINCT
            o.customer_id,
            p.id   AS product_id,
            p.name AS product_name
        FROM orders o
        JOIN order_items oi       ON oi.order_id = o.id
        JOIN product_variants pv  ON pv.id = oi.product_variant_id
        JOIN products p           ON p.id = pv.product_id;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        linhas = cur.fetchall()
        colunas = [desc[0] for desc in cur.description]

    return pd.DataFrame(linhas, columns=colunas)


def construir_matriz_usuario_produto(pares: pd.DataFrame) -> pd.DataFrame:
    """Pivota os pares (customer_id, product_id) em uma matriz onde:
        - linhas   = id_cliente
        - colunas  = id_produto
        - valores  = 1 se o cliente comprou o produto, 0 caso contrario
    """
    pares = pares.copy()
    pares["comprou"] = 1

    matriz = pares.pivot_table(
        index="customer_id",
        columns="product_id",
        values="comprou",
        fill_value=0,
        aggfunc="max",  # garante 1 mesmo se, por algum motivo, houver mais de uma linha
    )

    return matriz.astype(int)


# ---------------------------------------------------------------------------
# Etapa 2: similaridade de cosseno entre produtos
# ---------------------------------------------------------------------------

def calcular_similaridade_produtos(matriz_usuario_produto: pd.DataFrame) -> pd.DataFrame:
    """Calcula a similaridade de cosseno PRODUTO x PRODUTO, com base nos
    vetores de clientes que compraram cada um (colunas da matriz).

    cosine_similarity espera amostras nas LINHAS, entao transpomos a
    matriz (produtos passam a ser linhas, clientes as colunas) antes de
    calcular.
    """
    matriz_produto_cliente = matriz_usuario_produto.T  # produtos nas linhas
    similaridade = cosine_similarity(matriz_produto_cliente.values)

    return pd.DataFrame(
        similaridade,
        index=matriz_produto_cliente.index,
        columns=matriz_produto_cliente.index,
    )


# ---------------------------------------------------------------------------
# Etapa 3: ranking de produtos similares
# ---------------------------------------------------------------------------

def obter_ranking_similares(
    similaridade: pd.DataFrame,
    produto_id_referencia: int,
    mapa_id_para_nome: dict,
    top_n: int,
) -> pd.DataFrame:
    """Retorna os top_n produtos mais similares ao produto de referencia,
    desconsiderando o proprio produto no ranking."""
    scores = similaridade.loc[produto_id_referencia].drop(index=produto_id_referencia)
    top = scores.sort_values(ascending=False).head(top_n)

    ranking = pd.DataFrame({
        "product_id": top.index,
        "product_name": [mapa_id_para_nome[pid] for pid in top.index],
        "similaridade": top.values,
    })
    ranking.index = range(1, len(ranking) + 1)  # posicao no ranking (1o, 2o, ...)
    return ranking


# ---------------------------------------------------------------------------
# Execucao principal
# ---------------------------------------------------------------------------

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        print("Carregando pares cliente-produto...")
        pares = carregar_pares_cliente_produto(conn)
        print(f"  -> {len(pares)} pares distintos (cliente, produto) carregados.")

        # Mapa id -> nome (para exibir o ranking com nomes, nao so IDs)
        mapa_id_para_nome = (
            pares[["product_id", "product_name"]]
            .drop_duplicates()
            .set_index("product_id")["product_name"]
            .to_dict()
        )

        # Alerta de seguranca: mesmo problema encontrado na Questao 6 pode
        # se repetir aqui -- nomes de produto duplicados em product_id
        # diferentes.
        candidatos = pares.loc[
            pares["product_name"] == PRODUTO_REFERENCIA, "product_id"
        ].unique()

        if len(candidatos) == 0:
            raise ValueError(f"Produto '{PRODUTO_REFERENCIA}' nao encontrado nas vendas.")
        if len(candidatos) > 1:
            print(
                f"\nAVISO: existem {len(candidatos)} product_id diferentes com o "
                f"nome '{PRODUTO_REFERENCIA}': {list(candidatos)}. "
                f"Usando o de maior volume de compradores distintos."
            )
            candidatos = sorted(
                candidatos,
                key=lambda pid: (pares["product_id"] == pid).sum(),
                reverse=True,
            )

        produto_id_referencia = int(candidatos[0])
        print(f"\nProduto de referencia: '{PRODUTO_REFERENCIA}' (product_id={produto_id_referencia})")

        print("\nConstruindo matriz usuario x produto...")
        matriz = construir_matriz_usuario_produto(pares)
        print(f"  -> Matriz com {matriz.shape[0]} clientes x {matriz.shape[1]} produtos.")

        print("\nCalculando similaridade de cosseno produto x produto...")
        similaridade = calcular_similaridade_produtos(matriz)

        print(f"\nTop {TOP_N} produtos mais similares a '{PRODUTO_REFERENCIA}':\n")
        ranking = obter_ranking_similares(
            similaridade, produto_id_referencia, mapa_id_para_nome, TOP_N
        )
        for posicao, linha in ranking.iterrows():
            print(f"  {posicao}. {linha['product_name']} (similaridade: {linha['similaridade']:.4f})")

        print(f"\nProduto MAIS similar: {ranking.iloc[0]['product_name']} "
              f"(similaridade: {ranking.iloc[0]['similaridade']:.4f})")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
    