# Metodologia revisada

## 1. Objetivo e escopo

Este trabalho investiga um fluxo para organizar descrições de itens de notas fiscais brasileiras em categorias comerciais interpretáveis e recuperar descrições semelhantes para apoiar a classificação. O escopo implementado até o momento concentra-se na preparação de dados e na comparação exploratória de representações vetoriais e algoritmos de agrupamento. A atribuição validada de categorias comerciais e a avaliação da recuperação ainda estão pendentes.

O resultado atualmente demonstrável é um conjunto de experimentos não supervisionados e um protótipo de inferência. Os resultados de agrupamento não devem ser apresentados como desempenho de um classificador de categorias: não há, até o momento, um conjunto real de rótulos humanos, código de categorias acordado ou avaliação independente da qualidade semântica dos grupos.

## 2. Fonte e população dos dados

Os dados são obtidos do Portal da Transparência do Governo Federal, na seção de notas fiscais, por arquivos mensais baixados e convertidos em Parquet. O portal descreve esses registros como notas fiscais relacionadas a aquisições da Administração Pública Federal. Portanto, a população observada não é uma amostra representativa das compras de consumidores em supermercados. A aplicação de códigos NCM associados a supermercados não altera a natureza da população de origem. Essa limitação precisa ser refletida na pergunta de pesquisa, no título e nas conclusões.

Fontes oficiais:

- [Notas fiscais no Portal da Transparência](https://portaldatransparencia.gov.br/entenda-a-gestao-publica/notas-fiscais)
- [Download de dados de notas fiscais](https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais)

A análise ativa usa os doze arquivos mensais de 2025. O notebook 10 documenta o download e a conversão; o notebook 11 registra a exploração inicial. Os arquivos de entrada, parâmetros e artefatos citados abaixo devem ser mantidos juntos para que os números possam ser reproduzidos.

## 3. Seleção da base de itens

O notebook 13 identifica emissores por padrões textuais e seleciona dez emissores entre 397 candidatos para examinar suas ocorrências de NCM. Foram observados 453 códigos, considerando os códigos com pelo menos cinco ocorrências; a lista salva atualmente contém 241 códigos válidos. A seleção é exploratória e depende dos padrões empregados para reconhecer os emissores.

O notebook 21 normaliza os códigos para oito dígitos e aplica igualdade exata com a lista de 241 NCMs aos registros de todos os doze meses de 2025. O filtro é aplicado à base anual completa, e não somente às notas dos dez emissores usados para construir a lista. O resultado contém 868.292 linhas de itens antes da limpeza textual.

Esse desenho precisa ser descrito com precisão: os emissores ajudam a construir a lista de códigos, mas a base filtrada inclui itens de qualquer emissor que possua um desses códigos. O filtro não usa prefixos de NCM e não prova que cada item seja uma compra de supermercado. A justificativa de negócio e a adequação dessa seleção devem ser confirmadas pelo autor.

## 4. Limpeza, normalização e unidade de análise

O notebook 41 configura como entrada ativa a base 2025_NCMs_filtrados. A sequência observada é:

1. Remover descrições nulas ou vazias.
2. Remover sequências numéricas com seis ou mais dígitos da descrição.
3. Converter para minúsculas e remover acentos.
4. Manter letras e números ASCII, converter os demais caracteres em espaços e colapsar espaços consecutivos.
5. Descartar descrições que fiquem vazias após a normalização.
6. Agrupar por descrição normalizada e somar a frequência dos registros.

Na execução salva, 28.213 sequências longas de dígitos foram removidas do texto; isso é uma contagem de sequências, não de linhas. Quatro linhas foram excluídas por nulos ou vazios na validação. Restaram 868.288 ocorrências válidas, consolidadas em 149.149 descrições normalizadas distintas. A soma da coluna de frequência é 868.288; a mediana de frequência é 1 e o máximo é 7.814.

O notebook 30 registra 155.963 descrições distintas após trim e conversão para minúsculas. Esse número usa uma definição de normalização anterior, portanto não deve ser tratado como contraditório ao total de 149.149 após a limpeza mais completa do notebook 41.

Há uma variante histórica em data/processed/2025_NCMs-sem-duplicatas com 257.879 descrições e soma de frequência 1.238.688. Ela é diferente da base filtrada ativa e sua proveniência não está claramente ligada à configuração atual. Os resultados desse arquivo não devem ser combinados com os da base filtrada sem identificar a execução que o gerou. O valor de 158.293 descrições não foi confirmado nos artefatos examinados.

A representação de cada linha dos experimentos de agrupamento é uma descrição distinta, não uma ocorrência individual. Embora a frequência seja preservada, as execuções principais observadas não a usam como peso. Assim, itens frequentes não recebem maior influência no ajuste dos agrupamentos.

## 5. Representações textuais

O projeto usa TF-IDF e embeddings semânticos, além de uma combinação exploratória:

- TF-IDF representa palavras ou sequências de caracteres. As configurações variam entre notebooks; os experimentos incluem n-gramas de palavras e de caracteres, limites de frequência documental e de vocabulário distintos.
- MPNet usa sentence-transformers/paraphrase-multilingual-mpnet-base-v2 e produz vetores de 768 dimensões.
- No experimento híbrido do notebook 76, os dois espaços são normalizados, multiplicados pelas raízes dos pesos e concatenados. A execução local mais recente usa alpha=0,2; os artefatos salvos anteriormente incluem alpha=0,5. Essa diferença deve ser registrada por identificador de execução.

O notebook 41 também contém explorações de variantes que removem números e unidades. Essas variantes não participam do fluxo principal de comparação dos agrupamentos. t-SNE é usado para visualização, não para treinar os modelos.

## 6. Experimentos de agrupamento executados

Os experimentos são exploratórios e não formam uma comparação controlada única. Eles variam em período, base, amostra, representação, parâmetros e critério de seleção.

### 6.1 K-Means com TF-IDF

O notebook 60 e os relatórios associados analisam dados de janeiro a abril: 27.800 descrições distintas e frequência total 134.624, com redução simulada para 1.000 descrições. O baseline usa TF-IDF de palavras, unigramas, min_df=2 e até 5.000 características. Para k=25, o silhouette salvo é 0,075869 e os grupos variam de 6 a 417 itens. A execução serve à inspeção exploratória, não à classificação final.

Uma grade separada, em reports/grid_tfidf_kmeans/202501-202504_20260927T163113Z_3df937b0, usa 27.500 descrições para treino e 300 reservadas, seis configurações TF-IDF, k entre 10 e 80 e três sementes: 144 ajustes. A melhor mediana de silhouette relatada é 0,091191 para char_wb (3,5), min_df=5, vocabulário de até 30.000 e k=80. Os arquivos de revisão encontrados mantêm status REVISAR e não contêm rótulos humanos.

O notebook 70 usa a base anual filtrada e uma amostra de 5.000 descrições, com 4.700 para ajuste e 300 reservadas, semente 42. Com char_wb (3,5) e k=200, o silhouette salvo é 0,141113, com 191 grupos ocupados e maior grupo representando 15,43% da amostra. O valor chamado noise_fraction nessa saída representa a fração de vetores TF-IDF nulos; não representa ruído do K-Means. A seleção manual permanece vazia e não foi localizada validação rotulada.

### 6.2 K-Means com MPNet

O notebook 71 registra resultados para janeiro a abril. Com k=40, o silhouette mediano é 0,128974 e o desvio padrão entre sementes é 0,009335; para k=2.000 e k=3.000, as medianas são 0,057699 e 0,062694. A configuração ativa do notebook aponta atualmente para uma base anual distinta, enquanto as saídas salvas indicam janeiro a abril. Até reconciliar código, configuração e execução, esses números devem ser identificados como saídas históricas, sem comparação direta com os demais experimentos.

### 6.3 DBSCAN

No notebook 72, TF-IDF é aplicado a 5.000 descrições da base anual filtrada, com semente 42. A linha de melhor pontuação composta usa n-gramas de palavras (2,4), eps=0,035 e min_samples=2: 150 grupos, 75,48% de ruído e silhouette 0,999431 nos itens atribuídos. O silhouette é calculado sobre uma pequena fração coberta; não indica classificação de alta qualidade para a população completa.

No notebook 73, MPNet é aplicado à mesma amostra. Com eps=0,03 e min_samples=3, há 13 grupos e 99,02% de ruído; o silhouette dos itens atribuídos é 0,955757. Para outros valores de eps, há um único grupo e o silhouette não é definido. A cobertura baixa limita a utilidade desses resultados.

### 6.4 HDBSCAN e combinação híbrida

O notebook 74 usa 10.000 descrições da base anual filtrada, cinco configurações TF-IDF, min_cluster_size em 5, 10 e 20 e min_samples em None, 5 e 10, distância cosseno e semente 42. A melhor linha pela pontuação composta atual usa char_wb (5,10), min_cluster_size=20 e min_samples=5: dois grupos, sem ruído, silhouette 0,006381. Isso não demonstra grupos semanticamente coerentes.

O notebook 75 usa MPNet em 10.000 descrições. A melhor pontuação composta atual usa min_cluster_size=10 e min_samples=None: três grupos, 21,64% de ruído e silhouette 0,128221 calculado sobre 7.836 itens atribuídos. Uma configuração exportada com 134 grupos tem 68,12% de ruído e silhouette 0,319797 em 3.188 itens. As saídas registram modelos, mas não foi encontrado diretório models/mpnet_hdbscan na listagem atual; a persistência precisa ser reconciliada.

O notebook 76 combina TF-IDF e MPNet. Relatórios anteriores com alpha=0,5 registram como melhor linha char_wb (3,5), min_cluster_size=20 e min_samples=10: dois grupos, 28,86% de ruído, silhouette 0,100116. Um artefato híbrido salvo com 134 grupos tem 68,12% de ruído e silhouette 0,319797. A alteração local mais recente usa alpha=0,2 e produz 45 linhas de métricas; a melhor pontuação composta é 0,689523 para char_wb (3,5), min_cluster_size=10, dois grupos, 11,35% de ruído e silhouette 0,097649. A exportação do modelo dessa execução falha porque o identificador de execução ainda aponta para alpha=0,5. O código também usa pesos 0,7 para silhouette e 0,5 para cobertura, apesar de uma descrição indicar pesos iguais.

As pontuações compostas são critérios internos de triagem, não métricas de classificação. Não incorporam rótulos nem coerência semântica avaliada. Períodos, bases, amostras, métricas e configurações diferentes impedem ordenar os algoritmos como se fossem um estudo controlado. Uma alegação metodológica anterior sobre 328 grupos, 2% de ruído e silhouette 0,2034 não corresponde à execução atual identificada e precisa ser rastreada antes de ser usada.

## 7. Da descoberta de grupos à classificação e recuperação

O projeto já implementa uma função genérica em src/nofis_classifier/clustering.py para prever rótulos a partir de K-Means quando existe um mapeamento humano de grupos coerentes. Grupos sem rótulo e vetores nulos resultam em REVISAR. Os testes dessa função usam dados sintéticos; isso verifica o comportamento da implementação, mas não valida categorias reais.

O protótipo do notebook 90 carrega um modelo HDBSCAN híbrido salvo, mas não chama uma operação de previsão do HDBSCAN. Em vez disso, calcula similaridade cosseno TF-IDF, escolhe até dez vizinhos de treino sem ruído, vota no grupo e retorna até dez vizinhos desse grupo. A inferência usa somente TF-IDF e o vetoriza com o artefato carregado; não carrega o codificador SentenceTransformer nem reconstrói a representação híbrida usada no agrupamento. É, portanto, uma aproximação de propagação por vizinhos em TF-IDF, não inferência do agrupamento híbrido.

Esse protótipo ainda devolve um grupo, não uma categoria comercial. Não há codebook, categorias humanas, métrica de confiança calibrada nem avaliação de relevância dos vizinhos. A entrada pao gera vetor sem características com o vocabulário de palavras (2,5) e falha na execução salva.

Para atingir o objetivo de produto, o fluxo precisa: definir categorias interpretáveis; rotular uma amostra representativa; separar treino, validação e teste sem vazamento por duplicatas; mapear ou treinar o classificador; definir abstenção para casos ambíguos; retornar categoria com evidências de descrições semelhantes; e avaliar classificação e recuperação separadamente. A escolha entre classificar diretamente e usar grupos como etapa intermediária continua aberta.

## 8. Avaliação, reprodutibilidade e limitações

Silhouette, quantidade de grupos, tamanho dos grupos e proporção de ruído descrevem propriedades geométricas da representação e do agrupamento. Não medem se um grupo corresponde a uma categoria comercial nem se uma descrição recuperada é útil. A validação da solução deve incluir, no mínimo:

- concordância e desempenho de classificação em rótulos revisados por pessoas, com macro-F1, precisão/recall por categoria e matriz de confusão;
- cobertura e taxa de abstenção quando o sistema puder devolver REVISAR;
- relevância de vizinhos semelhantes por precisão@k ou julgamento humano em amostra;
- resultados por frequência e por categoria, além de análise de erros e estabilidade;
- separação de treino e teste que controle descrições repetidas e variantes quase duplicadas; considerar avaliação temporal se o uso pretendido incluir períodos futuros.

Os relatórios versionados em reports/ e os modelos em models/ são evidência de execuções e persistência, não de validação semântica. A execução de notebook precisa ser ligada ao código, à configuração, à base e ao identificador do artefato. A divergência de alpha e identificador no notebook 76 e a divergência de configuração e saída no notebook 71 são pendências de rastreabilidade.

## 9. Organização sugerida para o capítulo

1. Problema, objetivo e definição operacional de categoria comercial.
2. Fonte dos dados, população observada e limitações de representatividade.
3. Seleção dos NCMs, filtros, período e unidade de análise.
4. Limpeza textual, normalização e preservação das frequências.
5. Representações TF-IDF, MPNet e combinação híbrida.
6. Protocolo exploratório de agrupamento e resultados, identificado por base e execução.
7. Construção de rótulos, classificação, abstenção e recuperação de exemplos semelhantes.
8. Protocolo de validação e métricas, separando resultados já executados de trabalho futuro.
9. Limitações, ameaças à validade e decisões ainda abertas.

