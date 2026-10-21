# Matriz de experimentos e evidências

## Como ler esta matriz

“Executado” indica que foram encontradas saídas ou artefatos associados. “Validado” exige avaliação apropriada ao objetivo final. Silhouette e score composto não equivalem a validação de categoria. Valores devem ser comparados somente quando base, período, amostra, representação, parâmetros e protocolo coincidirem.

## Dados e preparação

| Etapa | Base e configuração | Evidência/resultado | Estado e observações |
|---|---|---|---|
| Download e conversão | Arquivos mensais do Portal da Transparência; notebook 10 | Conversão para Parquet | Executado. A fonte cobre notas ligadas a aquisições da Administração Pública Federal. |
| Exploração da fonte | Ano de 2025; notebook 11 | 7.639.476 linhas; 5.979.164 com descrição; 1.352.762 descrições originais distintas | Executado sobre o conjunto anual bruto/intermediário. |
| Seleção de NCM | Notebook 13; emissores localizados por padrões textuais | 397 emissores selecionados para análise; top 10 usados; 453 NCM observados; mínimo de 5 ocorrências; lista atual com 241 códigos | Executado, mas seleção exploratória. O critério de domínio precisa ser validado. |
| Filtro anual por NCM | Notebook 21; 241 códigos com oito dígitos e igualdade exata; 12 meses de 2025 | 868.292 linhas de itens | Executado. Lista derivada de emissores selecionados, aplicada à base anual inteira. |
| Limpeza e consolidação | Notebook 41; descrição normalizada; frequência preservada | 868.288 ocorrências válidas; 149.149 descrições distintas consolidadas; soma de frequência 868.288; mediana 1; máximo 7.814 | Executado. Quatro linhas nulas/vazias descartadas; 28.213 sequências numéricas longas removidas do texto. |
| Contagem intermediária distinta | Notebook 30; trim e minúsculas | 155.963 descrições | Executado com normalização mais leve; não comparar diretamente com o resultado do notebook 41. |
| Variante histórica | data/processed/2025_NCMs-sem-duplicatas | 257.879 descrições; frequência total 1.238.688 | Artefato existente, proveniência exata não reconciliada com o fluxo ativo. |

## Experimentos de agrupamento

| ID / notebook | Base, período e amostra | Representação e método | Configuração e resultado reportado | Evidência, limites e estado |
|---|---|---|---|---|
| KMeans exploratório / 60 | Itens com filtros combinados, jan–abr; 27.800 descrições; 134.624 de frequência; amostra simulada de 1.000 | TF-IDF palavras (1,1); K-Means | min_df=2; até 5.000 características; k=25; silhouette 0,075869; grupos de 6 a 417 | Execução para inspeção exploratória. Não é classificador final. |
| Grade TF-IDF / reports/grid_tfidf_kmeans/202501-202504_20260927T163113Z_3df937b0 | Jan–abr; 27.500 treino e 300 reservadas | Seis configurações TF-IDF; K-Means | k=10,15,20,25,30,40,60,80; três sementes; 144 ajustes. Melhor silhouette mediano 0,091191: char_wb (3,5), min_df=5, max_features=30.000, k=80 | Relatórios de revisão existem, mas rotulo_humano está vazio e status permanece REVISAR. Outra pasta contém resultados duplicados da grade. |
| TF-IDF anual / 70 | Base 2025_NCMs_filtrados; 5.000 amostras, 4.700 treino, 300 reservadas; semente 42 | TF-IDF palavras (1,1), palavras (1,2) e char_wb (3,5); K-Means | min_df=5; max_df=0,02; max_features=100.000; k=20,50,100,200; melhor reportado char_wb (3,5), k=200; silhouette 0,141113; 191 grupos ocupados; maior grupo 15,43% | Executado. noise_fraction nesta saída indica vetores TF-IDF nulos; não é ruído K-Means. SELECTED_EXPERIMENT_ID continua None; não há validação manual registrada. |
| MPNet K-Means / 71 | Saída indica jan–abr; configuração ativa aponta para base anual | MPNet, vetores de 768 dimensões; K-Means | k=10,20,30,40,2.000,3.000; três sementes. k=40: mediana silhouette 0,128974, desvio 0,009335. k=2.000: 0,057699; k=3.000: 0,062694 | Saídas executadas, mas configuração e saída divergem. Tratar como histórico até reconciliar. |
| DBSCAN TF-IDF / 72 | Base anual filtrada; amostra de 5.000; semente 42 | TF-IDF palavras; DBSCAN | Linha composta superior: n-gramas (2,4), eps=0,035, min_samples=2; 150 grupos; ruído 75,48%; silhouette 0,999431 nos atribuídos; score composto 0,622458 | Execução salva. Silhouette calculado somente sobre a fração atribuída; cobertura muito baixa. Pesos compostos 0,5/0,5. |
| DBSCAN MPNet / 73 | Base anual filtrada; amostra de 5.000; semente 42 | MPNet; DBSCAN | eps=0,03, min_samples=3; 13 grupos; ruído 99,02%; silhouette 0,955757 nos atribuídos. Outras configurações geram um grupo e silhouette indefinido | Execução salva. Cobertura inadequada para o objetivo final. |
| HDBSCAN TF-IDF / 74 | Base anual filtrada; amostra de 10.000; semente 42 | Cinco configurações TF-IDF; HDBSCAN; distância cosseno | min_cluster_size=5,10,20; min_samples=None,5,10; eom. Linha composta superior: char_wb (5,10), mcs=20, ms=5; 2 grupos; ruído 0%; silhouette 0,006381; composto 0,751595 | Execução salva. Dois grupos quase sem separação; score alto não comprova utilidade semântica. Pesos compostos declarados como 0,5/0,5. |
| HDBSCAN MPNet / 75 | Base anual filtrada; amostra de 10.000; semente 42 | MPNet; HDBSCAN; cosseno | mcs=2,5,10,20; ms=None,2,5,10; eom. Linha composta superior: mcs=10, ms=None; 3 grupos; ruído 21,64%; silhouette 0,128221 (7.836 atribuídos); score 0,673855. Variante exportada: 134 grupos, 68,12% de ruído, silhouette 0,319797 (3.188 atribuídos) | Execução e atribuições registradas. Diretório de modelo mpnet_hdbscan não foi localizado na listagem atual; verificar persistência. |
| HDBSCAN híbrido histórico / 76 e reports/tfidf_mpnet_hdbscan | Base anual filtrada; amostra de 10.000 | TF-IDF + MPNet normalizados e concatenados; alpha=0,5 | Linha superior histórica: char_wb (3,5), mcs=20, ms=10; 2 grupos; ruído 28,86%; silhouette 0,100116; score 0,630729. Modelo salvo de 134 grupos: ruído 68,12%; silhouette 0,319797 | Artefatos alpha=0,5 existentes; o modelo de 134 grupos é usado pelo notebook 90. Sem rótulos humanos. |
| HDBSCAN híbrido recente / 76, diretório 202501-202512_20261018T160430Z860319 | Base anual filtrada; amostra de 10.000 | TF-IDF + MPNet; alpha=0,2 | 45 linhas. Melhor score composto 0,689523: char_wb (3,5), mcs=10, ms=None/10; 2 grupos; ruído 11,35%; silhouette 0,097649 | Métricas locais disponíveis. Exportação não conclui porque ARTIFACT_RUN_ID continua apontando a alpha=0,5. O código combina pesos 0,7 e 0,5, em divergência com texto que informa pesos iguais. |

