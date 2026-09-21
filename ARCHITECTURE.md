# Arquitectura — worldcup-2026

## Visión general
Dashboard interactivo del Mundial FIFA 2026 con datos históricos y simulados, API Flask y frontend Dash/Plotly.

## Componentes principales

### Datos
- `data/historical.db` — SQLite con datos históricos de mundiales (1930-2022)
- `data/worldcup.db` — SQLite con datos simulados del Mundial 2026
- `src/seed_data.py` — Inicialización y poblamiento de bases de datos

### Backend (API)
- `api/server.py` — Flask REST API (`/api/*`)
- Endpoints: overview, goals-by-round, goals-by-confederation, top-scorers, stadiums, teams, knockout, group/<letter>

### Análisis (src/)
- `queries.py` — Consultas SQL parametrizadas
- `historical_data.py` — Carga de datos históricos
- `ranking_analysis.py` — Análisis de rankings
- `forecasting.py` — Predicciones
- `clustering_analysis.py` — Clustering
- `statistical_tests.py` — Tests estadísticos
- `sensitivity_analysis.py` — Análisis de sensibilidad
- `optimization_analysis.py` — Optimización
- `match_predictor.py` — Predicción de partidos
- `generate_tables.py` — Generación de tablas
- `generate_report.py` — Generación de reportes
- `export_visualizations.py` — Exportación de visualizaciones

### Frontend (Dashboard)
- `dashboard/app.py` — Dash app principal con tabs: Overview, Grupos, Eliminatorias, Goleadores, Estadios, Equipos, Predicciones

## Flujo de datos
1. `seed_data.py` → crea y puebla `historical.db` y `worldcup.db`
2. `api/server.py` consulta las BDs y sirve JSON
3. `dashboard/app.py` consume la API y renderiza gráficos Plotly

## Despliegue
- Render: `gunicorn dashboard.app:server` (ver `render.yaml`)
- Puerto: `$PORT` (variable de entorno)
- Workers: 2

## Tests
- `tests/test_queries.py` — Tests de consultas SQL con BD temporal
- `tests/test_analysis.py` — Smoke tests de imports
- CI: pytest + coverage + ruff