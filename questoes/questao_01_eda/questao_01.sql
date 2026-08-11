-- Parte 1
SELECT COUNT(*) AS total_linhas FROM orders;

SELECT COUNT(*) AS total_colunas
FROM information_schema.columns
WHERE table_name = 'orders';

SELECT 
    MIN(created_at) AS data_min, 
    MAX(created_at) AS data_max
FROM orders;

-- Parte 2
SELECT 
    MIN(total) AS total_min,
    MAX(total) AS total_max,
    AVG(total) AS total_medio,
    COUNT(*) FILTER (WHERE total IS NULL) AS nulos_total,
    COUNT(*) FILTER (WHERE total < 0) AS negativos_total
FROM orders;

-- Checagem geral de nulos (repita por coluna relevante)
SELECT 
    COUNT(*) - COUNT(created_at) AS nulos_created_at,
    COUNT(*) - COUNT(total) AS nulos_total
FROM orders;
