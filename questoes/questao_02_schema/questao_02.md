# Questão 2 - Schema

## Cenário

A empresa fornecedora do ERP não permite conexão direta com o banco de dados; a única forma de obter os dados é através dos CSVs já fornecidos. Para as próximas etapas do desafio, esses dados precisam estar carregados em um banco relacional (PostgreSQL) — e, para isso, é necessário definir o schema desse banco primeiro.

Esta questão implementa um script Python que lê os CSVs de origem, infere o tipo de dado mais adequado para cada coluna e gera um único arquivo `schema.sql` com os comandos `CREATE TABLE` correspondentes.

## Premissas obrigatórias

- Todos os CSVs foram considerados como arquivos de fonte
- Implementado em Python 3 puro
- Utilizadas apenas bibliotecas padrão: `csv`, `os`, `re`, `glob`, `datetime`
- Banco de destino: PostgreSQL

## Utilização do `schema.sql` gerado

O `schema.sql` é o elo entre os CSVs brutos e um banco de dados relacional funcional. Ele não contém dados — apenas a estrutura (tabelas, colunas, tipos e constraints). O fluxo de uso, após gerado, é:

1. **Criar a estrutura no banco**: rodar o arquivo contra uma instância PostgreSQL (`psql -f schema.sql`) para criar todas as tabelas vazias, já com tipos corretos e constraints (`NOT NULL`, `PRIMARY KEY`).
2. **Carregar os dados dos CSVs** (etapa seguinte do desafio), normalmente via `COPY` do Postgres ou scripts de carga.
3. **Habilitar análises relacionais**: com os dados no banco, é possível fazer `JOIN` entre tabelas (ex: `orders` com `customers`), garantir integridade referencial e ganhar performance de consultas — algo que não é viável trabalhando diretamente com CSVs soltos.

Ou seja, o `schema.sql` é o contrato estrutural que viabiliza as etapas seguintes do desafio (carga de dados e análises cruzadas entre as tabelas do ERP).

## Abordagem do script

O script (`generate_schema.py`) segue os seguintes passos para cada CSV encontrado no diretório de origem:

1. Lê o cabeçalho e todas as linhas do arquivo usando o módulo `csv` da biblioteca padrão.
2. Para cada coluna, analisa todos os valores presentes e aplica uma cadeia de verificações de tipo, do mais específico para o mais genérico:
   - **Identificador/documento** (pelo nome da coluna) → `VARCHAR(255)`
   - **Boolean** (`true`/`false`, `0`/`1`, `yes`/`no`, `t`/`f`) → `BOOLEAN`
   - **Inteiro** → `INTEGER` ou `BIGINT` (conforme o maior valor absoluto encontrado)
   - **Decimal** → `NUMERIC(18,4)`
   - **Data** (`YYYY-MM-DD` ou `DD/MM/YYYY`) → `DATE`
   - **Data e hora** → `TIMESTAMP`
   - **Fallback** → `VARCHAR(255)` ou `TEXT`, dependendo do tamanho máximo observado
3. Detecta se a coluna `id` é candidata a chave primária (valores únicos e sem nulos) e adiciona `PRIMARY KEY`.
4. Aplica `NOT NULL` em qualquer coluna sem valores vazios na amostra lida.
5. Gera o `CREATE TABLE` (precedido de `DROP TABLE IF EXISTS`, tornando o script idempotente) e escreve tudo em um único `schema.sql`.

## Decisões de modelagem e tratamento de casos especiais

A inferência de tipo não se baseia apenas no conteúdo dos valores — três decisões de design foram tomadas para que o schema gerado refletisse corretamente a semântica dos dados, e não apenas o formato bruto:

### 1. Identificadores e documentos são tratados como texto, não como número

Colunas como `cpf`, `phone`, `tax_id`, `barcode_ean` e `nfe_access_key` contêm apenas dígitos, mas **não são quantidades** — são identificadores. Tratá-las como tipo numérico traria dois riscos: perda de zeros à esquerda (comuns em CPF e CEP) e a falsa sugestão de que esses campos podem ser somados ou comparados matematicamente, o que nunca é o caso na prática.

Por isso, o script mantém uma lista de fragmentos de nome de coluna (`cpf`, `cnpj`, `tax_id`, `phone`, `barcode`, `zip`, `postal_code`, `document`, etc.) que, quando presentes no nome, **forçam o tipo `VARCHAR(255)`** independentemente do conteúdo parecer numérico. Essa checagem por nome acontece antes de qualquer checagem de conteúdo, garantindo que a semântica da coluna prevaleça sobre a aparência dos valores.

