# Questão 6 - Previsão de Demanda

## Cenário

No último verão, o estoque de "Coletes Salva-Vidas" acabou em 3 meses, e a empresa perdeu vendas. Por outro lado, "Âncoras" foram compradas em excesso e estão paradas no galpão. O Tech Lead Gabriel Santos quer um modelo preditivo que diga quantas unidades serão vendidas no próximo mês, para ajustar as compras com fornecedores — em vez de decidir por "feeling".

## Premissas obrigatórias

- Período de treino: dados até 31/12/2025
- Período de teste: 1º trimestre de 2026 (Jan, Fev, Mar)
- Previsão em base mensal
- Produto analisado: "Bússola de Bordo 702"

## Achado prévio: ambiguidade de cadastro no produto analisado

Antes de construir o modelo, uma investigação nos dados revelou um problema de qualidade de cadastro que precisava ser resolvido: **existem dois produtos distintos na tabela `products`, com IDs diferentes (74 e 240), mas exatamente o mesmo nome** — "Bússola de Bordo 702".

| Campo | Produto id 74 | Produto id 240 |
|---|---|---|
| Nome | Bússola de Bordo 702 | Bússola de Bordo 702 |
| Descrição | Bússola magnética líquida com iluminação | Bússola magnética líquida com iluminação (idêntica) |
| `brand_id` | 12 | 8 |
| `category_id` | 8 | 7 |
| `ncm_code` | 18607512 | 91287147 |
| SKUs (variantes) | LHN-677223 (R$3.400,77), LHN-795790 (R$1.235,13) | LHN-304058 (R$1.758,87) |
| Total de vendas (histórico) | 330 itens | 142 itens |
| Vendas desde | Janeiro/2020 | Janeiro/2020 |

**Por que não é um caso de "produto novo substituindo o antigo":** ambos os produtos têm vendas registradas desde o início da série histórica (janeiro de 2020) até o fim de 2026, convivendo lado a lado durante todo o período — não há uma transição temporal de um para o outro. As datas de `created_at` (jan/2025 e jun/2026) provavelmente refletem apenas quando cada registro foi inserido no sistema atual, não quando o produto começou a ser comercializado.

**Também não é um padrão do dataset:** uma checagem em toda a família "Bússola de Bordo" confirmou que esse é o **único** nome duplicado entre produtos distintos — não é uma característica sistemática dos dados, é uma exceção pontual, aparentemente uma falha real de cadastro no ERP de origem (dois itens de estoque/fiscal distintos que, por algum motivo, receberam o mesmo nome comercial).

### Decisão tomada

Como o enunciado se refere ao produto pelo **nome** ("Bússola de Bordo 702"), e não há como saber com certeza qual dos dois IDs era o pretendido, a decisão foi **agregar as vendas de ambos os `product_id` como uma única série temporal**, filtrando a consulta por `p.name` em vez de `p.id`. Essa é uma decisão pragmática diante de uma ambiguidade real da base — documentada aqui para transparência, e sinalizada como um ponto que o time de dados/ERP deveria investigar e corrigir antes de decisões de compra baseadas nesse produto especificamente.

## Questão 6.1 - Script Python

### Dataset unificado

A série mensal de vendas foi construída unindo `products`, `product_variants`, `order_items` e `orders`, seguindo a cadeia de chaves:

```
orders → order_items → product_variants → products
```

```sql
SELECT
    DATE_TRUNC('month', o.placed_at)::date AS mes,
    SUM(oi.quantity)                        AS quantidade_vendida
FROM orders o
JOIN order_items oi       ON oi.order_id = o.id
JOIN product_variants pv  ON pv.id = oi.product_variant_id
JOIN products p           ON p.id = pv.product_id
WHERE p.name = 'Bússola de Bordo 702'
  AND o.placed_at < '2026-04-01'
GROUP BY DATE_TRUNC('month', o.placed_at)
ORDER BY mes;
```

Meses sem nenhuma venda foram explicitamente preenchidos com `0` (função `preencher_meses_sem_venda`), para que a série temporal não tivesse lacunas que distorceriam o cálculo da média móvel.

