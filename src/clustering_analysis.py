"""
Clusterizacion de sedes Mundial 2026 por caracteristicas.
K-Means + silhouette + profiles.
"""

import json
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler

    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def run_clustering(
    data_dir: Path = Path("."), output_dir: Path = Path("data/export")
) -> dict:
    if not AVAILABLE:
        return {}

    csv_file = data_dir / "dw_asistencia_sedes.csv"
    if not csv_file.exists():
        print("[CLUSTER] dw_asistencia_sedes.csv no encontrado")
        return {}

    df = pd.read_csv(csv_file, encoding="utf-8")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) < 2:
        print("[CLUSTER] Need >= 2 numeric columns")
        return {}

    X = df[num_cols].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    silhouettes = []
    K_range = range(2, min(6, len(df) // 2 + 1))
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        silhouettes.append(silhouette_score(X_scaled, labels))

    optimal_k = list(K_range)[np.argmax(silhouettes)] if silhouettes else 2
    km_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    df["cluster"] = km_final.fit_predict(X_scaled)

    profiles = {}
    for c in range(optimal_k):
        cdf = df[df["cluster"] == c]
        profiles[f"cluster_{c}"] = {
            "size": len(cdf),
            "means": {col: round(cdf[col].mean(), 2) for col in num_cols},
        }
        if "city" in cdf.columns:
            profiles[f"cluster_{c}"]["cities"] = cdf["city"].tolist()
        elif "sede" in cdf.columns:
            profiles[f"cluster_{c}"]["sedes"] = cdf["sede"].tolist()

    results = {
        "optimal_k": optimal_k,
        "silhouette": round(max(silhouettes), 3) if silhouettes else 0,
        "profiles": profiles,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "clustering_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[CLUSTER] k={optimal_k}, silhouette={results['silhouette']}")
    return results


if __name__ == "__main__":
    run_clustering()
