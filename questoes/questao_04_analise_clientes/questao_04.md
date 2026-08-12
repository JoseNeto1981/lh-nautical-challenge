# Questão 4 - Análise de Clientes

## Cenário

A Diretoria da LH Nautical deseja identificar os clientes fiéis. Diferente de quem compra muito uma única vez, o cliente fiel é definido como aquele que possui um **gasto médio alto por transação** e **navega por diversas categorias da loja**. O objetivo é mapear o que esses clientes de elite consomem, para replicar o comportamento em outros segmentos.

## Premissas obrigatórias

- **Faturamento Total**: soma da coluna `total` por cliente
- **Frequência**: contagem total de transações (IDs de venda) por cliente
- **Ticket Médio**: Faturamento Total / Frequência
- **Diversidade de Categorias**: quantidade de categorias distintas (`category_id`) que o cliente comprou
- **Filtro de Elite**: apenas clientes com 13 ou mais categorias distintas
- **Desempate**: em caso de empate no Ticket Médio, `customer_id` em ordem crescente

## Questão 4.1 - Abordagem

### Mapeamento da cadeia de chaves

Nenhuma tabela reúne, numa única linha, faturamento, frequência e categoria ao mesmo tempo — essa informação está espalhada em tabelas diferentes, com granularidades diferentes:

- **Faturamento e Frequência** vêm direto de `orders` (uma linha = uma transação).
- **Diversidade de categorias** exige atravessar a cadeia de relacionamento:
  ```
  orders → order_items → product_variants → products → categories
  ```
  (pedido → item comprado naquele pedido → variante do produto → produto → categoria do produto)

Misturar as duas granularidades num único `JOIN` direto geraria "explosão de linhas": cada pedido apareceria duplicado uma vez por item comprado, inflando o Faturamento Total se somado depois desse cruzamento. Por isso, a solução foi calcular Faturamento/Frequência e Diversidade de Categorias em **CTEs separadas**, e só uni-las no final por `customer_id`.

### Query utilizada

```sql
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
```

O `COUNT(DISTINCT p.category_id)` é o ponto-chave da diversidade: garante que uma categoria comprada várias vezes conte como **1**, não como múltiplas ocorrências. O filtro `WHERE diversidade_categorias >= 13` só é aplicado **depois** da agregação (dentro da CTE `metrica_cliente`), já que o critério de elite depende de um valor que só existe após o `GROUP BY`.

### Resultado: os 10 clientes fiéis

| Posição | customer_id | Faturamento Total | Frequência | Ticket Médio | Diversidade |
|---|---|---:|---:|---:|---:|
| 1 | 22 | 1.087.838,44 | 26 | 41.839,94 | 14 |
| 2 | 1477 | 916.262,58 | 22 | 41.648,30 | 14 |
| 3 | 929 | 1.082.775,89 | 26 | 41.645,23 | 14 |
| 4 | 1116 | 655.737,20 | 16 | 40.983,58 | 14 |
| 5 | 1691 | 815.471,30 | 20 | 40.773,57 | 14 |
| 6 | 774 | 726.127,99 | 18 | 40.340,44 | 14 |
| 7 | 1470 | 1.040.553,09 | 26 | 40.021,27 | 14 |
| 8 | 1599 | 997.616,46 | 25 | 39.904,66 | 14 |
| 9 | 965 | 677.297,78 | 17 | 39.841,05 | 14 |
| 10 | 1722 | 1.146.455,22 | 29 | 39.532,94 | 14 |

**Observação:** todos os 10 clientes fiéis apresentam diversidade **exatamente igual a 14** categorias — nenhum com o mínimo de 13, e nenhum com 15 ou mais. Isso sugere que 14 pode ser um teto natural de diversidade de categorias no catálogo da loja para o perfil de cliente de maior ticket médio, algo que vale investigar em uma análise futura (ex: quantas categorias existem no total, e se 14 representa quase a totalidade delas).

## Questão 4.2 - Explicação

### 1. Como cheguei nas categorias mais vendidas? (mapeamento da cadeia de chaves)

A mesma cadeia de relacionamento usada para calcular diversidade foi reaproveitada para somar `quantity` por categoria, restrita aos 10 clientes fiéis:

```
orders (pedido)
   → order_items (o que foi comprado naquele pedido, com quantity)
      → product_variants (qual variante de produto foi comprada)
         → products (produto, que tem category_id)
            → categories (nome da categoria)
```

Cada seta é um `JOIN`: `order_items.order_id = orders.id`, `order_items.product_variant_id = product_variants.id`, `product_variants.product_id = products.id`, `products.category_id = categories.id`. Só depois de percorrer essa cadeia inteira cada linha da consulta reúne, ao mesmo tempo, a categoria do produto e a quantidade comprada — permitindo agrupar por categoria e somar `quantity`.

### 2. Que lógica utilizei para filtrar os clientes com diversidade mínima?

A diversidade foi calculada numa CTE própria (`diversidade_categorias`), percorrendo a cadeia de chaves e usando `COUNT(DISTINCT p.category_id)` — o `DISTINCT` é o que garante que compras repetidas na mesma categoria contem como uma categoria só, não uma vez por item. O filtro `WHERE diversidade_categorias >= 13` foi aplicado sobre o resultado dessa agregação (na CTE `metrica_cliente`), e não como uma condição sobre linhas individuais de `orders` — o critério de elite só existe depois que a contagem de categorias distintas já foi calculada por cliente.

### 3. Como garanti que a contagem de itens refletisse apenas os Top 10?

O resultado exato da Questão 4.1 (10 clientes já filtrados e ordenados) foi isolado em uma CTE própria, `top10_clientes`:

```sql
top10_clientes AS (
    SELECT customer_id
    FROM metrica_cliente
    WHERE diversidade_categorias >= 13
    ORDER BY ticket_medio DESC, customer_id ASC
    LIMIT 10
)
```

A consulta final parte dessa CTE, não de `orders` diretamente:

```sql
FROM top10_clientes t
JOIN orders o ON o.customer_id = t.customer_id
```

Como o primeiro `JOIN` exige que o `customer_id` do pedido exista em `top10_clientes`, nenhum pedido de cliente fora do grupo de elite entra na soma. Essa ordem importa: se o filtro dos 10 clientes fosse aplicado só no fim (depois de somar `quantity` de todo mundo), haveria risco de contar itens de clientes que não deveriam estar no grupo. Por isso o filtro do Top 10 precisa acontecer **antes** da agregação por categoria, não depois.

### Query utilizada (Parte 3)

```sql
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
```

### Resultado

| category_id | categoria | total_itens_comprados |
|---|---|---:|
| 8 | Hélices | 492 |

## Conclusão

Entre os 10 clientes fiéis (ticket médio mais alto, com diversidade de compra em 14 categorias distintas), a categoria que concentra a maior quantidade de itens comprados é **Hélices**, com **492 unidades**. Esse é o sinal mais forte de comportamento de consumo desse grupo de elite — uma pista concreta para a Diretoria sobre qual categoria priorizar ao tentar replicar esse padrão de fidelidade em outros segmentos de clientes.

## Arquivo utilizado

Ver `analise_clientes.sql` nesta mesma pasta, contendo as três partes da análise (métricas completas, filtro dos 10 clientes fiéis, e categoria vencedora).
