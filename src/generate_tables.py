"""Genera tabla ejecutiva de asistencia World Cup 2026 con great_tables"""

from pathlib import Path

import pandas as pd
from great_tables import GT


def generate():
    csv_file = Path("dw_asistencia_sedes.csv")
    if not csv_file.exists():
        print("[TABLE] dw_asistencia_sedes.csv no encontrado")
        return

    df = pd.read_csv(csv_file, encoding="utf-8")
    top = df.nlargest(5, df.columns[-1] if len(df.columns) > 0 else df.columns[0])

    tbl = (
        GT(top)
        .tab_header(title="Top 5 Sedes — Asistencia World Cup 2026")
        .tab_source_note("Fuente: FIFA | Análisis: Álvaro Salinas")
    )
    Path("assets").mkdir(exist_ok=True)
    tbl.save("assets/executive_table.html")
    print("[TABLE] assets/executive_table.html generado")


if __name__ == "__main__":
    generate()
