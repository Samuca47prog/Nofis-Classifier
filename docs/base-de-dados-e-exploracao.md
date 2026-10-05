# Base de dados e exploração inicial


---
Minhas notas:
- 
---




## Objetivo desta etapa

Esta etapa caracteriza os dados disponíveis e investiga se as descrições de itens fiscais oferecem informação suficiente para agrupamento e categorização. A unidade de análise adotada no fluxo de modelagem é o item da nota fiscal; o campo textual principal é `DESCRIÇÃO DO PRODUTO/SERVIÇO`. Os notebooks de exploração também examinam NCM e campos de contexto fiscal para compreender a heterogeneidade dos registros.

## Fonte e período

O notebook [`10_download_and_compress_raw_data.ipynb`](../notebooks/10_download_and_compress_raw_data.ipynb) registra como fonte os dados abertos de notas fiscais disponibilizados pelo Portal da Transparência. Foram baixados arquivos mensais de janeiro a abril de 2025. Os arquivos compactados originais foram mantidos em `data/raw/items-notas-fiscais/`; o fluxo lê os CSVs separados por ponto e vírgula, usando codificação Latin-1, concatena os arquivos do mês e grava uma versão intermediária em Parquet.

O pipeline importa tanto registros de notas quanto de itens. Por isso, o total de linhas do Parquet bruto mensal não deve ser interpretado diretamente como quantidade de itens: os registros de item são identificados pela presença da descrição do produto ou serviço. Na base original, o fluxo localizou os seguintes volumes de linhas com descrição:

| Competência | Linhas com descrição de item |
| --- | ---: |
| 2025-01 | 369.683 |
| 2025-02 | 490.657 |
| 2025-03 | 434.549 |
| 2025-04 | 470.126 |
| **Total** | **1.765.015** |

Essas contagens descrevem as linhas com descrição nos arquivos intermediários. A preparação posterior remove valores nulos ou vazios e pode consolidar várias ocorrências em uma descrição normalizada.

## Recorte temático da base

O notebook [`20_generate_interim_filtered_datasets.ipynb`](../notebooks/20_generate_interim_filtered_datasets.ipynb) permite gerar recortes por prefixos do código NCM, emitente, condição de consumidor final e presença do comprador. A configuração atualmente registrada para a base de filtros combinados usa:

- prefixos NCM associados principalmente a alimentos e produtos de mercado, além de itens selecionados de higiene, limpeza e uso doméstico;
- `CONSUMIDOR FINAL = "1 - CONSUMIDOR FINAL"`;
- `PRESENÇA DO COMPRADOR = "1 - OPERAÇÃO PRESENCIAL"`;
- sem lista de emitentes configurada.

Os filtros preenchidos são aplicados em conjunto. O recorte, portanto, significa itens cujo NCM começa por um dos prefixos selecionados **e** que estão marcados como venda a consumidor final **e** operação presencial. Essa seleção é uma aproximação operacional do escopo de compras de mercado; não equivale a uma identificação perfeita do tipo de estabelecimento ou da finalidade de cada compra.

As contagens conferidas nos Parquets intermediários filtrados foram:

| Competência | Itens no recorte combinado |
| --- | ---: |
| 2025-01 | 25.790 |
| 2025-02 | 29.289 |
| 2025-03 | 37.932 |
| 2025-04 | 41.614 |
| **Total** | **134.625** |

## Preparação e consolidação das descrições

No notebook [`40_prepare_modeling_dataset.ipynb`](../notebooks/40_prepare_modeling_dataset.ipynb), as competências filtradas são concatenadas. O fluxo seleciona a descrição, descarta nulos e textos vazios e normaliza o texto com as seguintes operações: remoção de espaços externos, conversão para minúsculas, remoção de diacríticos, substituição de sequências que não sejam letras ASCII ou números por espaço e redução de espaços repetidos.

As linhas que resultam na mesma descrição normalizada são agrupadas. A base processada guarda a frequência de ocorrência, um exemplo original, a quantidade de descrições originais distintas, primeiro e último mês de ocorrência, quantidade de meses presentes e, quando disponíveis, os NCMs e tipos de NCM mais frequentes. A soma das frequências preserva o número de descrições válidas antes da consolidação.

No Parquet processado atual, `items-notas-fiscais-filtros-combinados-202501-202504.parquet`, há **27.800 descrições normalizadas únicas**, que representam **134.624 ocorrências válidas**. A diferença de uma ocorrência em relação à contagem bruta do recorte corresponde a uma linha cuja descrição foi removida na validação de nulos/vazios. A frequência por descrição tem mediana 1, terceiro quartil 3 e máximo 1.533 ocorrências. Portanto, muitas descrições aparecem poucas vezes, enquanto uma pequena parte concentra recorrências elevadas.

