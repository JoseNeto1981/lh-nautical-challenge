-- ============================================================
-- Questao 5 - Dimensao de Calendario
-- LH Nautical
-- ============================================================
-- Cenario: identificar o dia da semana com pior media de vendas
-- nas lojas fisicas (POS), corrigindo o erro do estagiario que
-- ignorou dias sem venda ao calcular a media.
-- ============================================================


-- ============================================================
-- PARTE 1 - Construcao da dimensao de datas (calendario)
-- Periodo: da menor data de venda ate a data atual do arquivo
-- (MAX(placed_at)), cobrindo todos os dias corridos, incluindo
-- fins de semana, MESMO que nao tenham venda registrada.
-- ============================================================

WITH periodo AS (
    SELECT
        MIN(placed_at)::date AS data_inicial,
        MAX(placed_at)::date AS data_final
    FROM orders
),

calendario AS (
    SELECT
        gs::date AS data_calendario,
        EXTRACT(DOW FROM gs)::int AS numero_dia_semana,
        CASE EXTRACT(DOW FROM gs)::int
            WHEN 0 THEN 'Domingo'
            WHEN 1 THEN 'Segunda-feira'
            WHEN 2 THEN 'Terca-feira'
            WHEN 3 THEN 'Quarta-feira'
            WHEN 4 THEN 'Quinta-feira'
            WHEN 5 THEN 'Sexta-feira'
            WHEN 6 THEN 'Sabado'
        END AS nome_dia_semana
    FROM periodo p
    CROSS JOIN LATERAL generate_series(p.data_inicial, p.data_final, interval '1 day') AS gs
)

SELECT *
FROM calendario
ORDER BY data_calendario;


-- ============================================================
-- PARTE 2 - LEFT JOIN do calendario com as vendas (lojas fisicas)
-- Agregacao de vendas por dia, com dias sem venda = 0.
-- ============================================================

WITH periodo AS (
    SELECT
        MIN(placed_at)::date AS data_inicial,
        MAX(placed_at)::date AS data_final
    FROM orders
),

calendario AS (
    SELECT
        gs::date AS data_calendario,
        EXTRACT(DOW FROM gs)::int AS numero_dia_semana,
        CASE EXTRACT(DOW FROM gs)::int
            WHEN 0 THEN 'Domingo'
            WHEN 1 THEN 'Segunda-feira'
            WHEN 2 THEN 'Terca-feira'
            WHEN 3 THEN 'Quarta-feira'
            WHEN 4 THEN 'Quinta-feira'
            WHEN 5 THEN 'Sexta-feira'
            WHEN 6 THEN 'Sabado'
        END AS nome_dia_semana
    FROM periodo p
    CROSS JOIN LATERAL generate_series(p.data_inicial, p.data_final, interval '1 day') AS gs
),

-- Vendas diarias: soma do valor de venda por dia, somente lojas
-- fisicas (channel = 'pos'). Agrega ANTES do LEFT JOIN com o
-- calendario, para nao duplicar linhas do calendario caso um
-- dia tenha mais de um pedido.
vendas_diarias AS (
    SELECT
        placed_at::date AS data_venda,
        SUM(total)       AS valor_venda_dia
    FROM orders
    WHERE channel = 'pos'
    GROUP BY placed_at::date
)

SELECT
    c.data_calendario,
    c.nome_dia_semana,
    COALESCE(v.valor_venda_dia, 0) AS valor_venda_dia
FROM calendario c
LEFT JOIN vendas_diarias v ON v.data_venda = c.data_calendario
ORDER BY c.data_calendario;


-- ============================================================
-- PARTE 3 - Media de vendas por dia da semana
-- Considera TODOS os dias do calendario (inclusive os com
-- venda = 0), respondendo a pergunta do Sr. Almir.
-- ============================================================

WITH periodo AS (
    SELECT
        MIN(placed_at)::date AS data_inicial,
        MAX(placed_at)::date AS data_final
    FROM orders
),

calendario AS (
    SELECT
        gs::date AS data_calendario,
        EXTRACT(DOW FROM gs)::int AS numero_dia_semana,
        CASE EXTRACT(DOW FROM gs)::int
            WHEN 0 THEN 'Domingo'
            WHEN 1 THEN 'Segunda-feira'
            WHEN 2 THEN 'Terca-feira'
            WHEN 3 THEN 'Quarta-feira'
            WHEN 4 THEN 'Quinta-feira'
            WHEN 5 THEN 'Sexta-feira'
            WHEN 6 THEN 'Sabado'
        END AS nome_dia_semana
    FROM periodo p
    CROSS JOIN LATERAL generate_series(p.data_inicial, p.data_final, interval '1 day') AS gs
),

vendas_diarias AS (
    SELECT
        placed_at::date AS data_venda,
        SUM(total)       AS valor_venda_dia
    FROM orders
    WHERE channel = 'pos'
    GROUP BY placed_at::date
),

calendario_com_vendas AS (
    SELECT
        c.data_calendario,
        c.numero_dia_semana,
        c.nome_dia_semana,
        COALESCE(v.valor_venda_dia, 0) AS valor_venda_dia
    FROM calendario c
    LEFT JOIN vendas_diarias v ON v.data_venda = c.data_calendario
)

SELECT
    numero_dia_semana,
    nome_dia_semana,
    COUNT(*)                     AS total_dias_no_periodo,
    SUM(valor_venda_dia)         AS soma_vendas,
    ROUND(AVG(valor_venda_dia), 2) AS media_vendas_dia
FROM calendario_com_vendas
GROUP BY numero_dia_semana, nome_dia_semana
ORDER BY media_vendas_dia ASC;