# Melhorias de codigo e uso

Este documento resume os cinco planos aceitos para melhorar a base de codigo do
`Nofis-Classifier`, as modificacoes implementadas e como usar os novos modulos.

## Planos implementados

### 1. Aprofundar o pipeline de preparacao

Plano: retirar regras estaveis dos notebooks e concentrar o comportamento
reutilizavel em modulos Python pequenos. Os notebooks continuam sendo a narrativa
da pesquisa, mas deixam de ser o unico lugar onde a regra vive.

Implementado:

- `src/nofis_classifier/text.py` para normalizacao textual.
- `src/nofis_classifier/datasets.py` para caminhos de datasets, carga de
  Parquets processados e preparacao da base de modelagem.
- Testes focados em normalizacao, preparacao e preservacao de frequencia.

### 2. Nomear o schema da base

Plano: transformar nomes de colunas importantes em constantes e criar validacao
centralizada para detectar mudancas na estrutura dos dados.

Implementado:

- `src/nofis_classifier/schema.py` com nomes canonicos das colunas processadas.
- `find_column()` para localizar colunas originais por tokens normalizados.
- `validate_columns()` para falhas claras quando uma base nao contem o schema
  esperado.

### 3. Configurar o pacote `src`

Plano: declarar o layout do pacote no `pyproject.toml`, evitando que testes e
notebooks dependam de ajustes manuais em `sys.path`.

Implementado:

- `build-system` com `setuptools`.
- `[tool.setuptools.packages.find]` apontando para `src`.
- Remocao de `tests/conftest.py`, que antes inseria `src/` manualmente no path.

### 4. Adicionar `pytest` ao ambiente dev

Plano: tornar a verificacao por testes reproduzivel com `uv run pytest`.

Implementado:

- `pytest` foi adicionado em `[dependency-groups].dev`.
- A suite de testes cobre caminhos, texto, schema, datasets, TF-IDF e registro
  de experimentos.

### 5. Criar registro simples de experimentos

Plano: salvar metadados de experimentos em um CSV unico, para facilitar a
reprodutibilidade e a escrita dos resultados do TCC.

Implementado:

- `src/nofis_classifier/experiments.py` com `ExperimentRecord`,
  `create_experiment_record()` e `append_experiment_records()`.
- O fluxo de TF-IDF salva `reports/tfidf/experiment_registry.csv` junto dos
  relatorios de vocabulario e resumo. Cada execucao adiciona novos registros com
  timestamp no `experiment_id`.

## Como usar

### Rodar os testes

```bash
uv sync --dev
uv run pytest
```

### Carregar a base processada filtrada

```python
from nofis_classifier.datasets import load_processed_items, prepare_modeling_items, processed_dataset_path

path = processed_dataset_path()
raw_items = load_processed_items(path)
modeling_items = prepare_modeling_items(raw_items)
```

`modeling_items` tera uma linha por `descricao_normalizada`, um `descricao_id`
estavel e a coluna `frequencia` preservada.

### Normalizar texto

```python
from nofis_classifier.text import normalize_description

normalize_description("  Açúcar CRISTAL  1KG!!! ")
# "acucar cristal 1kg"
```

### Validar schema

```python
from nofis_classifier.schema import PROCESSED_MODELING_COLUMNS, validate_columns

validate_columns(raw_items, PROCESSED_MODELING_COLUMNS)
```

### Rodar a comparacao TF-IDF

```python
from pathlib import Path

from nofis_classifier.tfidf import run_default_tfidf_pipeline

summary, vocabulary_samples, registry = run_default_tfidf_pipeline(
    report_dir=Path("reports") / "tfidf"
)
```

Arquivos gerados:

- `reports/tfidf/tfidf_experiments_summary.csv`
- `reports/tfidf/tfidf_vocabulary_samples.csv`
- `reports/tfidf/experiment_registry.csv`

### Usar o notebook

Abra e execute:

```text
notebooks/50_train_clustering_baseline.ipynb
```

Ele carrega a base filtrada de `data/processed`, compara as configuracoes de
TF-IDF e salva os relatorios em `reports/tfidf/`.

## Observacoes

- Nenhuma dependencia de producao nova foi adicionada.
- Os dados em `data/processed/` nao foram alterados.
- A configuracao baseline de TF-IDF continua sendo `char_wb`, `ngram_range=(3, 5)`,
  `min_df=2`, `max_features=30000`.
