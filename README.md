# Nofis-Classifier

## Matriz de experimentos TF-IDF e K-Means

O [notebook 70](notebooks/70_matriz_tfidf_kmeans_e_validacao.ipynb) compara representações
TF-IDF, valores de `k` e sementes, gera rankings e prepara a revisão humana dos clusters.
Abra com o ambiente do projeto (`uv run jupyter lab`), ajuste a célula de parâmetros e
execute todas as células. O padrão usa toda a base disponível, reservando 300 descrições
para validação, e executa 144 ajustes.

Os resultados ficam em `reports/grid_tfidf_kmeans/` e os modelos em
`models/grid_tfidf_kmeans/`, separados por período e execução. Para retomar, preencha
`RUN_ID` com o identificador exibido, mantendo os mesmos dados e parâmetros.
Depois revise os CSVs `cluster_review.csv`, escolha o experimento no notebook e
preencha `validation_labels.csv` para avaliar a categorização. A revisão humana não
é sobrescrita ao reexecutar as células.
