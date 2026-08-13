# Relatório Final — Documentação de Geração

## Objetivo

Consolidar as frentes de trabalho do desafio (EDA, Tratamento de Dados, Análise de Clientes, Análise de Vendas, Previsão de Demanda e Sistemas de Recomendação) em um relatório único, no formato exigido pela entrega (material complementar com visualizações — item 20 do desafio), pronto para leitura pela diretoria da LH Nautical.

## Componentes desta pasta

| Arquivo | O que é |
|---|---|
| `relatorio_final_completo.docx` | O relatório final, pronto para leitura/entrega |
| `gerar_relatorio.js` | Script que monta o `.docx` (capa, sumário, texto, tabelas e imagens) |
| `gerar_graficos.py` | Script que gera os 4 gráficos de apoio às análises de negócio |
| `logo_indicium.png` | Logo usado no cabeçalho de todas as páginas do relatório |
| `fluxo_geral.png` | Fluxograma macro do pipeline de dados (CSV → banco → análises) |
| `fluxo_engenharia.png` | Detalhamento técnico da frente de Tratamento de Dados |
| `fluxo_analises.png` | Detalhamento técnico das frentes de análise de negócio |
| `grafico_q4.png` | Ticket médio dos 10 clientes fiéis (Figura 4 do relatório) |
| `grafico_q5.png` | Vendas médias por dia da semana (Figura 5) |
| `grafico_q6.png` | Previsto vs. realizado — previsão de demanda (Figura 6) |
| `grafico_q7.png` | Ranking de similaridade de produtos (Figura 7) |

## Metodologia

### 1. Por que gerar o `.docx` via script, em vez de editar manualmente no Word

A primeira tentativa de montar o relatório foi em Markdown, para depois colar no Word. Isso gerou um problema real: tabelas em Markdown (sintaxe `| coluna | coluna |`) não são reconhecidas pelo Word como tabelas de verdade — ao colar, os caracteres `|` e `-` aparecem literalmente na página, sem nenhuma formatação de grade.

A solução foi gerar o `.docx` **nativamente**, usando a biblioteca `docx` (Node.js). Isso garante que tabelas, títulos, cores e imagens sejam objetos reais do formato Word desde a origem — sem depender de conversão manual de colar-e-formatar.

### 2. Fluxogramas do pipeline

Os três fluxogramas (visão geral + dois de detalhe técnico) foram desenhados como SVG e exportados para PNG (via `cairosvg`), para poderem ser embutidos como imagem no `.docx` — o formato Word não interpreta SVG nativamente. Eles ilustram, respectivamente: o pipeline de ponta a ponta (CSVs → EDA → Schema → Docker/PostgreSQL → Carga → Análises), o detalhamento técnico da engenharia de dados, e o detalhamento técnico das análises de negócio.

### 3. Gráficos de apoio às análises de negócio

Os quatro gráficos (`gerar_graficos.py`) foram gerados com `matplotlib`, a partir dos resultados já obtidos e documentados em cada frente do desafio. Cada gráfico usa destaque de cor (vermelho) no ponto de maior relevância para a conclusão de negócio:

- **Figura 4**: barras do ticket médio dos 10 clientes fiéis, evidenciando a proximidade entre eles.
- **Figura 5**: barras da média de vendas por dia da semana, com Quinta-feira destacada como o pior dia — o principal achado da correção do erro do estagiário.
- **Figura 6**: linha comparando previsão (média móvel) e vendas reais no 1º trimestre de 2026, evidenciando a subestimação sistemática do modelo baseline.
- **Figura 7**: barras horizontais do ranking de similaridade de cosseno, com o produto de maior similaridade destacado.

## Como reproduzir

Pré-requisitos:
```bash
pip install matplotlib cairosvg --break-system-packages
```
*(o `cairosvg` só é necessário se for regenerar os fluxogramas a partir de um SVG — os PNGs já estão prontos nesta pasta)*

Gerar os gráficos de apoio:
```bash
python gerar_graficos.py
```

Gerar o relatório final (requer Node.js e a biblioteca `docx`):
```bash
node gerar_relatorio.js
```

O script `gerar_relatorio.js` espera que todos os arquivos `.png` desta pasta (fluxogramas, gráficos e logo) estejam no mesmo diretório do script — os caminhos são resolvidos via `__dirname`.