"""Summarize the completed grid without changing model or human-review artifacts."""
import json
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
run = Path("reports/grid_tfidf_kmeans/202501-202504_20260926T194715Z_7df01672")
metrics = pd.read_csv(run / "metrics.csv")
ranking = pd.read_csv(run / "ranking.csv")
candidates = pd.read_csv(run / "candidates.csv")
assert len(metrics) == 144, "Aguarde a grade completa."
best = ranking.groupby("config_name", sort=False).head(1)
best.to_csv(run / "melhor_por_representacao.csv", index=False)
names = {
    "word_1_1_df2_max10000": "Palavras; min_df=2",
    "word_1_1_df5_max10000": "Palavras; min_df=5",
    "word_1_2_df2_max10000": "Palavras + bigramas; min_df=2",
    "word_1_2_df5_max10000": "Palavras + bigramas; min_df=5",
    "char_wb_3_5_df2_max30000": "Caracteres 3–5; min_df=2",
    "char_wb_3_5_df5_max30000": "Caracteres 3–5; min_df=5",
}
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for config, rows in ranking.groupby("config_name", sort=False):
    rows = rows.sort_values("k")
    axes[0].plot(rows.k, rows.silhouette_median, marker="o", label=names[config])
    axes[1].plot(rows.k, rows.largest_cluster_fraction * 100, marker="o", label=names[config])
axes[0].set(title="Separação dos grupos", xlabel="Número de clusters (k)", ylabel="Silhouette cosseno — mediana de 3 sementes")
axes[1].set(title="Concentração no maior grupo", xlabel="Número de clusters (k)", ylabel="% das descrições — mediana de 3 sementes")
for ax in axes:
    ax.grid(alpha=0.25)
axes[1].legend(fontsize=8)
fig.suptitle("TF-IDF + K-Means: 27.500 descrições de treino; métricas em amostra fixa de 1.000")
fig.tight_layout()
fig.savefig(run / "comparacao_interpretavel.png", dpi=160, bbox_inches="tight")
plt.close(fig)

evidence = {
    "completed": len(metrics), "status_counts": metrics.status.value_counts().to_dict(),
    "total_fit_seconds": float(metrics.elapsed_seconds.sum()),
    "reached_max_iter": int(metrics.reached_max_iter.sum()),
    "best_per_representation": best.to_dict(orient="records"),
    "top_ten": ranking.head(10).to_dict(orient="records"),
    "candidates": [],
}
for row in candidates.itertuples(index=False):
    review_dir = run / "review" / row.experiment_id
    review = pd.read_csv(review_dir / "cluster_review.csv").fillna("")
    record = {
        "experiment_id": row.experiment_id,
        "silhouette": row.silhouette_cosine,
        "ch": row.calinski_harabasz,
        "db": row.davies_bouldin,
        "largest_fraction": row.largest_cluster_fraction,
        "sample_clusters": row.sample_clusters,
        "top_clusters": review.head(12).to_dict(orient="records"),
        "bottom_clusters": review.tail(3).to_dict(orient="records"),
    }
    evidence["candidates"].append(record)
