# Contributing

¡Gracias por tu interés en contribuir a **worldcup-2026-dashboard**!

Este proyecto es un dashboard interactivo del Mundial FIFA 2026 construido con Python, SQLite, Streamlit y Plotly.

## Entorno de desarrollo

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt -r requirements-dev.txt
```

## Inicializar la base de datos

```bash
python -m src.seed_data
```

## Ejecutar la app

```bash
streamlit run src/app.py
```

## Tests y calidad

```bash
pytest                              # suite de tests sobre SQLite temporal
pytest --cov=. --cov-report=term-missing   # con cobertura
ruff check .                        # lint
ruff format --check .               # formato
```

Toda contribución debe pasar `ruff check .`, `ruff format --check .` y la suite de `pytest` antes de abrir un PR.

## Convenciones de commits

Se usa [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add group stage knockout bracket view
fix: correct attendance aggregation query
test: cover filtered_matches by confederation
chore: bump plotly to >=5.18
```

## Proceso para contribuir

1. Haz un *fork* del repositorio y crea una rama descriptiva (`feat/nueva-seccion`, `fix/agregacion-asistencia`).
2. Realiza los cambios y añade/actualiza los tests correspondientes.
3. Ejecuta lint + formato + tests localmente.
4. Abre un Pull Request describiendo el cambio y el motivo.

Gracias por mantener la calidad del proyecto.