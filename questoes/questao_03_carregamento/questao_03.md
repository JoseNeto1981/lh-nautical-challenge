# Questão 3 - Carregamento

## Cenário

Com o schema já criado (Questão 2), o próximo passo é carregar os dados reais dos CSVs dentro do banco PostgreSQL. Sem isso, o schema é só uma estrutura vazia — o carregamento é o que transforma o banco em uma base de dados utilizável para as análises seguintes.

## Premissas obrigatórias

- Carregamento de **todos** os CSVs (24 arquivos)
- Implementado em Python 3
- Permitido uso de bibliotecas externas para conexão e carga (usada `psycopg2-binary`)
- **Nenhum tratamento aplicado**: sem remoção de nulos, sem correção de caracteres especiais — carga bruta, tal como os dados existem no CSV

## Por que usar `COPY` em vez de `INSERT` linha a linha

Existem basicamente duas formas de levar dados de um CSV para o PostgreSQL via Python:

1. **Ler o CSV linha a linha e gerar `INSERT` para cada linha** — funciona, mas é lento (uma viagem ao banco por linha) e, principalmente, exige que o script decida como interpretar cada valor antes de inserir (ex: converter texto para número). Isso abre espaço para "tratamento" acidental dos dados, o que contraria a premissa da questão.

2. **Usar o comando `COPY` nativo do PostgreSQL** — o próprio banco lê o arquivo CSV inteiro de uma vez e insere os dados, interpretando os tipos com base no schema já criado. O script Python só abre o arquivo e entrega ele pro Postgres processar; nenhuma lógica de conversão passa pela mão do Python.

A opção 2 foi escolhida porque é: (a) muito mais rápida para volumes grandes (algumas tabelas têm mais de 100 mil linhas), e (b) mais alinhada à premissa de carga sem tratamento — o script não decide nada sobre o conteúdo, apenas transporta o arquivo até o banco.

## Como o script funciona

O script (`carregar_dados.py`) segue estes passos para cada CSV encontrado no diretório de origem:

1. **Deriva o nome da tabela** a partir do nome do arquivo (ex: `orders.csv` → tabela `orders`), usando a **mesma função de normalização** (`sanitize_identifier`) da Questão 2 — isso garante que o nome bata exatamente com a tabela já criada pelo `schema.sql`.

2. **Limpa a tabela antes de carregar** (`TRUNCATE TABLE ... RESTART IDENTITY`). Isso não é um "tratamento de dado" — é apenas o que permite rodar o script várias vezes sem erro de chave duplicada (`PRIMARY KEY`). Os dados em si não são alterados, só a tabela é esvaziada antes de receber a carga completa novamente.

3. **Executa o `COPY`**, apontando o arquivo CSV como fonte:
   ```sql
   COPY orders FROM STDIN WITH (
       FORMAT csv,
       HEADER true,
       DELIMITER ',',
       NULL ''
   )
   ```
   - `HEADER true` → ignora a primeira linha do CSV (nomes das colunas)
   - `NULL ''` → instrui o Postgres a tratar campo vazio (`""`) como `NULL`. Isso **não é uma limpeza** feita pelo script: é a própria definição do formato CSV — célula vazia representa ausência de valor. O dado chega ao banco exatamente como estava no arquivo.

4. Todo o processo roda dentro de uma **transação única**: se qualquer CSV falhar ao carregar, um `rollback` desfaz tudo, evitando um banco com carga parcial/inconsistente.

## Pré-requisitos para execução

```bash
pip install psycopg2-binary
```

Dependência registrada em `requirements.txt`, na raiz do projeto.

## Execução

```bash
python carregar_dados.py
```

