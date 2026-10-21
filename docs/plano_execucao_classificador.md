# Plano de execução do classificador

## Objetivo do plano

Levar o repositório dos agrupamentos exploratórios atuais a um sistema que atribua uma categoria comercial interpretável e apresente descrições semelhantes como evidência. O plano mantém a estrutura atual dos notebooks e do pacote; recomenda novas abstrações somente quando uma necessidade compartilhada estiver clara.

## Etapas priorizadas

| Prioridade | Etapa | Situação atual | Trabalho necessário | Critério de conclusão |
|---|---|---|---|---|
| P0 | Fixar a população e a pergunta de pesquisa | A fonte é o Portal da Transparência, com registros ligados a aquisições da Administração Pública Federal. O texto de projeto alude a compras de consumidores/supermercados. | Escolher e justificar a população-alvo. Explicar a distância entre a população da fonte e o domínio comercial desejado; se o objetivo exigir compras reais de consumidores, decidir se esta base serve ou se é necessária outra fonte. | Pergunta, população, período e limites estão formulados consistentemente na metodologia e no capítulo de resultados. |
| P0 | Reconciliar a base de análise | O fluxo ativo tem 868.292 itens e 149.149 descrições após normalização; uma variante histórica tem 257.879 linhas e frequência 1.238.688. A proveniência dessa variante não está clara. | Declarar qual artefato é canônico; registrar a origem do outro ou deixá-lo fora da análise principal. Confirmar números com caminho, notebook e execução. | Um único caminho de dados canônico é reproduzível e os totais do texto correspondem aos artefatos. |
| P0 | Definir o codebook comercial | Não foi localizado codebook nem taxonomia final. Os clusters ainda não têm rótulos humanos. | Definir categorias e regras de inclusão/exclusão; registrar casos que podem pertencer a múltiplas categorias e a categoria de revisão. Preferir uma taxonomia existente se ela se ajustar ao domínio e às descrições. | Codebook versionado com nome, definição, exemplos positivos/negativos e regras de fronteira por categoria. |
| P0 | Construir conjunto rotulado | Os CSVs de revisão estão sem rótulos; não há arquivo de validação real. | Amostrar descrições pelo domínio e pela frequência, cobrir descrições ambíguas e raras, anotar conforme codebook e registrar decisões. Se viável, obter segunda revisão de parte da amostra e medir concordância. | Conjunto rotulado rastreável, com procedimento de anotação, versão de codebook e decisões de desacordo. |
| P1 | Fixar um protocolo sem vazamento | O notebook 70 separa 4.700/300 descrições distintas, mas não há rótulos; controle de quase duplicatas e avaliação temporal não está estabelecido. | Definir divisão treino/validação/teste por descrição normalizada e agrupar variantes quase duplicadas antes da divisão. Se a aplicação futura for temporal, reservar período posterior. Congelar semente e amostra. | Divisões documentadas e reutilizáveis; teste não usado na seleção de modelo. |
| P1 | Escolher abordagem de classificação e abstenção | Existe helper K-Means que mapeia clusters rotulados e devolve REVISAR; não há mapeamentos reais. O objetivo pode ser atendido por classificador supervisionado, cluster + revisão ou combinação. | Começar com baseline simples usando a representação já disponível. Comparar a classificação direta com o mapeamento de clusters apenas se ambos puderem ser treinados e avaliados no mesmo split. Definir quando retornar REVISAR. | Modelo e política de abstenção escolhidos por métricas no conjunto de validação e com análise dos erros por categoria. |
| P1 | Padronizar representação e inferência | TF-IDF, MPNet e híbrido foram explorados em configurações diferentes. O notebook 90 usa TF-IDF para vizinhos embora carregue artefato de agrupamento híbrido. | Selecionar e versionar a representação usada no treino e na inferência. Tornar a inferência compatível com o artefato salvo. Tratar entradas com vetor nulo, como pao, com fallback ou abstenção. | Inferência em sessão limpa reproduz a representação selecionada, tem comportamento definido para entradas fora do vocabulário e não mistura versões de artefatos. |
| P1 | Avaliar descrições semelhantes | A busca por vizinhos TF-IDF existe como protótipo, mas não tem avaliação de relevância. | Criar consultas rotuladas e julgar os primeiros k exemplos; comparar configurações de representação e registrar se os vizinhos pertencem à mesma categoria ou são úteis ao usuário. | Resultados de precisão@k ou julgamento humano, com amostra e critério de relevância documentados. |
| P2 | Comparar modelos sob condições comuns | As experiências variam em período, base, dimensão de amostra e objetivos. Scores compostos não incluem rótulos. | Após estabilizar rótulos e split, comparar baselines no mesmo dado, com a mesma divisão e métricas. Manter clustering como etapa exploratória ou método candidato, sem tratar silhouette como métrica final. | Matriz de resultados reproduzível, com macro-F1, desempenho por classe, cobertura/abstenção e recuperação lado a lado. |
| P2 | Completar rastreabilidade dos notebooks e artefatos | Há divergências no notebook 71 e no identificador de exportação do notebook 76; diretório de modelo MPNet não foi localizado. | Registrar id de execução, data, caminho da base, hash/versão da configuração, parâmetros e caminho de saída. Corrigir referências cruzadas antes de novas execuções. | Cada tabela de resultado aponta para código, configuração e artefato correspondentes; execuções incompletas são identificadas. |
| P2 | Atualizar a documentação do projeto | Metodologia é um esboço; plano ainda prioriza taxonomia; README aponta para notebook ausente. | Revisar documentos após as decisões P0/P1 e corrigir caminhos. Separar explicitamente resultados executados de atividades propostas. | README e documentos descrevem os notebooks e objetivo atuais sem caminhos quebrados ou números não rastreados. |

## Caminho crítico mínimo

1. Decidir população-alvo e adequação da fonte.
2. Escolher e reconciliar a base canônica.
3. Aprovar o codebook.
4. Rotular e revisar uma amostra com rastreabilidade.
5. Congelar divisão sem vazamento.
6. Treinar e comparar baseline de classificação, incluindo política REVISAR.
7. Avaliar recuperação de descrições semelhantes.
8. Revisar erros, documentar limites e só então ampliar a busca de parâmetros.

## Sequência de execução por notebook

Os notebooks devem continuar autocontidos nas configurações específicas de cada análise. Depois das decisões de domínio:

- Atualizar o notebook de preparação para explicitar a base canônica, o significado de cada contagem e a unidade de análise.
- Completar a revisão humana dos clusters somente se clustering permanecer como candidato ou instrumento de exploração.
- Criar um notebook numerado e descritivo para anotação/avaliação ou classificação, com objetivo, parâmetros e fluxo completos no próprio notebook.
- Deixar código no pacote apenas quando for compartilhado entre análises ou tiver responsabilidade independente clara; documentar funções públicas em Python.
- Identificar células de persistência e gravar novos artefatos com nomes versionados. Não sobrescrever modelos existentes.

## Entrega final esperada

Uma execução limpa deve aceitar uma descrição de item, devolver categoria comercial ou REVISAR, exibir descrições semelhantes com sua similaridade/ordem e permitir rastrear modelo, representação e versão do codebook. O capítulo deve apresentar avaliação em dados rotulados independentes, métricas por categoria, cobertura, erros representativos e qualidade dos exemplos recuperados. Até que esses critérios sejam atendidos, o sistema deve ser descrito como protótipo exploratório.