### Baseline: média móvel de 3 meses

Para cada mês do período de teste, a previsão é a média dos 3 meses **imediatamente anteriores** (dados já conhecidos naquele ponto do tempo):

```python
def media_movel(serie, mes_previsto, janela):
    meses_disponiveis = [m for m in serie.keys() if m < mes_previsto]
    ultimos_n = meses_disponiveis[-janela:]
    valores = [serie[m] for m in ultimos_n]
    return sum(valores) / len(valores)
```

Ver script completo em `previsao_demanda.py`, nesta mesma pasta.

## Resultado

### Série mensal (treino + teste)

A série completa cobre de janeiro/2020 a março/2026 (75 meses). Os últimos meses de treino e o trimestre de teste:

| Mês | Quantidade vendida | Conjunto |
|---|---:|---|
| 2025-10 | 34 | Treino |
| 2025-11 | 60 | Treino |
| 2025-12 | 22 | Treino |
| 2026-01 | 79 | **Teste** |
| 2026-02 | 68 | **Teste** |
| 2026-03 | 60 | **Teste** |

### Previsão vs. Realizado — 1º trimestre de 2026

| Mês | Previsto (média móvel 3m) | Realizado | Erro Absoluto |
|---|---:|---:|---:|
| 2026-01 | 38,67 | 79 | 40,33 |
| 2026-02 | 53,67 | 68 | 14,33 |
| 2026-03 | 56,33 | 60 | 3,67 |
| **Soma do trimestre** | **149** | **207** | — |

**MAE (Mean Absolute Error): 19,44 unidades**

### Como o MAE foi calculado

A fórmula do MAE é a média dos erros absolutos entre previsto e realizado:

$$MAE = \frac{1}{n} \sum |previsto - real|$$

Aplicando aos três meses do trimestre:

| Mês | Previsto | Realizado | Erro (previsto − real) | Erro Absoluto |
|---|---:|---:|---:|---:|
| 2026-01 | 38,67 | 79 | −40,33 | 40,33 |
| 2026-02 | 53,67 | 68 | −14,33 | 14,33 |
| 2026-03 | 56,33 | 60 | −3,67 | 3,67 |

$$MAE = \frac{40,33 + 14,33 + 3,67}{3} = \frac{58,33}{3} = 19,44$$

**O valor absoluto é o que faz a diferença aqui.** Se os erros fossem somados com o sinal original (sem `abs()`), erros para cima e para baixo poderiam se cancelar parcialmente, escondendo o tamanho real do erro do modelo. Usar o valor absoluto garante que o MAE meça "o quão longe, em média, a previsão ficou do real", independente da direção do erro — nesse caso, todos os três meses erraram na mesma direção (subestimando), então o MAE aqui coincide em módulo com a média simples dos erros, mas isso não seria garantido se o modelo tivesse superestimado em algum mês e subestimado em outro.

**Interpretação prática:** em média, cada previsão mensal do modelo ficou a cerca de 19-20 unidades de distância do valor real. Considerando que os valores reais do trimestre variaram entre 60 e 79 unidades, esse erro médio representa entre 25% e 32% do valor real de cada mês — um erro relativamente alto, reforçando o diagnóstico de que o baseline não acompanhou bem a tendência de crescimento da demanda no período.

## Questão 6.2 - Validação

**Pergunta:** Qual é a soma total da previsão de vendas (arredondada para número inteiro) para a "Bússola de Bordo 702" durante o 1º trimestre de 2026?

**Resposta: 149 unidades.**

(Soma de 38,67 + 53,67 + 56,33 = 148,67, arredondado para 149)

## Questão 6.3 - Explicação

### 1. Como o baseline foi construído?

O baseline é uma **média móvel de 3 meses**, aplicada de forma incremental (*rolling forecast*): para prever a demanda de um mês específico, o modelo calcula a média da quantidade vendida nos 3 meses imediatamente anteriores àquele mês.

