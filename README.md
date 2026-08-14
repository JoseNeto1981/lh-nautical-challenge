# LH Nautical — Desafio Técnico

Resolução completa do case técnico da LH Nautical: um pipeline de dados de ponta a ponta, da ingestão bruta de 24 arquivos CSV até insights preditivos e um sistema de recomendação, entregue para dar suporte a decisões reais de negócio.

**[Relatório final consolidado →](relatorio_final/relatorio_final_completo.pdf)**

## Sobre o desafio

A LH Nautical é uma empresa fictícia de varejo náutico cujos dados operacionais (2020–2026) estavam disponíveis apenas como CSVs brutos, sem banco de dados estruturado. A missão: modelar um schema, carregar os dados em um banco relacional real e responder perguntas de negócio que a diretoria precisava para tomar decisões — de estoque, de operação de loja, de retenção de clientes.

## Principais achados

| # | Insights | Impacto |
|---|---|---|
| 1 | A base de dados brutos tem boa integridade (sem nulos, sem negativos), mas contém uma data futura suspeita e ao menos um caso de produto duplicado no cadastro. | Confiabilidade dos dados |
| 2 | Entre os 10 clientes mais fiéis (maior ticket médio, compram em 14+ categorias), **Hélices** é a categoria mais vendida. | Estratégia comercial |
| 3 | Corrigido o erro do estagiário: **Quinta-feira** é o pior dia de vendas, não Domingo — que fica em segundo pior lugar, não em primeiro melhor. | Decisão operacional |
| 4 | O baseline de previsão (média móvel) **subestimou sistematicamente** as vendas do 1º trimestre de 2026 (149 previstas vs. 207 reais). | Risco de ruptura de estoque |
| 5 | A recomendação por similaridade aponta outro motor de popa — não uma defensa — como produto mais associado ao Motor de Popa 1949. | Estratégia de cross-sell |

Detalhamento completo de cada achado no [relatório final](relatorio_final/relatorio_final_completo.pdf).

## Pipeline e stack técnica

```
24 CSVs brutos → EDA (DuckDB) → Schema (Python) → PostgreSQL (Docker) → Carga (psycopg2) → Análises (SQL + Python)
```

- **Banco de dados:** PostgreSQL 16, rodando em container Docker
- **Engenharia de dados:** Python (stdlib para geração de schema; psycopg2 + COPY para carga)
- **Análises:** SQL analítico (CTEs, window functions, generate_series) e Python (pandas, scikit-learn)
- **Relatório final:** gerado programaticamente (docx-js) com gráficos em matplotlib

## Estrutura do repositório

```
├── data/raw/                          CSVs originais, sem tratamento
├── docs/                              Decisões técnicas e dicionário de dados
├── questoes/                          Uma pasta por questão do desafio
│   ├── questao_01_eda/                Análise exploratória de dados
│   ├── questao_02_schema/             Geração do schema PostgreSQL
│   ├── questao_03_carregamento/       Carga dos dados no banco
│   ├── questao_04_analise_clientes/   Clientes fiéis e categoria mais vendida
│   ├── questao_05_dimensão_de_calendario/  Vendas por dia da semana
│   ├── questao_06_previsao_demanda/   Modelo preditivo de demanda
│   └── questao_07_recomendacao/       Sistema de recomendação
└── relatorio_final/                   Relatório consolidado + gráficos de apoio
```

## Cada frente do desafio

| Frente | O que foi feito | Pasta |
|---|---|---|
| EDA | Diagnóstico de qualidade e confiabilidade dos dados brutos | [`questao_01_eda/`](questoes/questao_01_eda/) |
| Tratamento de Dados — Schema | Script Python (stdlib) que infere tipos e gera `schema.sql` a partir dos CSVs | [`questao_02_schema/`](questoes/questao_02_schema/) |
| Tratamento de Dados — Carregamento | Carga dos 24 CSVs no PostgreSQL via `COPY`, sem transformação | [`questao_03_carregamento/`](questoes/questao_03_carregamento/) |
| Análise de Clientes | Identificação dos clientes fiéis (ticket médio + diversidade de categorias) | [`questao_04_analise_clientes/`](questoes/questao_04_analise_clientes/) |
| Análise de Vendas | Dimensão de calendário para corrigir viés de dias sem venda | [`questao_05_dimensão_de_calendario/`](questoes/questao_05_dimensão_de_calendario/) |
| Previsão de Demanda | Baseline de média móvel, sem data leakage, com métrica MAE | [`questao_06_previsao_demanda/`](questoes/questao_06_previsao_demanda/) |
| Sistemas de Recomendação | Similaridade de cosseno sobre matriz usuário-produto | [`questao_07_recomendacao/`](questoes/questao_07_recomendacao/) |

## Como rodar

Cada pasta em `questoes/` contém um `.md` com o passo a passo específico (setup do banco, dependências, comandos). Visão geral:

```bash
# 1. Subir o banco
docker run --name lh-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=lh_nautical -p 5432:5432 -d postgres:16

# 2. Instalar dependências Python
pip install -r requirements.txt

# 3. Gerar e aplicar o schema
python questoes/questao_02_schema/gerar_schema.py
docker exec -i lh-postgres psql -U postgres -d lh_nautical < sql/schema.sql

# 4. Carregar os dados
python questoes/questao_03_carregamento/carregar_dados.py
```

A partir daí, as queries SQL de cada questão podem ser rodadas contra o banco (ex: via extensão SQLTools do VS Code), e os scripts Python de cada frente rodam de forma independente.
