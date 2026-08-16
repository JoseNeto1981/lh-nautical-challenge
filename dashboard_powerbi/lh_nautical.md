# Dashboard Power BI — LH Nautical

## Objetivo

Material complementar de visualização, consolidando os principais achados das análises de negócio em um dashboard interativo — complementar ao [relatório final](../relatorio_final/relatorio_final_completo.pdf).

## Conteúdo

Arquivo `dashboard_lh_nautical.pbix`, com 5 páginas:

| Página | Conteúdo | Frente do desafio |
|---|---|---|
| **Kpis_Gerais** | Cartões de KPI (total de pedidos, clientes, produtos, ticket médio, faturamento) + volumetria por tabela | EDA / Tratamento de Dados |
| **Clientes_Fieis** | Ranking dos 10 clientes fiéis por ticket médio + tabela detalhada | Análise de Clientes |
| **Vendas_por_dia_da_semana** | Média de vendas por dia da semana, com Quinta-feira destacada como pior dia | Análise de Vendas |
| **Previsão_Demanda** | Previsto vs. realizado (1º trimestre 2026) + MAE | Previsão de Demanda |
| **Recomendacao_de_Produtos** | Ranking de similaridade de cosseno, com o produto de maior similaridade destacado | Sistemas de Recomendação |

## Fonte dos dados

- **Páginas 1, 2 e 3** (Kpis_Gerais, Clientes_Fieis, Vendas_por_dia_da_semana): conectadas diretamente ao PostgreSQL via Consulta Nativa (SQL), usando as mesmas queries já validadas nas Questões 4 e 5 do desafio.
- **Páginas 4 e 5** (Previsão_Demanda, Recomendacao_de_Produtos): dados inseridos manualmente (Inserir Dados / Enter Data), pois os resultados originais foram calculados em Python (média móvel e similaridade de cosseno via scikit-learn), não em SQL — não fazia sentido recalcular no Power BI algo que já havia sido calculado e validado no script `.py` correspondente.

## Como reproduzir a conexão

Pré-requisito: container PostgreSQL ativo (`docker start lh-postgres`).

1. Abrir o `.pbix` no Power BI Desktop
2. Se solicitado, atualizar as credenciais de conexão:
   - **Servidor:** `localhost`
   - **Banco de dados:** `lh_nautical`
   - **Usuário/senha:** `postgres` / `postgres`
3. **Atualizar dados** (Home → Atualizar) para trazer os valores mais recentes do banco

## Decisões técnicas

- **Consulta Nativa em vez de navegação de tabelas**: as queries SQL já validadas nas questões do desafio foram usadas diretamente como Instrução SQL na conexão do Power BI, evitando risco de recalcular alguma métrica de forma diferente do que já foi documentado.
- **Paleta de cores consistente com o relatório final**: azul (`#2a78d6`) para dados neutros, vermelho (`#e34948`) para destaque do ponto mais relevante de cada página (pior caso na análise de vendas, melhor caso no ranking de recomendação).

## Limitações conhecidas

- As Páginas 4 e 5 não se atualizam automaticamente com o banco, já que os dados foram inseridos manualmente. Caso o modelo de previsão ou o cálculo de similaridade seja re-executado com novos dados, essas duas tabelas precisam ser atualizadas manualmente no Power BI.