(run / "interpretation_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
logging.info("RESUMO\n%s", best.to_string(index=False))
logging.info("CANDIDATOS\n%s", candidates[["experiment_id", "silhouette_cosine", "calinski_harabasz", "davies_bouldin", "largest_cluster_fraction", "sample_clusters"]].to_string(index=False))
logging.info("Status: %s; tempo somado dos ajustes %.1f minutos; atingiram max_iter: %s", evidence["status_counts"], evidence["total_fit_seconds"] / 60, evidence["reached_max_iter"])

# These are assistant observations of examples, not human ground truth or purity estimates.
word_id = "word_1_1_df5_max10000_k80_seed42"
word_review = pd.read_csv(run / "review" / word_id / "cluster_review.csv")
observations = [
    (30, "heterogeneo", "", "Mistura alimentos, limpeza e baterias; inclui as 200 descrições com vetor zero. Os exemplos centrais podem ser artefatos dessa ausência de vocabulário."),
    (45, "coerente nos exemplos", "Biscoitos", "Exemplos centrais, distantes e aleatórios são biscoitos; conferir mais itens antes de aceitar o grupo inteiro."),
    (27, "coerente nos exemplos", "Biscoitos", "Descrições abreviadas como bisc foram separadas do cluster 45; ambos podem compartilhar a mesma categoria."),
    (66, "coerente nos exemplos", "Feijões e leguminosas", "Amostras apresentam feijões; há broto de feijão, cuja inclusão depende da granularidade da taxonomia."),
    (65, "parcialmente coerente", "Arroz — revisar exceções", "Amostras centrais são arroz alimentício, mas exemplos distantes incluem sementes para plantio."),
    (75, "parcialmente coerente", "Refrigerantes — revisar exceções", "Predominam refrigerantes nos exemplos, mas há refeição buffet incluindo refrigerante."),
    (56, "parcialmente coerente", "Leites — revisar exceções", "Exemplos aleatórios são leites; exemplos distantes incluem torradas e biscoitos integrais."),
    (16, "heterogeneo", "", "A palavra pó aproxima leite, achocolatado e sabão, cruzando alimentação e limpeza."),
    (9, "heterogeneo", "", "500ml aproxima detergente, azeite, soro e utensílios; volume não define categoria."),
    (61, "heterogeneo", "", "500g aproxima massas, café, frutas, manteiga e outros produtos."),
    (35, "heterogeneo", "", "2l reúne refrigerantes, desinfetantes e recipientes."),
    (23, "heterogeneo", "", "Limão aparece como fruta, sabor e fragrância de produtos de limpeza."),
]
suggestions = pd.DataFrame(observations, columns=["cluster", "avaliacao_assistente", "categoria_sugerida", "justificativa"])
suggestions.insert(0, "experiment_id", word_id)
suggestions["origem_avaliacao"] = "Inspeção pelo assistente de exemplos centrais, distantes e aleatórios; exige revisão humana."
suggestions = suggestions.merge(word_review[["cluster", "descricoes_unicas", "sem_vocabulario"]], on="cluster", validate="one_to_one")
suggestions.to_csv(run / "review" / word_id / "sugestoes_assistente.csv", index=False, encoding="utf-8-sig")

char_id = "char_wb_3_5_df2_max30000_k80_seed2026"
char_review = pd.read_csv(run / "review" / char_id / "cluster_review.csv")
char_observations = [
    (0, "heterogeneo", "", "6.621 descrições; exemplos incluem lixeiras, massa de pastel, absorventes, biscoitos e frutas."),
    (29, "heterogeneo", "", "Contagem nas atribuições: 211 descrições contêm feijao e 88 contêm requeijao; categorias distintas compartilham fragmentos da escrita."),
    (40, "coerente nos exemplos", "Biscoitos", "Exemplos centrais, distantes e aleatórios inspecionados são biscoitos; ainda requer revisão humana ampliada."),
    (42, "coerente nos exemplos", "Farinhas e derivados de trigo", "Inclui farinha de trigo, farelo, trigo para quibe e panko; o nome da categoria deve refletir essa amplitude."),
    (65, "coerente nos exemplos", "Molhos e condimentos", "Molhos e pimentas aparecem nos três tipos de exemplos; não limitar o rótulo a molho de pimenta."),
    (73, "parcialmente coerente", "Arroz — revisar exceções", "Predominam descrições de arroz nos exemplos; há colher de arroz, sementes e caneca de fibra de arroz entre os distantes."),
    (36, "parcialmente coerente", "Refrigerantes — revisar exceções", "Há leite cru refrigerado e refeição buffet com refrigerante entre os exemplos distantes."),
    (24, "parcialmente coerente", "Leites e derivados — revisar exceções", "Mistura leite, creme, leite condensado, doces e suplemento para animais com leite na descrição."),
    (8, "heterogeneo", "", "Exemplos de sabonete líquido misturam-se a molho shoyo, achocolatado líquido e polidor."),
    (62, "coerente no tipo, revisar escopo", "Detergentes", "Inclui detergentes domésticos, automotivos e enzimáticos; escopo de mercado exige revisar aplicações."),
    (9, "coerente nos exemplos, revisar escopo", "Lâmpadas", "Exemplos são lâmpadas, muitas automotivas; a inclusão depende do escopo da taxonomia."),
    (71, "coerente nos exemplos, revisar escopo", "Lâmpadas", "Predominam lâmpadas automotivas 12V; pode compartilhar categoria com o cluster 9."),
]
char_suggestions = pd.DataFrame(char_observations, columns=["cluster", "avaliacao_assistente", "categoria_sugerida", "justificativa"])
char_suggestions.insert(0, "experiment_id", char_id)
char_suggestions["origem_avaliacao"] = "Inspeção pelo assistente; somente a mistura feijão/requeijão foi contada em todo o cluster. Demais conclusões são amostrais."
char_suggestions = char_suggestions.merge(char_review[["cluster", "descricoes_unicas", "sem_vocabulario"]], on="cluster", validate="one_to_one")
char_suggestions.to_csv(run / "review" / char_id / "sugestoes_assistente.csv", index=False, encoding="utf-8-sig")
