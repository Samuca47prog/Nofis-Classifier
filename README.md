# Nofis-Classifier

Agrupamento não supervisionado de descrições de itens de notas fiscais brasileiras em categorias de produto.

Descrições fiscais são textos curtos, abreviados e ruidosos (`biscoito salgado tipo salt plus c 360g`, `luva latex c po 100 un pp`). O projeto compara representações de texto (TF-IDF, embeddings MPNet e uma combinação dos dois) e algoritmos de clusterização (K-Means, DBSCAN, HDBSCAN) para descobrir grupos de produtos sem rótulos, e avalia os grupos com o código NCM como referência externa e com revisão manual.

É a implementação prática de um Trabalho de Conclusão de Curso (Unisinos).

## Dados

- **Origem:** [Portal da Transparência — notas fiscais](https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais), base pública de NF-e que têm órgãos do governo federal como destinatários. Período: jan–dez/2025.
- **Recorte:** itens cujo NCM está entre os códigos mais frequentes em supermercados e redes varejistas (notebooks 13 e 21).
- **Unidade de análise:** descrição normalizada única. Descrições repetidas são consolidadas e a coluna `frequencia` guarda quantos itens cada uma representa.

O repositório inclui apenas a base final usada nos experimentos:

```text
data/processed/2025_NCMs_filtrados_semstopwords/2025_NCMs_filtrados_semstopwords-202501-202512.parquet
```

| | |
|---|---|
| Descrições únicas | 146.999 |
| Itens representados (`frequencia`) | 868.287 |
| Colunas principais | `descricao_normalizada`, `frequencia`, `descricao_original_exemplo`, `codigo_ncm_mais_frequente`, `ncm_tipo_mais_frequente` |

As bases intermediárias (`data/raw/`, `data/interim/`), os relatórios (`reports/`) e os modelos treinados (`models/`) não são versionados. Para reconstruí-los, execute os notebooks a partir do 10.

## Estrutura

```text
data/processed/        base final em Parquet
notebooks/             análises e experimentos, numerados pela etapa do fluxo
src/nofis_classifier/  código compartilhado entre notebooks (normalização, esquema, TF-IDF, grade K-Means)
tests/                 testes pytest do pacote
```

Cada notebook segue o mesmo formato: objetivo no topo, configurações e funções da análise nas primeiras células, execução nas células finais. Os caminhos são relativos à raiz do repositório e as células que gravam arquivos estão identificadas. As convenções completas estão em [AGENTS.md](AGENTS.md).

## Fluxo dos notebooks

```text
10 download ──► 11, 12, 30 exploração da base bruta
     │
     └──► 13 NCMs de supermercados ──► 21 filtro por NCM ──► 41 preparação ──► data/processed/
                                                                                  │
                         42 análise das descrições ◄──────────────────────────────┤
                                                                                  ▼
                                          70–76 grade de experimentos (representação × algoritmo)
                                                                                  │
                                    80–82 visualização · 83–85 avaliação · 90 predição
```

| Etapa | Notebooks | O que faz |
|---|---|---|
| Coleta | `10` | Baixa os ZIPs mensais do Portal da Transparência e converte os CSVs para Parquet. |
| Exploração | `11`, `12`, `13`, `30` | Perfil da base bruta, concentração por emitente e município, NCMs mais comuns em supermercados. |
| Recorte e preparação | `21`, `41`, `42` | Filtra pelos NCMs de supermercado, normaliza o texto, remove stop words, consolida duplicatas e analisa o resultado. |
| Primeiros testes | `50`, `51`, `52`, `60` | Comparação inicial de configurações TF-IDF, t-SNE, representação híbrida e K-Means. Usam bases anteriores, não incluídas. |
| Experimentos | `70`–`76` | Grade com amostra e avaliação comuns: TF-IDF e MPNet com K-Means, DBSCAN e HDBSCAN, e o híbrido TF-IDF + MPNet com HDBSCAN. |
| Visualização | `80`–`82` | Projeções e perfis lexicais dos clusters de execuções salvas. |
| Avaliação | `83`–`85` | Reúne as nove configurações selecionadas, calcula pureza, AMI e ARI contra o NCM e consolida a revisão manual. |
| Uso | `90` | Atribui uma nova descrição a um cluster de um modelo TF-IDF + HDBSCAN exportado. |
| Figura | `86` | Figura ilustrativa de t-SNE com o conjunto `digits` do scikit-learn. |

Os notebooks `70`–`76` dependem apenas da base incluída. Os notebooks `80`–`90` leem relatórios e modelos gerados pelos experimentos. Para executá-los, rode antes os experimentos correspondentes.

## Resultados

Nove configurações foram selecionadas a partir dos rankings dos notebooks `70`–`76`. Todas usam a mesma amostra de 20.000 descrições. A cobertura é a parcela das descrições que recebeu cluster (DBSCAN e HDBSCAN marcam o restante como ruído). A coluna "Coerentes" é a parcela dos clusters sorteados que a revisão manual considerou coerentes.

| Configuração | Clusters | Silhueta | Cobertura | Pureza NCM | Coerentes |
|---|---:|---:|---:|---:|---:|
| TF-IDF + K-Means | 200 | 0,21 | 100,0% | 0,26 | 81,0% |
| MPNet + K-Means | 200 | 0,12 | 100,0% | 0,37 | 28,6% |
| TF-IDF + DBSCAN | 734 | 1,00 | 36,1% | 0,74 | 100,0% |
| MPNet + DBSCAN | 11 | 0,98 | 0,7% | 1,00 | 100,0% |
| TF-IDF + HDBSCAN (1º do ranking) | 736 | 0,52 | 50,9% | 0,69 | 95,2% |
| TF-IDF + HDBSCAN (candidata A) | 101 | 0,71 | 20,0% | 0,67 | 81,0% |
| TF-IDF + HDBSCAN (candidata B) | 381 | 0,57 | 39,7% | 0,69 | 90,5% |
| MPNet + HDBSCAN | 123 | 0,47 | 16,9% | 0,68 | 85,7% |
| TF-IDF + MPNet (α = 0,2) + HDBSCAN | 982 | 0,35 | 48,4% | 0,75 | 85,7% |

- Os métodos por densidade formam clusters mais coerentes que o K-Means, mas deixam parte das descrições como ruído. Coerência e cobertura precisam ser lidas juntas.
- Com o mesmo algoritmo, TF-IDF teve cobertura ou coerência maior que MPNet em todas as comparações.
- A revisão manual cobriu 179 clusters, sorteados por tercil de tamanho em cada configuração e avaliados às cegas: 29 pelo autor e 150 com assistência de LLM. As taxas de coerência dos dois grupos ficaram próximas (82,8% e 82,0%).

Detalhes, métricas por estrato e a comparação com a pureza NCM estão nos notebooks [84](notebooks/84_avaliacao_ncm_e_revisao_manual.ipynb) e [85](notebooks/85_resultado_revisao_manual.ipynb).

## Como executar

Requisitos: Python 3.12 e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

```bash
uv run jupyter lab
```

Abra um notebook, revise a célula de configurações e execute de cima para baixo em uma sessão limpa. Os notebooks com MPNet baixam o modelo `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` do Hugging Face na primeira execução.

Os experimentos gravam relatórios em `reports/<experimento>/` e modelos em `models/<experimento>/`, em uma pasta nova por execução. Resultados anteriores não são sobrescritos.

## Testes

```bash
uv run pytest
```

Os testes cobrem o pacote `src/nofis_classifier/`: normalização de texto, validação de esquema, preparação da base, configurações TF-IDF, registro de experimentos e a grade K-Means com retomada.
