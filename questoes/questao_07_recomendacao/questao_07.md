# Questão 7 - Sistema de Recomendação

## Cenário

A Marina percebeu que clientes que compram lanchas quase sempre esquecem de levar a defensa (proteção lateral). Ela quer implementar uma vitrine de "Quem comprou isso, também levou..." no site. Sem ferramentas de Big Data caras, o motor de recomendação precisa ser construído a partir da similaridade de comportamento de compra dos clientes — identificando qual produto deve ser recomendado junto ao item **"Motor de Popa 1949"**.

## Tarefa

1. Construir uma matriz de interação Usuário × Produto (1 se o cliente comprou o produto ao menos uma vez, 0 caso contrário — ignorando quantidade)
2. Calcular a Similaridade de Cosseno entre os vetores dos produtos
3. Gerar um ranking dos 5 produtos mais similares ao "Motor de Popa 1949", excluindo ele mesmo

## Questão 7.1 - Script Python

### Bibliotecas utilizadas

`pandas`, `numpy` e `sklearn.metrics.pairwise.cosine_similarity` — todas dentro do conjunto autorizado pelo enunciado. `psycopg2` foi usado apenas para trazer os dados do PostgreSQL (mesma abordagem já usada nas Questões 3 e 6).

### Etapa 1 — Matriz Usuário × Produto

Os pares (cliente, produto) foram obtidos com uma única query, usando `DISTINCT` para já garantir a regra "1 se comprou ao menos uma vez, ignorando quantidade":

```sql
SELECT DISTINCT
    o.customer_id,
    p.id   AS product_id,
    p.name AS product_name
FROM orders o
JOIN order_items oi       ON oi.order_id = o.id
JOIN product_variants pv  ON pv.id = oi.product_variant_id
JOIN products p           ON p.id = pv.product_id;
```

A cadeia de chaves percorrida é a mesma já utilizada nas Questões 4 e 6: `orders → order_items → product_variants → products`.

Esses pares foram então pivotados com `pandas.pivot_table`, gerando a matriz binária:

```python
matriz = pares.pivot_table(
    index="customer_id",
    columns="product_id",
    values="comprou",
    fill_value=0,
    aggfunc="max",
)
```

- **Linhas**: `customer_id`
- **Colunas**: `product_id`
- **Valores**: `1` se o cliente comprou o produto ao menos uma vez, `0` caso contrário

### Etapa 2 — Similaridade de Cosseno entre produtos

```python
matriz_produto_cliente = matriz_usuario_produto.T  # produtos passam a ser as linhas
similaridade = cosine_similarity(matriz_produto_cliente.values)
```

A matriz foi **transposta** antes do cálculo porque `cosine_similarity` do scikit-learn compara **linhas** entre si — como o objetivo é comparar produtos (não clientes), os produtos precisam ocupar as linhas nesse momento específico do processamento.

### Etapa 3 — Ranking dos 5 produtos mais similares

```python
scores = similaridade.loc[produto_id_referencia].drop(index=produto_id_referencia)
top = scores.sort_values(ascending=False).head(5)
```

O próprio produto de referência é removido do ranking (`.drop(index=produto_id_referencia)`) antes de ordenar e pegar os 5 maiores — evitando que ele apareça "similar a si mesmo" (o que sempre resultaria em similaridade 1,0, distorcendo o ranking).

### Proteção contra nomes de produto duplicados

A Questão 6 revelou que o dataset tem pelo menos um caso de dois `product_id` diferentes com o mesmo nome ("Bússola de Bordo 702"). Por precaução, o script verifica isso também para "Motor de Popa 1949": se houver mais de um `product_id` com esse nome, o script avisa e usa o de maior volume de compradores distintos, em vez de escolher arbitrariamente. Na execução real, **não houve ambiguidade** — apenas um `product_id` (180) corresponde a esse nome.

Ver script completo em `sistema_recomendacao.py`, nesta mesma pasta.

## Resultado

- **135.508 pares** distintos (cliente, produto) carregados
- **Matriz de 2.000 clientes × 500 produtos** — consistente com os totais já confirmados nas Questões 1 e 2
- Produto de referência: **Motor de Popa 1949** (`product_id = 180`)

### Ranking dos 5 produtos mais similares

| Posição | Produto | Similaridade (cosseno) |
|---|---|---:|
| 1 | Motor de Popa 5331 | 0,2566 |
| 2 | Cabo Náutico 2105 | 0,2562 |
| 3 | Vela Mestra 1913 | 0,2558 |
| 4 | Cabo Náutico 9048 | 0,2393 |
| 5 | GPS Plotter 6249 | 0,2377 |