### 2. Boolean tem prioridade sobre inteiro na ordem de inferência

Colunas booleanas podem ser representadas de formas diferentes na origem: `true`/`false`, mas também `0`/`1`, `yes`/`no` ou `t`/`f`. Como `0` e `1` também são inteiros válidos, a ordem de verificação importa: **boolean é checado antes de inteiro** na cadeia de inferência, para que colunas binárias sejam identificadas como `BOOLEAN` independentemente de qual das representações a origem usar — em vez de caírem, por coincidência de formato, em `INTEGER`.

### 3. Chave primária e obrigatoriedade (NOT NULL) são inferidas automaticamente

Um schema relacional só é útil de fato quando expressa as regras de integridade dos dados, não apenas os tipos. Por isso, o script aplica duas heurísticas adicionais:
- A coluna `id` é marcada como `PRIMARY KEY` quando todos os seus valores são únicos e não nulos — condição necessária para funcionar como chave primária.
- Qualquer coluna sem nenhum valor vazio na amostra lida recebe `NOT NULL`, refletindo a obrigatoriedade observada nos dados reais.

## Validação da abordagem

As decisões acima foram testadas com CSVs de exemplo contendo colunas de CPF, telefone e uma coluna booleana com valores textuais (`true`/`false`). O resultado confirmou:

```sql
CREATE TABLE customers (
    id INTEGER NOT NULL,
    legal_name VARCHAR(255) NOT NULL,
    tax_id VARCHAR(255) NOT NULL,
    phone VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);
```

- `tax_id` e `phone` corretamente inferidos como `VARCHAR(255)` (não mais `BIGINT`).
- `is_active` corretamente inferido como `BOOLEAN`.
- `id` corretamente marcado como `PRIMARY KEY` com `NOT NULL`.
- Colunas com valores vazios na amostra (ex: `status` em um pedido incompleto) corretamente **não** receberam `NOT NULL`, preservando a nulabilidade real observada nos dados.

## Validação contra um PostgreSQL real

Além da geração do arquivo, o `schema.sql` foi testado executando-o de fato contra uma instância PostgreSQL, para confirmar que o SQL gerado é válido e não apenas teoricamente correto.

**Ambiente:** container Docker com PostgreSQL 16.

```bash
docker run --name lh-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=lh_nautical -p 5432:5432 -d postgres:16
```

**Execução do schema:**
```bash
docker exec -i lh-postgres psql -U postgres -d lh_nautical < schema.sql
```

O script rodou sem nenhum erro de sintaxe. As mensagens `NOTICE: table "X" does not exist, skipping` são esperadas — vêm do `DROP TABLE IF EXISTS` que precede cada `CREATE TABLE`, avisando que não havia tabela anterior para remover (primeira execução).

**Confirmação das tabelas criadas:**
```bash
docker exec -it lh-postgres psql -U postgres -d lh_nautical -c "\dt"
```

Resultado: **24 tabelas criadas**, uma para cada CSV de origem do desafio.

Essa validação confirma que o `schema.sql` gerado pelo script não é apenas um arquivo de texto com aparência de SQL — ele é executável e cria de fato a estrutura completa do banco de dados PostgreSQL, pronta para receber a carga de dados na etapa seguinte.

## Limitações conhecidas

- A inferência de tipo é feita com base em uma amostra (o CSV completo), não em uma regra de negócio validada externamente — colunas com poucos valores preenchidos podem gerar inferências menos confiáveis.
- A lista de fragmentos de nome para identificadores (`IDENTIFIER_NAME_HINTS`) é heurística e pode não cobrir 100% dos casos; nomes de coluna fora do padrão esperado podem não ser capturados.
- Não há detecção automática de chaves estrangeiras (`FOREIGN KEY`) — apenas a chave primária (`id`) é identificada. Relacionamentos entre tabelas (ex: `orders.customer_id` → `customers.id`) precisariam ser adicionados manualmente ou em uma etapa posterior.
- O script assume que o `id` é sempre a chave primária "natural"; tabelas de junção (ex: `product_suppliers`, `variant_attribute_values`, que não possuem coluna `id`) não recebem `PRIMARY KEY` automaticamente.

## Script utilizado

Ver arquivo `gerar_schema.py` nesta mesma pasta.

Uso:
```bash
python gerar_schema.py
```

O script lê os CSVs do diretório configurado em `INPUT_DIR` (`data/raw`) e escreve o resultado em `OUTPUT_FILE` (`sql/schema.sql`).