O script se conecta ao PostgreSQL usando os parâmetros padrão do container Docker configurado na Questão 2 (`localhost:5432`, banco `lh_nautical`, usuário `postgres`). Esses parâmetros podem ser sobrescritos por variáveis de ambiente (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`), sem necessidade de alterar o código.

## Resultado do carregamento

Todos os 24 arquivos CSV foram carregados com sucesso, sem erros:

| Tabela | Linhas carregadas |
|---|---:|
| addresses | 3.998 |
| attributes | 8 |
| brands | 12 |
| categories | 14 |
| customers | 2.000 |
| employees | 15 |
| fiscal_invoices | 34.365 |
| goods_receipt_items | 4.733 |
| goods_receipts | 1.548 |
| locations | 6 |
| order_items | 147.320 |
| orders | 48.998 |
| payments | 53.546 |
| product_suppliers | 1.520 |
| product_variants | 1.009 |
| products | 500 |
| purchase_order_items | 6.059 |
| purchase_orders | 2.000 |
| return_items | 1.384 |
| returns | 980 |
| stock_levels | 6.054 |
| stock_movements | 115.312 |
| suppliers | 25 |
| variant_attribute_values | 2.018 |

## Validação

Duas checagens foram feitas para confirmar que a carga refletiu fielmente os dados de origem, sem perdas nem duplicações:

**1. Contagem de linhas bate com o CSV original**
```sql
SELECT COUNT(*) FROM orders;
-- 48998
```
Esse número é idêntico ao total de linhas identificado na Questão 1 (EDA), confirmando que nenhuma linha foi perdida ou duplicada na carga.

**2. Inspeção de amostra confirma tipos e nulos preservados**
```sql
SELECT * FROM orders LIMIT 3;
```
```
 id | order_number |  channel  | customer_id | salesperson_id | location_id |  status   |  subtotal  | discount_amount |   total    |      placed_at      
----+--------------+-----------+-------------+----------------+-------------+-----------+------------+-----------------+------------+---------------------
  1 | SO-000001    | ecommerce |        1136 |                |           1 | paid      |   323.3400 |         35.5700 |   287.7700 | 2022-09-06 05:37:37
  2 | SO-000002    | ecommerce |         618 |              9 |           4 | paid      | 53199.0500 |          0.0000 | 53199.0500 | 2023-02-03 04:36:21
```

Pontos confirmados nessa amostra:
- **Valores numéricos** (`subtotal`, `discount_amount`, `total`) chegaram como decimais corretos, respeitando o tipo `NUMERIC(18,4)` definido no schema.
- **Nulo preservado sem tratamento**: a linha 1 tem `salesperson_id` vazio — exatamente como especificado na premissa de não tratar nulos. O dado ausente permanece ausente, não foi preenchido nem removido.
- **Nenhuma corrupção de caractere** nos campos de texto (`ecommerce`, `pos`, `paid`, `confirmed`).

## Questão 3.2 - Validação

**Pergunta:** Qual o total de linhas somadas das seguintes tabelas: `customers`, `orders`, `order_items` e `payments`?

Consulta executada diretamente no container PostgreSQL:

```bash
docker exec -it lh-postgres psql -U postgres -d lh_nautical -c "SELECT (SELECT COUNT(*) FROM customers) + (SELECT COUNT(*) FROM order_items) + (SELECT COUNT(*) FROM orders) + (SELECT COUNT(*) FROM payments) AS total_linhas_somadas;"
```

Query em formato SQL puro (equivalente, para leitura):
```sql
SELECT
    (SELECT COUNT(*) FROM customers) +
    (SELECT COUNT(*) FROM order_items) +
    (SELECT COUNT(*) FROM orders) +
    (SELECT COUNT(*) FROM payments) AS total_linhas_somadas;
```

Resultado retornado pelo terminal:
```
 total_linhas_somadas 
----------------------
               251864
(1 row)
```

| Tabela | Linhas |
|---|---:|
| customers | 2.000 |
| orders | 48.998 |
| order_items | 147.320 |
| payments | 53.546 |
| **Total somado** | **251.864** |

**Resposta: 251.864 linhas.**

Esse valor bate exatamente com a soma dos totais individuais já registrados na carga (Questão 3.1), confirmando que nenhuma linha foi perdida ou duplicada entre a carga inicial e essa checagem — reforçando a integridade do processo de carregamento.

## Conclusão

O carregamento foi concluído com sucesso para as 24 tabelas, com volumes e valores consistentes com os dados de origem. Como o schema da Questão 2 não define `FOREIGN KEY` (apenas `PRIMARY KEY`), não houve necessidade de respeitar uma ordem específica de carregamento entre tabelas — cada CSV foi carregado de forma independente. O banco está agora pronto para servir de base às análises relacionais das próximas etapas do desafio.

## Script utilizado

Ver arquivo `carregar_dados.py` nesta mesma pasta.