- **Previsão de Jan/2026** = média de (Out/2025: 34, Nov/2025: 60, Dez/2025: 22) = 38,67
- **Previsão de Fev/2026** = média de (Nov/2025: 60, Dez/2025: 22, **Jan/2026: 79** — já conhecido, pois é passado no momento da previsão) = 53,67
- **Previsão de Mar/2026** = média de (Dez/2025: 22, Jan/2026: 79, **Fev/2026: 68**) = 56,33

A cada passo, o valor real do mês anterior passa a integrar a janela do mês seguinte — é assim que uma média móvel "anda junto" com o tempo, sempre usando os 3 meses mais recentes disponíveis até aquele ponto.

Antes do cálculo, a série mensal foi construída unindo `orders`, `order_items`, `product_variants` e `products`, somando a quantidade vendida por mês, filtrada pelo nome "Bússola de Bordo 702" (ver seção de achado acima sobre a decisão de somar dois `product_id` distintos).

### 2. Como evitou data leakage?

Data leakage, nesse contexto, seria usar informação do **futuro** (dados que só existiriam depois da data sendo prevista) para calcular a previsão — o que produziria um resultado artificialmente bom, inútil na prática, já que num cenário real essa informação futura não estaria disponível no momento da decisão de compra.

Duas garantias foram aplicadas no código:

- A função de média móvel filtra explicitamente `meses_disponiveis = [m for m in serie.keys() if m < mes_previsto]` — apenas meses **estritamente anteriores** ao mês sendo previsto entram no cálculo. Não existe caminho no código em que um mês igual ou posterior ao mês previsto seja usado em sua própria previsão.
- A previsão de Fevereiro/2026 usa o valor real de Janeiro/2026 — isso **não é vazamento**, porque, no momento em que a previsão de Fevereiro é gerada, Janeiro já é passado (já aconteceu, e seu valor real já seria conhecido por qualquer pessoa tomando essa decisão naquele momento). O que seria vazamento é usar o valor de Fevereiro ou Março para prever Janeiro — o filtro `m < mes_previsto` impede isso estruturalmente.

### 3. O baseline é adequado para esse produto?

**Não é totalmente adequado.** Os resultados mostram uma **subestimação sistemática** em todos os 3 meses do trimestre (erro absoluto de 40,33 / 14,33 / 3,67 unidades, sempre para menos), somando 58 unidades de diferença no trimestre (149 previstas vs. 207 vendidas — quase 28% abaixo do realizado). Isso indica que a demanda de "Bússola de Bordo 702" estava numa **tendência de crescimento** no início de 2026, e uma média móvel simples, por natureza, reage com atraso a esse tipo de mudança de padrão — ela sempre "olha para trás".

O erro decrescente ao longo do trimestre (de 40,33 em janeiro para 3,67 em março) reforça esse diagnóstico: o modelo está gradualmente se "recuperando" à medida que os valores mais altos de meses recentes entram na janela móvel, mas sempre um passo atrás da realidade.

### Limitação do método

A média móvel de 3 meses **não captura sazonalidade nem tendência**. O próprio cenário do desafio (esgotamento de estoque no verão) é um sinal de que a demanda de produtos náuticos tem picos sazonais previsíveis (verão, temporada de navegação). Uma média móvel simples trata os últimos meses como igualmente representativos do futuro próximo, sem nenhum mecanismo para reconhecer "estamos entrando na alta temporada" ou "a demanda está em trajetória de crescimento" — ela reage aos números observados, mas não antecipa mudanças de padrão que já são conhecidas do negócio. Isso é exatamente o que se observou nesta análise: a demanda real do 1º trimestre de 2026 cresceu mais rápido do que o modelo conseguiu acompanhar.

## Arquivos utilizados

- `previsao_demanda.py`: script completo (dataset unificado, baseline, previsão, MAE)

## Recomendação adicional

Além de responder à tarefa proposta, esta análise identificou uma inconsistência de cadastro (dois `product_id` com o mesmo nome) que deveria ser investigada e corrigida na origem dos dados. Enquanto isso não acontece, qualquer análise futura sobre "Bússola de Bordo 702" deve estar ciente de que o nome, sozinho, não identifica um produto único no sistema.