## Questão 7.2 - Validação

**Pergunta:** Qual é o nome do produto com MAIOR similaridade ao "Motor de Popa 1949"?

**Resposta: Motor de Popa 5331**, com similaridade de cosseno de **0,2566**.

### Observação sobre a magnitude dos valores

Todos os valores de similaridade ficaram numa faixa relativamente baixa e próxima entre si (0,2377 a 0,2566) — a diferença entre o 1º e o 5º colocado é de apenas 0,0189. Isso é esperado num catálogo de 500 produtos e 2.000 clientes: a chance de dois produtos específicos serem comprados exatamente pelo mesmo subconjunto de clientes é naturalmente pequena, então nenhuma similaridade tende a ser "alta" em termos absolutos. O que importa nesse tipo de análise é a **ordem relativa** (ranking), não o valor absoluto do cosseno.

Também vale observar que o produto mais similar encontrado foi **outro motor de popa** (modelo diferente), e não uma "defensa" como a Marina hipotetizou no cenário. Isso não invalida o resultado — reflete o padrão de compra real registrado nos dados (clientes que compram um motor tendem a comprar outro modelo, possivelmente para reposição ou embarcações diferentes) — mas é uma diferença interessante entre a expectativa qualitativa do negócio e o que o modelo, baseado puramente em co-ocorrência de compra, efetivamente encontrou.

## Questão 7.3 - Explicação

### 1. Como a matriz foi construída?

A matriz Usuário × Produto foi construída em duas etapas. Primeiro, uma consulta SQL trouxe todos os pares distintos `(customer_id, product_id)` em que houve pelo menos uma compra — o `DISTINCT` na query já elimina naturalmente a informação de quantidade e de pedidos repetidos, atendendo à regra de "presença/ausência apenas". Em seguida, esses pares foram pivotados com `pandas.pivot_table`, transformando a lista de pares em uma matriz onde cada linha representa um cliente (`customer_id`), cada coluna representa um produto (`product_id`), e cada célula contém `1` (o cliente comprou aquele produto ao menos uma vez) ou `0` (nunca comprou). Células sem nenhuma ocorrência na lista de pares foram preenchidas com `0` via `fill_value=0`.

### 2. O que significa a similaridade de cosseno nesse contexto?

A similaridade de cosseno mede o quão parecido é o **padrão de clientes** que compraram dois produtos, tratando cada produto como um vetor onde cada posição representa um cliente (1 se ele comprou aquele produto, 0 se não comprou). O cosseno do ângulo entre dois desses vetores varia de 0 (nenhum cliente em comum entre os dois produtos) a 1 (exatamente o mesmo conjunto de clientes compra ambos os produtos, na mesma proporção).

Nesse contexto de recomendação, dois produtos com similaridade de cosseno alta significam: **os clientes que compraram o produto A tendem fortemente a também comprar o produto B** (e vice-versa) — é essa correlação de comportamento de compra que sustenta a lógica de "quem comprou isso, também levou aquilo". A métrica não usa quantidade nem valor de compra, apenas o padrão binário de presença/ausência entre os clientes.

### 3. Uma limitação desse método de recomendação

O método (filtragem colaborativa baseada em item, usando apenas presença/ausência) **ignora completamente informações de contexto e semântica dos produtos** — ele não sabe que "Motor de Popa" e "Defensa" são itens complementares por natureza (um protege o barco onde o outro é instalado); ele só enxerga se os mesmos clientes historicamente compraram os dois. Isso tem duas consequências práticas:

- **Produtos genuinamente complementares, mas ainda pouco vendidos juntos**, não aparecem bem ranqueados simplesmente por falta de histórico suficiente — o modelo não tem como "entender" que uma defensa devia acompanhar um motor, só pode aprender isso observando compras passadas.
- **Cold start**: um produto novo no catálogo, sem nenhum histórico de venda, não tem como ser comparado a nada — sua linha na matriz seria inteiramente zero, tornando sua similaridade com qualquer outro produto sempre 0, mesmo que ele fosse, na prática, um complemento óbvio de algum item popular.

Esse é o motivo pelo qual o resultado da Questão 7.2 recomendou outro motor de popa em vez de uma defensa: o modelo captura corretamente correlação estatística de compra, mas não tem nenhum mecanismo para incorporar conhecimento de domínio (como "motores e defensas são usados juntos na prática náutica") além do que os próprios dados de venda já revelam.

## Arquivo utilizado

Ver `sistema_recomendacao.py` nesta mesma pasta.