## Explorações realizadas

### Qualidade e perfil textual

Os notebooks [`30_interim_data_exploration.ipynb`](../notebooks/30_interim_data_exploration.ipynb) e [`11_exploratory_analysis.ipynb`](../notebooks/11_exploratory_analysis.ipynb) caracterizam as descrições antes e depois da preparação. São examinados valores ausentes, duplicatas, frequências, tamanho em caracteres e palavras, presença de números e sinais de pontuação, além de exemplos curtos, longos e potencialmente ruidosos.

As heurísticas de ruído são exploratórias: descrições curtas, numéricas, com muitos dígitos, caracteres incomuns ou sinais de truncamento/codificação são sinalizadas para inspeção, mas não são automaticamente consideradas inválidas. Essa distinção evita descartar, sem análise, descrições fiscais legítimas que contenham medidas, códigos ou abreviações.

### Frequência e cobertura temporal

O notebook 11 ordena as descrições mais frequentes, resume a distribuição de ocorrências por descrição e calcula o volume mensal de itens e a proporção entre ocorrências e descrições únicas. A distribuição ajuda a identificar a cauda longa e a avaliar como descrições recorrentes podem influenciar a modelagem. Também são listadas descrições únicas para inspeção posterior.

### NCM e relação com as descrições

O código NCM e o tipo de produto associado são explorados como variáveis de apoio. As análises levantam os códigos mais frequentes e o número de descrições distintas associado a cada código. Uma amostra fixa de até 75 mil itens é usada para inspecionar a relação descrição–NCM, incluindo descrições associadas a mais de um código e códigos associados a descrições diversas.

Essas verificações servem para entender a estrutura e possíveis ambiguidades do dado. O NCM não é tratado automaticamente como rótulo final da categoria textual: códigos fiscais e descrições comerciais cumprem papéis diferentes, e a associação observada pode não ser unívoca.

### Campos fiscais, emitentes e localidade

Também são examinados série, natureza da operação, razão social do emitente, condição de consumidor final e presença do comprador. Uma análise adicional no notebook [`12_sao_leopoldo_volume_notas.ipynb`](../notebooks/12_sao_leopoldo_volume_notas.ipynb) investiga por que São Leopoldo aparece com volume elevado nos dados. O próprio notebook delimita a interpretação: município e UF são do **emitente**, não necessariamente do local de consumo; portanto, esse recorte não permite inferir consumo municipal nem representatividade populacional. As hipóteses de concentração em fornecedores, notas com muitos itens e concentração temporal são questões investigadas, não conclusões assumidas.

## Síntese metodológica

A exploração orientou a montagem de um conjunto temático menor e revelou características relevantes para as etapas seguintes: descrições curtas e heterogêneas, forte desigualdade de frequência, códigos fiscais úteis como contexto e relações descrição–NCM que merecem cautela. Após o recorte combinado e a normalização, a base atual reúne 27.800 descrições distintas e 134.624 ocorrências válidas no período de janeiro a abril de 2025.

Os resultados numéricos aqui registrados são contagens dos artefatos atualmente presentes no repositório. As análises dos notebooks são reexecutáveis e podem variar caso os dados de origem, filtros ou versões dos arquivos mudem. Para uma versão final do TCC, convém preservar junto aos resultados a data de execução e os parâmetros usados.

## Artefatos relacionados

- Download e conversão: [`10_download_and_compress_raw_data.ipynb`](../notebooks/10_download_and_compress_raw_data.ipynb)
- Exploração da base bruta: [`11_exploratory_analysis.ipynb`](../notebooks/11_exploratory_analysis.ipynb)
- Investigação do volume por município do emitente: [`12_sao_leopoldo_volume_notas.ipynb`](../notebooks/12_sao_leopoldo_volume_notas.ipynb)
- Geração de recortes: [`20_generate_interim_filtered_datasets.ipynb`](../notebooks/20_generate_interim_filtered_datasets.ipynb)
- Exploração dos dados intermediários: [`30_interim_data_exploration.ipynb`](../notebooks/30_interim_data_exploration.ipynb)
- Preparação da base de modelagem: [`40_prepare_modeling_dataset.ipynb`](../notebooks/40_prepare_modeling_dataset.ipynb)
- Dados processados: `data/processed/items-notas-fiscais-filtros-combinados/`


# Pré-processamento textual

# Representação textual

# Clusterização

# Seleção de exemplos representativos dos clusters

#  Nomenclatura de clusters com apoio de LLM

# Construção e refinamento da taxonomia

# Avaliação dos resultados
