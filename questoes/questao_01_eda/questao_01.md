# Questão 1 - EDA (Análise Exploratória de Dados)

## Cenário

Antes de qualquer análise, modelagem ou tomada de decisão, é fundamental entender o que existe nos dados. O Sr. Almir quer uma resposta simples: **"Posso confiar nesses dados para tomar decisões?"**

Esta questão realiza uma análise exploratória inicial na tabela `orders`, respondendo perguntas básicas — porém críticas — sobre volume, distribuição e qualidade dos dados.

## Premissas obrigatórias

- Utilizada apenas a tabela `orders`
- Nenhuma limpeza ou tratamento foi aplicado aos dados
- Apenas observação, agregação e descrição

## Metodologia

- **Ferramenta:** DuckDB (via terminal)
- **Fonte de dados:** `orders.csv`
- **Execução:** comandos SQL rodados a partir da raiz do projeto

## Resultados

### Parte 1 - Visão geral da tabela `orders`

| Métrica | Valor |
|---|---|
| Total de linhas | 48.998 |
| Total de colunas | 13 |
| Data mínima (`created_at`) | 2020-01-01 01:19:28 |
| Data máxima (`created_at`) | 2026-12-31 23:43:09 |

### Parte 2 - Análise de valores numéricos (`total`)

| Métrica | Valor |
|---|---|
| Valor mínimo | 32,62 |
| Valor máximo | 127.262,02 |
| Valor médio | 28.704,99 |
| Valores nulos em `total` | 0 |
| Valores negativos em `total` | 0 |
| Valores nulos em `created_at` | 0 |

## Parte 3 - Interpretação / Diagnóstico

**Diagnóstico geral:** a tabela `orders` é estruturalmente confiável nas colunas auditadas (sem nulos, sem negativos), mas apresenta pontos que exigem atenção antes de ser usada como base para decisões de negócio.

### Possíveis outliers em `total`

A média (28.704,99) está muito mais próxima do valor máximo (127.262,02) do que do valor mínimo (32,62), o que indica uma distribuição assimétrica à direita. Isso sugere que um grupo pequeno de pedidos de alto valor está puxando a média para cima, e que **a média sozinha não representa bem o "pedido típico"**.

**Recomendação:** calcular mediana, desvio padrão e percentis (p95/p99) para confirmar o grau de assimetria antes de usar `total` em relatórios ou KPIs.

### Qualidade dos dados

- Nenhum valor nulo encontrado nas colunas `created_at` e `total`.
- Nenhum valor negativo encontrado em `total`.
- A data máxima (`2026-12-31`) está no futuro em relação à data atual, o que é um forte indício de dado sintético/gerado para fins do desafio — mas essa é uma suposição, não uma confirmação, e deve ser documentada como ressalva.
- Apenas 2 das 13 colunas da tabela foram auditadas quanto a nulos; as demais colunas (prováveis IDs, status, chaves estrangeiras) ainda não foram verificadas.

### A tabela está pronta para análises?

**Não integralmente.** Antes de análises mais profundas ou decisões estratégicas, recomenda-se:

1. Tratar/decidir explicitamente como lidar com os outliers de `total` antes de qualquer cálculo de média ou KPI.
2. Esclarecer e documentar a natureza da data futura em `created_at`.
3. Auditar as demais colunas da tabela quanto a nulos e inconsistências.
4. Relacionar `orders` com tabelas complementares (ex: clientes, produtos, pagamentos) para validar consistência de negócio de ponta a ponta — uma tabela isolada garante apenas integridade interna, não coerência com o restante do sistema.

**Resposta direta ao Sr. Almir:** os dados são utilizáveis para uma análise exploratória inicial, como esta, mas não é recomendado tomar decisões estratégicas com base neles sem antes tratar os outliers de `total` e esclarecer a questão da data futura.

## Queries utilizadas

```sql
-- Parte 1: Visão geral
SELECT COUNT(*) AS total_linhas FROM orders;

SELECT COUNT(*) AS total_colunas
FROM information_schema.columns
WHERE table_name = 'orders';

SELECT 
    MIN(created_at) AS data_min, 
    MAX(created_at) AS data_max
FROM orders;

-- Parte 2: Análise numérica de "total"
SELECT 
    MIN(total) AS total_min,
    MAX(total) AS total_max,
    AVG(total) AS total_medio,
    COUNT(*) FILTER (WHERE total IS NULL) AS nulos_total,
    COUNT(*) FILTER (WHERE total < 0) AS negativos_total
FROM orders;

-- Checagem de nulos por coluna relevante
SELECT 
    COUNT(*) - COUNT(created_at) AS nulos_created_at,
    COUNT(*) - COUNT(total) AS nulos_total
FROM orders;
```