# FIFA World Cup 2026 — Interactive Dashboard

Dashboard interactivo del Mundial FIFA 2026 construido con **Python, SQLite, Plotly.js y Vite**.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Plotly.js](https://img.shields.io/badge/Plotly.js-3.x-3F4F75?logo=plotly&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white)

[![CI](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml)
[![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A580%25-green)](#tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Contiene datos reales del torneo (España campeón, Mbappé máximo goleador con 10 goles, récord de asistencia de 6.8M).

## Índice

1. [Stack](#-stack)
2. [Funcionalidades](#-funcionalidades)
3. [Arquitectura](#-arquitectura)
4. [Cómo ejecutar](#-cómo-ejecutar)
5. [Tests](#-tests)
6. [Estructura del proyecto](#-estructura-del-proyecto)
7. [Datos incluidos](#-datos-incluidos)

## Stack

| Capa | Tecnología |
|------|-----------|
| Data | SQLite (normalizado, 7 tablas con FK) |
| Backend | Python + Pandas |
| Visualización | **Plotly.js** (frontend), Plotly Express (Python) |
| Frontend | Vite + Vanilla JS (Portfolio Web) |

## Funcionalidades

- **Tournament Overview** — métricas clave, medallero, awards, mapa de las 16 sedes
- **Group Stage** — tabla de los 12 grupos con indicador de clasificación
- **Knockout Stage** — bracket visual + lista detallada + goles por ronda
- **Top Scorers** — ranking dinámico + Golden Boot + distribución por confederación y ronda
- **Venue Analysis** — asistencia por estadio, % de ocupación, mapa interactivo
- **Team Performance** — tabla completa, scatter GF vs GA, goal difference, timeline de partidos
- **Champion Path** — el camino de España al título con stats
- **Surprises & Debutants** — rendimiento de debutantes (Cape Verde, Curaçao, Jordan, Uzbekistán), ranking completo de 48 equipos, relación FIFA Rank vs rendimiento

## Arquitectura

```
src/
├── schema.sql      # Esquema normalizado (7 tablas + FK)
├── seed_data.py    # Población con datos reales del torneo
├── queries.py      # 16 queries analíticas con Pandas (conexión gestionada)
└── export_json.py  # Exporta datos a portfolio-web/public/data/
```

El acceso a datos está separado de la UI: `queries.py` encapsula las consultas SQL y cierra las conexiones mediante un context manager, mientras que `export_json.py` serializa DataFrames para consumo en Portfolio Web (Plotly.js).

## Cómo ejecutar

```bash
pip install -r requirements.txt
python src/seed_data.py
python src/export_json.py
```

> La base de datos se crea automáticamente en `data/worldcup.db` si no existe. También puedes apuntar a otra ruta con la variable de entorno `WC2026_DB`.

## Ver Dashboard Interactivo

**[https://alvarosalinaso.github.io/portfolio-web/](https://alvarosalinaso.github.io/portfolio-web/)** → Tab **"🌍 World Cup 2026 Analysis"** (pendiente de integración completa)

## Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=. --cov-report=term-missing
```

La suite construye una base SQLite **temporal y aislada** por test (vía `seed_data`) y valida las 16 consultas analíticas: ranking de grupos, bracket, goleadores (Mbappé primero), asistencia, ocupación de estadios, camino del campeón, debutantes y filtros combinados. El CI exige **≥80% de cobertura** (`--cov-fail-under`).

## Estructura del proyecto

```
worldcup-2026/
├── src/
│   ├── schema.sql        # Esquema de base de datos (7 tablas)
│   ├── seed_data.py      # Población con datos reales del torneo
│   ├── queries.py        # 16 queries analíticas con Pandas
│   └── export_json.py    # Exporta JSON para Portfolio Web
├── data/
│   └── worldcup.db       # Base de datos SQLite (autogenerada)
├── tests/
│   └── test_queries.py   # Cobertura de seed_data y queries
├── .github/workflows/ci.yml  # CI: ruff + pytest (3.9–3.13)
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Datos incluidos

- 48 equipos con confederación, ranking FIFA, indicador de debut
- 16 sedes con ciudad, país, capacidad, región
- 12 grupos con posiciones, puntos, diferencia de gol
- 104 partidos con marcador, sede, asistencia
- 285 goles registrados con goleador y equipo
- Awards: Golden Ball, Golden Boot, Golden Glove, Fair Play

**Autor:** Álvaro Salinas — Proyecto de portafolio como Data Analyst