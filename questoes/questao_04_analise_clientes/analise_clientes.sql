--  Ticket Medio e Diversidade de Categorias por cliente
-- (todos os clientes, sem filtro de elite)

WITH faturamento_frequencia AS (
    SELECT
        customer_id,
        SUM(total)  AS faturamento_total,
        COUNT(id)   AS frequencia
    FROM orders
    GROUP BY customer_id
),

diversidade_categorias AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT p.category_id) AS diversidade_categorias
    FROM orders o
    JOIN order_items oi      ON oi.order_id = o.id
    JOIN product_variants pv ON pv.id = oi.product_variant_id
    JOIN products p          ON p.id = pv.product_id
    GROUP BY o.customer_id
),

metrica_cliente AS (
    SELECT
        f.customer_id,
        f.faturamento_total,
        f.frequencia,
        ROUND(f.faturamento_total / f.frequencia, 2) AS ticket_medio,
        d.diversidade_categorias
    FROM faturamento_frequencia f
    JOIN diversidade_categorias d ON d.customer_id = f.customer_id
)

SELECT *
FROM metrica_cliente
ORDER BY ticket_medio DESC, customer_id ASC;


--  Filtro dos 10 clientes "Fieis"
-- Criterio: diversidade >= 13 categorias, maior Ticket Medio.
-- Desempate: customer_id crescente.


WITH faturamento_frequencia AS (
    SELECT
        customer_id,
        SUM(total)  AS faturamento_total,
        COUNT(id)   AS frequencia
    FROM orders
    GROUP BY customer_id
),

diversidade_categorias AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT p.category_id) AS diversidade_categorias
    FROM orders o
    JOIN order_items oi      ON oi.order_id = o.id
    JOIN product_variants pv ON pv.id = oi.product_variant_id
    JOIN products p          ON p.id = pv.product_id
    GROUP BY o.customer_id
),

metrica_cliente AS (
    SELECT
        f.customer_id,
        f.faturamento_total,
        f.frequencia,
        ROUND(f.faturamento_total / f.frequencia, 2) AS ticket_medio,
        d.diversidade_categorias
    FROM faturamento_frequencia f
    JOIN diversidade_categorias d ON d.customer_id = f.customer_id
)

SELECT *
FROM metrica_cliente
WHERE diversidade_categorias >= 13
ORDER BY ticket_medio DESC, customer_id ASC
LIMIT 10;


-- PARTE 3 - Categoria com maior SUM(quantity) entre os 10
-- clientes fieis identificados na Parte 2.


WITH faturamento_frequencia AS (
    SELECT
        customer_id,
        SUM(total)  AS faturamento_total,
        COUNT(id)   AS frequencia
    FROM orders
    GROUP BY customer_id
),

diversidade_categorias AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT p.category_id) AS diversidade_categorias
    FROM orders o
    JOIN order_items oi      ON oi.order_id = o.id
    JOIN product_variants pv ON pv.id = oi.product_variant_id
    JOIN products p          ON p.id = pv.product_id
    GROUP BY o.customer_id
),

metrica_cliente AS (
    SELECT
        f.customer_id,
        f.faturamento_total,
        f.frequencia,
        ROUND(f.faturamento_total / f.frequencia, 2) AS ticket_medio,
        d.diversidade_categorias
    FROM faturamento_frequencia f
    JOIN diversidade_categorias d ON d.customer_id = f.customer_id
),

top10_clientes AS (
    SELECT customer_id
    FROM metrica_cliente
    WHERE diversidade_categorias >= 13
    ORDER BY ticket_medio DESC, customer_id ASC
    LIMIT 10
)

SELECT
    p.category_id,
    c.name              AS categoria,
    SUM(oi.quantity)    AS total_itens_comprados
FROM top10_clientes t
JOIN orders o             ON o.customer_id = t.customer_id
JOIN order_items oi       ON oi.order_id = o.id
JOIN product_variants pv  ON pv.id = oi.product_variant_id
JOIN products p           ON p.id = pv.product_id
JOIN categories c         ON c.id = p.category_id
GROUP BY p.category_id, c.name
ORDER BY total_itens_comprados DESC
LIMIT 1;
