import os
from datetime import date
from collections import OrderedDict

import psycopg2


PRODUTO_ALVO = "Bússola de Bordo 702"

DATA_FIM_TREINO = date(2025, 12, 31)
MESES_TESTE = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]

JANELA_MEDIA_MOVEL = 3  

DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "lh_nautical"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "postgres"),
}

# Dataset unificado

def carregar_vendas_mensais(conn, nome_produto: str) -> "OrderedDict[date, float]":
    """Une products, product_variants, orders e order_items para obter a
    quantidade vendida por mes do produto informado, do inicio da serie ate
    o fim do periodo de teste (Mar/2026).

    A cadeia de chaves percorrida e:
        orders -> order_items -> product_variants -> products
    (mesma cadeia usada na Questao 4, aqui agregada por mes em vez de
    por cliente/categoria).
    """
    query = """
        SELECT
            DATE_TRUNC('month', o.placed_at)::date AS mes,
            SUM(oi.quantity)                        AS quantidade_vendida
        FROM orders o
        JOIN order_items oi       ON oi.order_id = o.id
        JOIN product_variants pv  ON pv.id = oi.product_variant_id
        JOIN products p           ON p.id = pv.product_id
        WHERE p.name = %s
          AND o.placed_at < %s
        GROUP BY DATE_TRUNC('month', o.placed_at)
        ORDER BY mes;
    """
   
    limite_superior = date(2026, 4, 1)

    with conn.cursor() as cur:
        cur.execute(query, (nome_produto, limite_superior))
        linhas = cur.fetchall()

    vendas_por_mes = OrderedDict()
    for mes, quantidade in linhas:
        vendas_por_mes[mes] = float(quantidade)

    return vendas_por_mes


def preencher_meses_sem_venda(vendas_por_mes: "OrderedDict[date, float]") -> "OrderedDict[date, float]":
    """Garante que todo mes entre o primeiro e o ultimo mes da serie exista
    no dicionario, mesmo que nao tenha havido nenhuma venda naquele mes
    (quantidade = 0). Isso evita "buracos" na serie temporal que
    distorceriam a media movel."""
    if not vendas_por_mes:
        return vendas_por_mes

    primeiro_mes = next(iter(vendas_por_mes))
    ultimo_mes = list(vendas_por_mes.keys())[-1]

    serie_completa = OrderedDict()
    ano, mes = primeiro_mes.year, primeiro_mes.month
    while (ano, mes) <= (ultimo_mes.year, ultimo_mes.month):
        chave = date(ano, mes, 1)
        serie_completa[chave] = vendas_por_mes.get(chave, 0.0)
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1

    return serie_completa


# Baseline de media movel + previsao do 1o trimestre de 2026

def media_movel(serie: "OrderedDict[date, float]", mes_previsto: date, janela: int) -> float:
    """Calcula a media dos 'janela' meses IMEDIATAMENTE ANTERIORES ao mes
    previsto, usando apenas dados ja conhecidos naquele ponto do tempo
    (sem olhar para o futuro)."""
    meses_disponiveis = [m for m in serie.keys() if m < mes_previsto]
    ultimos_n = meses_disponiveis[-janela:]

    if len(ultimos_n) < janela:
        raise ValueError(
            f"Nao ha {janela} meses de historico anteriores a {mes_previsto} "
            f"para calcular a media movel (apenas {len(ultimos_n)} disponiveis)."
        )

    valores = [serie[m] for m in ultimos_n]
    return sum(valores) / len(valores)


def gerar_previsoes(serie_treino_e_real: "OrderedDict[date, float]", meses_teste: list, janela: int):
    """Gera a previsao para cada mes de teste, em ordem cronologica.
    A cada passo, o valor REAL do mes anterior (se ja tiver sido
    'observado' na linha do tempo) passa a fazer parte da janela do
    proximo mes -- e assim que uma media movel simples funciona na
    pratica (rolling forecast one-step-ahead)."""
    previsoes = OrderedDict()

    for mes in meses_teste:
        previsao = media_movel(serie_treino_e_real, mes, janela)
        previsoes[mes] = previsao

    return previsoes



# Comparacao com o realizado (MAE)


def calcular_mae(previsoes: "OrderedDict[date, float]", realizados: "OrderedDict[date, float]") -> float:
    erros_absolutos = []
    for mes, previsto in previsoes.items():
        real = realizados.get(mes, 0.0)
        erros_absolutos.append(abs(previsto - real))
    return sum(erros_absolutos) / len(erros_absolutos)


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        print(f"Carregando serie mensal de vendas para: {PRODUTO_ALVO}\n")

        vendas_brutas = carregar_vendas_mensais(conn, PRODUTO_ALVO)
        serie = preencher_meses_sem_venda(vendas_brutas)

        print("Serie mensal completa (quantidade vendida por mes):")
        for mes, qtd in serie.items():
            marcador = "[TREINO]" if mes.year < 2026 else "[TESTE] "
            print(f"  {marcador} {mes.strftime('%Y-%m')}: {qtd:.0f}")

        
        previsoes = gerar_previsoes(serie, MESES_TESTE, JANELA_MEDIA_MOVEL)

        realizados = OrderedDict((mes, serie[mes]) for mes in MESES_TESTE)

        print("\nPrevisao (media movel 3 meses) vs. Realizado - Q1 2026:")
        print(f"  {'Mes':<10} {'Previsto':>12} {'Realizado':>12} {'Erro Abs.':>12}")
        for mes in MESES_TESTE:
            previsto = previsoes[mes]
            real = realizados[mes]
            erro = abs(previsto - real)
            print(f"  {mes.strftime('%Y-%m'):<10} {previsto:>12.2f} {real:>12.2f} {erro:>12.2f}")

        mae = calcular_mae(previsoes, realizados)
        soma_previsao_trimestre = sum(previsoes.values())

        print(f"\nMAE (Mean Absolute Error): {mae:.2f}")
        print(f"Soma da previsao para o 1o trimestre de 2026 (arredondada): {round(soma_previsao_trimestre)}")
        print(f"Soma REALIZADA no 1o trimestre de 2026: {sum(realizados.values()):.0f}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
