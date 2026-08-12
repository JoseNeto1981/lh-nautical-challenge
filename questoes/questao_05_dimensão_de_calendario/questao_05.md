# Questão 5 - Dimensão de Calendário

## Cenário

O Sr. Almir quer saber: *"Qual é o dia da semana, nas lojas físicas, temos a pior média de vendas?"*, para decidir se vale a pena fechar a loja nesses dias.

Um estagiário fez um `GROUP BY dia_semana` direto na tabela de vendas e concluiu que o **Domingo** era ótimo, com média de R$ 5.000,00. O problema: em muitos domingos a loja abriu mas vendeu zero. Como esses dias não existem na tabela `orders` (não há linha para "dia sem venda"), eles foram ignorados no cálculo da média, **inflando artificialmente o resultado**. A correção exige construir um calendário de datas (dimensão de datas) e cruzá-lo com as vendas, garantindo que todo dia do período — com ou sem venda — entre no cálculo.

## Premissas obrigatórias

- Período de análise: todas as datas entre a menor e a maior data de venda presentes no arquivo
- A loja esteve aberta em todos os dias do período (inclusive fins de semana)
- Considerar apenas lojas físicas (`channel = 'pos'`)
- Dias sem registro em `orders` devem entrar no cálculo com valor de venda = 0
- "Vendas diárias" = soma do valor de venda por dia
- A média por dia da semana deve considerar todos os dias do calendário, inclusive os sem venda
- Nome do dia da semana em português

## Questão 5.1 - Abordagem e código SQL

### Por que `generate_series` e não `EXTRACT(DOW)` com `to_char`

O PostgreSQL tem uma função nativa (`to_char(data, 'TMDay')`) que retornaria o nome do dia da semana diretamente, mas ela depende do **locale do banco** estar configurado como `pt_BR`. Como o container Docker usado no projeto não tem essa garantia (o padrão costuma ser `en_US`), a abordagem escolhida foi mais portável: usar `EXTRACT(DOW FROM data)` — que retorna um número de 0 (Domingo) a 6 (Sábado) de forma independente de locale — e mapear esse número para o nome em português via `CASE`.

Para gerar o calendário em si, foi usada a função `generate_series(data_inicial, data_final, interval '1 day')`, que cria uma linha para cada dia do intervalo, de forma nativa no PostgreSQL — sem precisar de tabela auxiliar, loop ou biblioteca externa.

### Construção da dimensão de datas (Parte 1)

```sql
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
```

**Resultado:** 2.557 dias gerados, cobrindo o período de `2020-01-01` até a maior data de `placed_at` presente em `orders`.

### Cruzamento com as vendas (Parte 2)

```sql
WITH vendas_diarias AS (
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
```

Dois pontos técnicos importantes:
- **A agregação de vendas acontece antes do `LEFT JOIN`** (na CTE `vendas_diarias`), não depois. Se o `JOIN` fosse feito direto contra `orders` sem agregação prévia, cada pedido do dia geraria uma linha extra, duplicando o calendário.
- **`COALESCE(v.valor_venda_dia, 0)`**: converte o `NULL` (dia sem nenhuma venda física) em `0`, exatamente como pedido na premissa.

**Resultado:** 2.557 linhas — o mesmo total do calendário, confirmando que o `LEFT JOIN` preservou todos os dias, mesmo os sem venda.

### Média por dia da semana (Parte 3 — resposta à pergunta do Sr. Almir)

```sql
SELECT
    numero_dia_semana,
    nome_dia_semana,
    COUNT(*)                       AS total_dias_no_periodo,
    SUM(valor_venda_dia)           AS soma_vendas,
    ROUND(AVG(valor_venda_dia), 2) AS media_vendas_dia
FROM calendario_com_vendas
GROUP BY numero_dia_semana, nome_dia_semana
ORDER BY media_vendas_dia ASC;
```

## Resultado final

| Dia da semana | Dias no período | Soma de vendas (R$) | Média de vendas/dia (R$) |
|---|---:|---:|---:|
| **Quinta-feira** | 366 | 57.518.480,61 | **157.154,32** |
| Domingo | 365 | 57.529.887,95 | 157.616,13 |
| Segunda-feira | 365 | 57.758.021,43 | 158.241,15 |
| Sábado | 365 | 60.173.268,58 | 164.858,27 |
| Terça-feira | 365 | 60.633.373,26 | 166.118,83 |
| Sexta-feira | 365 | 62.120.694,25 | 170.193,68 |
| Quarta-feira | 366 | 63.539.589,22 | 173.605,44 |

**Resposta ao Sr. Almir: o dia com a pior média de vendas nas lojas físicas é a Quinta-feira**, com média de R$ 157.154,32/dia — não o Domingo, como o estagiário havia concluído.

### O erro do estagiário, quantificado

O cálculo corrigido mostra que o Domingo, na verdade, tem a **segunda pior** média (R$ 157.616,13) — próxima da Quinta-feira, não um "dia ótimo" como reportado. A média de R$ 5.000,00 do estagiário estava **cerca de 31 vezes menor** que o valor real (R$ 157.616,13), justamente porque ele dividiu a soma de vendas apenas pelos domingos que tiveram ao menos uma venda registrada, ignorando todos os domingos "vazios" — que, sendo dias sem faturamento, deveriam ter reduzido a média, não sido excluídos dela.

## Questão 5.2 - Explicação

### 1. Por que é necessário utilizar uma tabela de datas (calendário) em vez de agrupar diretamente a tabela de vendas?

A tabela `orders` só contém uma linha quando **existe** uma venda — ela não tem como representar "esse dia a loja abriu e vendeu zero", porque simplesmente não existe registro nenhum para esse dia. Um `GROUP BY` direto em `orders` calcula a média dividindo a soma de vendas apenas pelos dias que aparecem na tabela (ou seja, dias com pelo menos uma venda), ignorando por completo os dias sem nenhum pedido.

A dimensão de datas resolve isso porque ela é **gerada de forma independente da tabela de vendas** — representa o calendário real (todo dia em que a loja esteve aberta, segundo a premissa do exercício), não os dias em que houve transação. Ao fazer um `LEFT JOIN` do calendário para `orders`, cada dia do calendário aparece uma vez, com ou sem venda associada; os dias sem venda ficam com `NULL` (convertido para `0` via `COALESCE`), entrando corretamente no denominador do cálculo de média.

### 2. O que aconteceria com a média de vendas se um dia da semana tivesse muitos dias sem nenhuma venda registrada?

A média ficaria **artificialmente inflada** — exatamente o erro cometido pelo estagiário. Isso acontece porque, ao ignorar os dias sem venda, o denominador da média (quantidade de dias) fica menor do que deveria, considerando só os dias "bons". Quanto maior a proporção de dias sem venda em um dia da semana específico, maior a distorção: no caso do Domingo, dividir a soma de vendas apenas pelos domingos com venda (em vez de todos os domingos do período) fez a média parecer artificialmente baixa a ponto de sugerir "ótimo desempenho", quando na realidade o dia tem desempenho mediano a fraco quando todos os dias — inclusive os de venda zero — são considerados.

Esse é o risco central de ignorar dias ausentes numa análise de série temporal: **dias sem evento não são "dados faltantes" que devem ser descartados — são informação real** (a loja abriu e não vendeu nada), e precisam contar no denominador para que a média reflita o desempenho verdadeiro do dia da semana.

## Arquivo utilizado

Ver `dimensao_calendario.sql` nesta mesma pasta, contendo as três partes da análise (construção do calendário, cruzamento diário com as vendas, e a média final por dia da semana).