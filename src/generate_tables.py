"""Genera tabla ejecutiva de asistencia World Cup 2026 con fallback a pandas styling."""

from pathlib import Path

import pandas as pd


def generate():
    csv_file = Path("dw_asistencia_sedes.csv")
    if not csv_file.exists():
        print("[TABLE] dw_asistencia_sedes.csv no encontrado")
        return

    df = pd.read_csv(csv_file, encoding="utf-8")
    top = df.nlargest(5, df.columns[-1] if len(df.columns) > 0 else df.columns[0])

    # Try great_tables first, fallback to pandas styling
    try:
        from great_tables import GT
        tbl = (
            GT(top)
            .tab_header(title="Top 5 Sedes — Asistencia World Cup 2026")
            .tab_source_note("Fuente: FIFA | Análisis: Álvaro Salinas")
        )
        Path("assets").mkdir(exist_ok=True)
        tbl.save("assets/executive_table.html")
        print("[TABLE] assets/executive_table.html generado (great_tables)")
    except ImportError:
        # Fallback: pandas styling
        styled = top.style.set_caption("Top 5 Sedes — Asistencia World Cup 2026") \
            .set_table_styles([
                {"selector": "caption", "props": [("font-size", "16px"), ("font-weight", "bold")]},
                {"selector": "th", "props": [("background-color", "#1a6b5a"), ("color", "white"), ("font-weight", "bold")]},
                {"selector": "td", "props": [("border", "1px solid #d4c9a8")]},
            ]) \
            .format(precision=0) \
            .hide(axis="index")
        Path("assets").mkdir(exist_ok=True)
        styled.to_html("assets/executive_table.html")
        print("[TABLE] assets/executive_table.html generado (pandas styling fallback)")


if __name__ == "__main__":
    generate()
