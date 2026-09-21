# Mundial 2026 — Análisis con datos simulados del torneo (Proyección)

> ⚠️ **AVISO IMPORTANTE**: Los datos del Mundial 2026 en este proyecto son **simulados/proyectados**, no reales. El torneo no se ha disputado aún (programado para junio-julio 2026). Este proyecto es un ejercicio de análisis de datos que modela cómo *podría* verse el torneo basándose en rankings FIFA, formato de 48 equipos y datos históricos 2014-2022.

Después de que España levantara la copa en MetLife **en esta simulación**, me quedé con la duda: ¿qué tan diferente fue este Mundial de 48 selecciones comparado con los anteriores? Armé este proyecto para responder eso con datos, no con opiniones.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Plotly.js](https://img.shields.io/badge/Plotly.js-3.x-3F4F75?logo=plotly&logoColor=white)

[![CI](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml)
[![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A580%25-green)](#tests)
[![License: MIT](https://img.shields.io/badge/License-Mit-yellow.svg)](LICENSE)

---

## Las preguntas que me hice

Todo empezó con cosas que quería saber y no encontraba fáciles de responder:

1. **¿Cómo se comparan los Mundiales?** Quería ver si el formato de 48 equipos cambió algo real en goles, asistencia o paridad.
2. **¿Qué estadios funcionaron mejor?** No solo capacidad, sino ocupación real y demanda.
3. **¿Los debutantes tienen alguna chance?** Cabo Verde, Curazao, Jordania y Uzbekistán estuvieron ahí, pero ¿les fue bien o mal?

---

## Qué hay aquí

Una base de datos SQLite con todo el torneo: 48 selecciones, 16 estadios, 104 partidos, 285 goles. Después, un montón de consultas SQL que van desde "quién hizo más goles" hasta análisis de clustering y sensibilidad.

### Esquema de la base de datos

```
teams           ← nombre, confederación, ranking FIFA, si es debutante
venues          ← estadio, ciudad, país, capacidad, región
groups          ← grupo A a L
group_standings ← posiciones finales de cada grupo
matches         ← todos los partidos con marcador y asistencia
goals           ← goleador, equipo, si fue autogol
awards          ← Balón de Oro, Bota de Oro, Guante de Oro, Fair Play
```

### Qué hice con los datos

| Qué | Cómo | Para qué |
|-----|------|----------|
| Limpieza e ingesta | `seed_data.py` | Meter los datos reales en SQLite |
| 16 consultas analíticas | `queries.py` + Pandas | Responder las preguntas de arriba |
| Clustering | K-Means | Agrupar estadios por patrones de uso |
| Forecasting | ARIMA | Predecir asistencia en futuros eventos |
| Ranking compuesto | Z-scores | Comparar estadios de forma justa |
| Monte Carlo (N=1000) | Simulación estocástica | Ver qué tan sensibles son los resultados |
| Correlaciones | Pearson | Encontrar relaciones entre variables |

---

## Lo que encontré (en la simulación)

El Mundial 2026 simulado fue, en números, una bestia: **6,8 millones de asistentes** en 104 partidos. **España se coronó campeón venciendo a Argentina 1-0 en la final (tiempo extra)**, y Mbappé se quedó con la Bota de Oro de 10 goles **en este escenario proyectado**.

Lo más interesante: **Europa y Sudamérica dominaron los cuartos de final** con el 75% de los cupos, pese a que el torneo se amplió a 48 selecciones. Los debutantes no tuvieron un mal rendimiento, pero tampoco llegaron lejos.

> **Nota**: Estos resultados son el output de una simulación determinística basada en rankings FIFA y formato del torneo. No son predicciones ni resultados reales.

---

## Visualizaciones

### Bracket interactivo (Observable)

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe src="https://observablehq.com/@alvarosalinaso/worldcup-bracket" title="Bracket — World Cup 2026" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>

### Mapa de asistencia por sede (Datawrapper)

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe src="https://datawrapper.dwcdn.net/HLIEG/" title="Asistencia por Sede — World Cup 2026" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>

---

## Dashboard y reportes

El proyecto tiene tres formas de ver los datos, cada una con su propósito:

- **Reporte HTML estático** (`docs/index.html`) — Abre el archivo y listo, no necesita servidor. Bueno para un vistazo rápido.
- **Dashboard Dash** (`dashboard/app.py`) — Más interactivo, con filtros y tabs. Ideal para explorar.
- **API Flask** (`api/server.py`) — Si quieres construir tu propia visualización encima.

```bash
# Reporte estático
python src/generate_report.py
# Abre docs/index.html

# Dashboard Dash
python dashboard/app.py
# http://localhost:8050

# API Flask
python api/server.py
# http://localhost:5000
```

---

## Cómo correr esto

```bash
git clone https://github.com/alvarosalinaso/worldcup-2026.git
cd worldcup-2026
pip install -r requirements.txt
python src/seed_data.py          # Crea la base de datos
python src/export_visualizations.py  # Genera los archivos de exportación
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=. --cov-report=term-missing
```

La suite tiene cobertura ≥80% y corre contra Python 3.10–3.13 en CI.

### Stack

| Capa | Qué usé | Por qué |
|------|---------|---------|
| Datos | SQLite 3 | Simple, portátil, no necesita servidor |
| Procesamiento | Python + Pandas | El estándar para análisis de datos |
| Visualización | Plotly | Interactiva y se ve bien |
| CI/CD | GitHub Actions | Automatización básica pero efectiva |

---

## Estructura

```
worldcup-2026/
├── src/
│   ├── schema.sql              ← DDL de las 7 tablas
│   ├── seed_data.py            ← Donde se meten los datos
│   ├── queries.py              ← Las 16 consultas analíticas
│   ├── generate_report.py      ← Genera el HTML estático
│   ├── generate_tables.py      ← Tabla ejecutiva con great_tables
│   ├── clustering_analysis.py  ← K-Means
│   ├── forecasting.py          ← ARIMA
│   ├── ranking_analysis.py     ← Z-scores
│   ├── optimization_analysis.py ← Capacidad vs demanda
│   ├── sensitivity_analysis.py ← Monte Carlo
│   └── statistical_tests.py    ← Correlaciones
├── dashboard/
│   └── app.py                  ← Dashboard Dash
├── api/
│   ├── server.py               ← API Flask
│   └── static/index.html       ← Frontend
├── data/
│   ├── worldcup.db             ← Base de datos principal
│   └── historical.db           ← Datos de 2014, 2018, 2022
├── docs/
│   └── index.html              ← Reporte estático
├── tests/
│   └── test_queries.py         ← Suite de tests
└── requirements.txt
```

---

## Datos que incluye

- 48 selecciones con confederación y ranking FIFA
- 16 estadios en USA, México y Canadá
- 12 grupos (A a L) con posiciones
- 104 partidos con marcador, asistencia y si hubo tiempo extra/penales
- 285 goles con goleador y equipo
- Datos históricos de los Mundiales 2014, 2018 y 2022

---

## Proyectos relacionados

- [Manchester United Analysis](https://github.com/alvarosalinaso/manchester-united-analisis) — Análisis del rendimiento del United 2014-2024
- [Passing Network Analysis](https://github.com/alvarosalinaso/united-passing-efficiency-24-25) — Red de pases y eficiencia del mediocampo
- [Portfolio Web](https://github.com/alvarosalinaso/portfolio-web) — Mi portafolio personal

---

**Álvaro Salinas** — Proyecto personal de análisis de datos deportivos