## Componentes de classificação e recuperação

| Componente | Base/artefato | Comportamento observado | Estado |
|---|---|---|---|
| predict_categories em src/nofis_classifier/clustering.py | Modelo K-Means e mapa de grupos fornecido | Mapeia grupos marcados coerentes com rótulo; grupo sem rótulo e vetor nulo resultam em REVISAR; admite mais de um grupo por rótulo | Implementado e coberto por testes sintéticos. Sem mapeamento real de categorias. |
| Revisão de agrupamentos | cluster_review.csv em relatórios de K-Means | Arquivos contêm linhas de revisão; campos de rótulo humano vazios e status REVISAR | Artefato preparado; processo de revisão não concluído. |
| Inferência do notebook 90 | Modelo híbrido HDBSCAN e atribuições salvas; TF-IDF carregado | Compara a descrição com vizinhos TF-IDF sem ruído, vota em grupo e retorna vizinhos do grupo | Protótipo executado parcialmente. Não chama HDBSCAN predict e não reconstrói vetores híbridos. |
| Entrada lexical curta | notebook 90, exemplo pao | TF-IDF de palavras com n-gramas (2,5) gera vetor sem características | Falha observada; não há política de fallback/abstenção para esse caso no protótipo. |
| Categoria comercial e exemplos | Objetivo final declarado | Nenhum arquivo de categorias, predições reais ou avaliação de relevância localizado | Pendente. |

## Métricas necessárias para o objetivo final

| Pergunta | Métricas/avaliação sugeridas | Evidência atual |
|---|---|---|
| A categoria atribuída está correta? | Macro-F1, precisão e recall por categoria, matriz de confusão em conjunto rotulado independente | Nenhuma avaliação real encontrada |
| Quando o sistema deve pedir revisão? | Cobertura, taxa de abstenção e erro entre previsões aceitas | Há política REVISAR no helper K-Means, mas sem calibragem em dados reais |
| Os exemplos semelhantes ajudam? | Precisão@k ou julgamento humano de relevância em amostra | Nenhuma avaliação localizada |
| O método generaliza? | Divisão sem duplicatas/vizinhos quase idênticos entre treino e teste; eventualmente corte temporal | Não executada |
| Os agrupamentos fazem sentido comercial? | Revisão humana com codebook e concordância entre revisores | Revisões ainda sem rótulos |

