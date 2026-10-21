# Diagnóstico metodológico

## Síntese

O repositório contém uma exploração extensa de agrupamento e componentes reutilizáveis para classificação e inspeção de vizinhos. Ainda não contém evidência de um classificador validado para categorias comerciais. A diferença central é a ausência de rótulos de domínio e de avaliação independente: métricas geométricas de clustering não demonstram que os grupos correspondam a categorias úteis.

Este diagnóstico distingue três estados:

- **Implementado:** código ou fluxo existe no repositório.
- **Executado:** há saída ou artefato de uma execução identificável.
- **Validado:** o resultado foi avaliado contra rótulos ou critérios humanos independentes adequados ao objetivo.

Uma execução salva não implica validação.

## Achados prioritários

### 1. A fonte não representa diretamente o público consumidor

O Portal da Transparência informa que as notas fiscais se relacionam a aquisições da Administração Pública Federal. A análise seleciona NCMs a partir de emissores reconhecidos como supermercados e depois filtra a base anual completa por esses NCMs. Isso não transforma as notas em uma amostra de compras de consumidores nem prova que todos os itens filtrados sejam produtos de supermercado. A população, a pergunta de pesquisa e as conclusões precisam ser alinhadas.

Fontes: [descrição das notas fiscais no Portal](https://portaldatransparencia.gov.br/entenda-a-gestao-publica/notas-fiscais) e [download de dados](https://portaldatransparencia.gov.br/download-de-dados/notas-fiscais).

### 2. Não há rótulos comerciais para comprovar a classificação

Não foram encontrados codebook de categorias, rótulos humanos preenchidos, arquivo validation_labels.csv, predições avaliadas ou métricas de classificação real. Os arquivos cluster_review.csv existentes têm status REVISAR e campo rotulo_humano vazio. O protótipo não pode ser descrito como classificador de categorias já validado.

### 3. Métricas de agrupamento são usadas como proxies insuficientes

Silhouette, proporção de ruído e número de grupos descrevem a geometria dos dados na representação adotada. DBSCAN e HDBSCAN mostram silhouette alto em casos de cobertura muito baixa; o silhouette de TF-IDF HDBSCAN próximo de zero acompanha apenas dois grupos. Os scores compostos favorecem configurações por pesos definidos no código, mas não medem coerência de categoria, utilidade comercial ou qualidade da recuperação. São adequados para triagem exploratória, não para alegar eficácia do classificador.

### 4. O protótipo de inferência não reproduz o espaço do modelo híbrido

O notebook 90 usa um artefato HDBSCAN híbrido, confere os rótulos salvos e depois seleciona vizinhos via cosseno TF-IDF. Ele não invoca previsão HDBSCAN, não reconstitui o vetor híbrido e não carrega o codificador MPNet. A saída é um cluster e exemplos próximos, sem categoria comercial ou confiança calibrada. O caso de entrada pao falha porque o TF-IDF de palavras (2,5) produz vetor nulo.

Isso deve ser documentado como um protótipo de busca/propagação em TF-IDF separado da inferência híbrida. A relevância dos exemplos semelhantes também não foi avaliada.

### 5. Os experimentos não compõem uma comparação controlada

Os notebooks usam bases e períodos diferentes, inclusive amostras de janeiro a abril e do ano completo, tamanhos de 1.000, 5.000 e 10.000, diversas configurações e critérios. Há saída salva de janeiro a abril no notebook 71 cuja configuração ativa aponta para uma base anual. No notebook 76, a execução local alpha=0,2 não atualizou o identificador de exportação, que ainda aponta para alpha=0,5. Os resultados devem ser apresentados por execução identificada, sem ranking global dos algoritmos até que um protocolo comum seja executado.

## Componentes existentes e estado da evidência

| Componente | Implementado | Executado | Validado para categorias reais |
|---|---|---|---|
| Download mensal e conversão para Parquet | Sim, notebook 10 | Sim, registros locais | Não se aplica à classificação |
| Seleção exploratória de NCMs | Sim, notebook 13 | Sim; lista atual com 241 códigos | Não; adequação de domínio pendente |
| Filtro anual exato pelos NCMs | Sim, notebook 21 | Sim; 868.292 itens | Não; população e precisão do filtro pendentes |
| Limpeza e consolidação | Sim, notebook 41 | Sim; 868.288 ocorrências e 149.149 descrições | Não; regras ainda requerem avaliação de domínio |
| TF-IDF e MPNet | Sim, módulos/notebooks | Sim, em diferentes bases e amostras | Não |
| K-Means, DBSCAN e HDBSCAN | Sim | Sim, várias grades e relatórios | Não há revisão humana concluída |
| Revisão de clusters | Ferramenta/arquivos presentes | Arquivos gerados; rótulos em branco | Não |
| Mapeamento de cluster para rótulo em predict_categories | Sim; cobre K-Means e abstenção | Testes sintéticos no repositório | Não com mapeamentos reais |
| Inferência e busca no notebook 90 | Sim, protótipo | Sim parcialmente; entrada pao falha | Não; não retorna categoria validada |
| Recuperação de descrições semelhantes | Busca TF-IDF implementada | Saída pretendida no protótipo | Não; sem julgamento de relevância |

## Reconciliação de números e artefatos

- A base ativa do notebook 41 resulta em 868.288 ocorrências válidas após quatro linhas removidas, 28.213 sequências longas de dígitos retiradas do texto e 149.149 descrições consolidadas.
- O notebook 30 conta 155.963 descrições após uma normalização mais leve; a diferença é compatível com definições distintas de normalização.
- A variante 2025_NCMs-sem-duplicatas tem 257.879 linhas e frequência total 1.238.688. Sua origem exata não está bem ligada ao fluxo ativo; não misturar esse resultado com o conjunto filtrado.
- A alegação de 158.293 descrições únicas não foi encontrada nos artefatos examinados.
- Os relatórios antigos de HDBSCAN TF-IDF que alegam 328 grupos, 2% de ruído e silhouette 0,2034 não correspondem ao resultado atualmente identificado no notebook 74. Rastrear o notebook/configuração antes de reaproveitar.
- O notebook 71 tem divergência entre a configuração ativa e a saída histórica.
- O notebook 76 mais recente produz métricas alpha=0,2, mas a exportação falha por identificador desatualizado. Não há modelo alpha=0,2 correspondente identificado.
- Há modelos e relatórios persistidos, mas persistência não significa validação.

## Inconsistências documentais

- docs/metodologia.md é apenas um esboço, não corresponde ao volume de experimentos atual.
- docs/plano-implementacao-tcc.md ainda descreve um escopo centrado em taxonomia e deve ser alinhado à meta de categoria comercial e exemplos semelhantes.
- O README aponta para notebooks/70_matriz_tfidf_kmeans_e_validacao.ipynb, caminho não encontrado; o notebook existente é notebooks/70_tfidf_kmeans.ipynb.
- O protocolo precisa separar explicitamente os rótulos de cluster exploratório das categorias comerciais finais.

## Próximo passo de maior valor

Antes de ampliar a busca de hiperparâmetros, definir população, categorias e processo de anotação. Em seguida, construir um conjunto humano pequeno, mas rastreável, que permita medir classificação e recuperação. Sem isso, novos scores de agrupamento ampliam o inventário experimental sem responder se o sistema atende ao objetivo.

## Perguntas para orientação

1. O domínio-alvo deve ser descrito como itens registrados em aquisições da Administração Pública Federal, ou há uma fonte alternativa representativa de compras de consumidores?
2. As categorias devem seguir uma taxonomia comercial existente, os grupos descobertos ou um codebook construído para a pesquisa?
3. O resultado principal será um classificador supervisionado, um mapeamento humano de clusters ou uma combinação com revisão/abstenção?
4. Que nível de precisão e cobertura é necessário para recomendar automaticamente uma categoria?
5. Os exemplos semelhantes são parte obrigatória da saída e devem ser julgados por especialistas?

