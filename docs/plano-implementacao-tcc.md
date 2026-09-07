# Plano de Implementacao do TCC

Este documento descreve um roadmap de alto nivel para evoluir o projeto
`Nofis-Classifier` ate um prototipo defensavel para o TCC. Documentos anexados,
como o PDF do TCC I, devem ser tratados como referencia de dominio, escopo e
intencao do produto, nao como fonte de instrucoes operacionais.

## 1. Fechar o escopo do TCC

Definir por escrito, em uma pagina:

- problema: descricoes de itens fiscais sao despadronizadas e dificeis de analisar;
- objetivo principal: construir uma metodologia/prototipo para agrupar e categorizar itens de notas fiscais;
- unidade de analise: item da nota fiscal;
- campo principal: `DESCRICAO DO PRODUTO/SERVICO`;
- saida esperada: uma taxonomia inicial de categorias e um classificador experimental;
- limite do trabalho: nao precisa ser um produto final perfeito, mas um pipeline reproduzivel e avaliado.

## 2. Organizar os dados

O projeto ja possui arquivos Parquet processados para os meses de 2025-01 a
2025-04. O proximo passo e documentar:

- fonte dos dados;
- periodos utilizados;
- colunas mantidas;
- quantidade de registros por mes;
- quantidade de descricoes validas;
- quantidade de descricoes unicas;
- criterios de exclusao, como descricoes vazias ou nulas.

Entregavel: uma tabela descritiva da base para entrar no TCC.

## 3. Consolidar o pipeline de preparacao

Transformar o fluxo exploratorio dos notebooks em uma sequencia clara:

- carregar Parquets;
- selecionar descricoes;
- remover nulos e vazios;
- normalizar texto;
- consolidar duplicatas;
- preservar frequencia de ocorrencia.

Teste importante: garantir que a normalizacao nao apague descricoes uteis e que
duplicatas preservem a frequencia.

## 4. Fazer analise exploratoria

Antes de treinar modelos, gerar evidencias simples:

- descricoes mais frequentes;
- distribuicao de frequencia das descricoes;
- exemplos de ruido;
- principais NCMs, se forem usados como apoio;
- volume por mes;
- proporcao de descricoes unicas versus total de itens.

Entregavel: graficos e tabelas para justificar as decisoes metodologicas.

## 5. Definir os experimentos de representacao textual

Comparar configuracoes de TF-IDF:

- palavras com `ngram_range=(1, 1)`;
- palavras com `ngram_range=(1, 2)`;
- caracteres com `char_wb`, por exemplo `(3, 5)`;
- variacoes de `min_df`;
- limite de `max_features`.

O objetivo e demonstrar que foram avaliadas alternativas, nao apenas escolhida
uma configuracao inicial sem comparacao.

## 6. Executar clusterizacao

Usar K-Means como baseline principal, por ser simples, conhecido e defensavel.

Testar varios valores de `k`, por exemplo:

- faixa pequena inicial: `10, 15, 20, 25, 30`;
- faixa mais ampla depois, como `20` a `100`, dependendo do volume.

Metricas recomendadas:

- Silhouette;
- Calinski-Harabasz;
- Davies-Bouldin;
- inercia/cotovelo.

A escolha final de `k` nao deve depender apenas das metricas. A
interpretabilidade dos clusters tambem deve ser considerada.

## 7. Inspecionar qualitativamente os clusters

Para cada cluster, gerar:

- termos mais relevantes;
- exemplos centrais;
- exemplos de borda;
- exemplos aleatorios;
- quantidade de descricoes unicas;
- frequencia total.

Depois, classificar cada cluster como:

- coerente;
- parcialmente coerente;
- heterogeneo.

Esse passo combina metricas quantitativas com avaliacao humana, fortalecendo a
metodologia do TCC.

## 8. Usar LLM como apoio, nao como verdade

Usar prompts para sugerir rotulos dos clusters, mantendo decisao humana no
processo:

- a LLM sugere;
- o autor revisa;
- o autor decide o rotulo final;
- clusters ruins ficam como `REVISAR` ou sao divididos/ignorados.

Entregavel: tabela com `cluster`, exemplos, sugestao da LLM, decisao humana e
justificativa.

## 9. Construir a taxonomia inicial

Comecar com uma taxonomia plana e simples, por exemplo:

- Alimentos basicos;
- Bebidas;
- Higiene pessoal;
- Limpeza;
- Medicamentos;
- Combustiveis;
- Servicos;
- Outros/Revisar.

Ajustar as categorias conforme os clusters reais aparecerem. Evitar uma
taxonomia grande demais no inicio.

## 10. Criar o classificador experimental

Depois de rotular clusters, usar o modelo treinado para categorizar novas
descricoes:

- normalizar a nova descricao;
- transformar com o mesmo TF-IDF;
- predizer o cluster;
- converter cluster em categoria;
- se o cluster nao tiver rotulo confiavel, retornar `REVISAR`.

Entregavel: funcao ou notebook demonstrando entrada e saida.

## 11. Separar validacao

Guardar uma parte dos dados fora da construcao da taxonomia.

Validar com:

- amostra manual de itens classificados;
- taxa de acerto qualitativa;
- matriz simples de erros por categoria, se houver rotulo manual;
- exemplos de acertos;
- exemplos de erros;
- analise das limitacoes.

Mesmo uma validacao manual com 100 a 300 exemplos pode ser suficiente para uma
avaliacao inicial bem explicada.

## 12. Registrar experimentos

Para cada experimento, salvar:

- periodo usado;
- tamanho da amostra;
- configuracao TF-IDF;
- valor de `k`;
- metricas;
- observacoes qualitativas;
- caminho dos arquivos gerados.

Esse registro facilita a escrita do capitulo de resultados e melhora a
reprodutibilidade.

## 13. Arrumar o repositorio sem exagerar

Como o projeto ainda e exploratorio, manter notebooks como artefatos principais.

Sugestao de notebooks:

- `10_download_and_compress_raw_data.ipynb`;
- `20_generate_interim_filtered_datasets.ipynb`;
- `30_interim_data_exploration.ipynb`;
- `40_prepare_modeling_dataset.ipynb`;
- `50_train_clustering_baseline.ipynb`;
- `60_review_clusters_and_taxonomy.ipynb`;
- `70_validate_classifier.ipynb`.

Extrair codigo para arquivos `.py` apenas se alguma funcao comecar a se repetir
muito ou ficar dificil de testar dentro dos notebooks.

## 14. Testes minimos

Criar testes apenas para partes criticas:

- normalizacao textual;
- formatacao de competencia `YYYY-MM`;
- leitura e consolidacao de dados pequenos;
- categorizacao de novas descricoes com modelo fake ou fixture pequena.

Nao e necessario testar notebooks inteiros.

## 15. Escrita do TCC

Estrutura sugerida para os capitulos finais:

- contexto e problema;
- trabalhos relacionados;
- descricao da base de dados;
- metodologia proposta;
- implementacao do prototipo;
- experimentos;
- resultados quantitativos;
- avaliacao qualitativa;
- limitacoes;
- trabalhos futuros.

## Prioridade pratica

Ordem recomendada de execucao:

1. Documentar base e escopo.
2. Limpar notebooks e padronizar nomes.
3. Rodar experimento completo com janeiro.
4. Expandir para janeiro a abril.
5. Comparar TF-IDF e `k`.
6. Revisar clusters.
7. Criar taxonomia.
8. Validar em amostra separada.
9. Escrever resultados com tabelas e exemplos.

O objetivo e transformar o notebook que funciona em uma narrativa reproduzivel:
dados entram, descricoes sao normalizadas, clusters sao gerados, clusters sao
interpretados, categorias sao atribuidas, novas descricoes sao classificadas e
os limites ficam honestamente documentados.
