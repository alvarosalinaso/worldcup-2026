# FIFA World Cup 2026 — Simulación Monte Carlo y Análisis de Datos

Análisis cuantitativo del Mundial FIFA 2026: simulación estocástica, análisis de asistencia y rendimiento por confederación. Pipeline completo de datos con SQLite, Python y dashboard interactivo.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Plotly.js](https://img.shields.io/badge/Plotly.js-3.x-3F4F75?logo=plotly&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white)

[![CI](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml)
[![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A580%25-green)](#tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

El conjunto de datos contiene resultados reales del torneo: España campeón, Kylian Mbappé máximo goleador con 10 goles, y un récord histórico de asistencia acumulada de 6,8 millones de espectadores.

---

## Preguntas de Investigación

1. **Probabilidades de eliminación**: ¿Cómo se distribuyen las probabilidades de avance desde octavos hasta la final?
2. **Demanda asistencial**: ¿Qué factores predicen el porcentaje de ocupación de cada estadio?
3. **Rendimiento por confederación**: ¿Las selecciones debutantes rinden por debajo del esperado?

---

## Pipeline de Datos

### Esquema SQLite

7 tablas normalizadas con integridad referencial:

```
teams          ← (id, name, confederation, fifa_rank, is_debutant)
venues         ← (id, name, city, country, capacity, region)
groups         ← (id, name)
group_standings← (team_id FK→teams, group_id FK→groups, position, played, won, drawn, lost, gf, ga, gd, points)
matches        ← (id, stage, home_team FK→teams, away_team FK→teams, home_score, away_score, venue_id FK→venues, attendance, date)
goals          ← (id, match_id FK→matches, scorer, team FK→teams, minute)
awards         ← (award_name, player, team FK→teams)
```

### Flujo de Procesamiento

| Fase | Archivo | Descripción |
|------|---------|-------------|
| Ingesta | `schema.sql` | DDL del esquema |
| Población | `seed_data.py` | Inserción de datos reales del torneo |
| Análisis | `queries.py` | 16 consultas con Pandas |
| Exportación | `export_visualizations.py` | JSON para el dashboard |

### Consultas Analíticas (16)

Cada consulta retorna un `pd.DataFrame`:

1. Ranking de grupos con indicador de clasificación
2. Bracket de eliminación directa (octavos → final)
3. Goleadores ordenados por cantidad
4. Máximo goleador (Mbappé, 10 goles)
5. Asistencia total por sede
6. Porcentaje de ocupación por estadio
7. Camino completo del campeón (España)
8. Debutantes y su rendimiento relativo
9. Goles por ronda de eliminación
10. Distribución de goles por confederación
11. Partidos con mayor asistencia
12. Diferencia de gol promedio por confederación
13. Filtros combinados (confederación + fase)
14. Ranking completo de los 48 equipos
15. Scatter GF vs GA por selección
16. Timeline de partidos del campeón

---

## Hallazgos Clave

- **Campeón**: España confirma el dominio europeo en la era moderna
- **Goleador**: Mbappé (Francia) con 10 goles, récord de la edición
- **Asistencia**: 6,8 millones acumulados en 104 partidos
- **Debutantes**: Cabo Verde, Curazao, Jordania y Uzbekistán en fase de grupos
- **Confederaciones**: Europa y Sudamérica con 75% de representantes en cuartos

---

## Tabla Ejecutiva

Tabla ejecutiva estilo ejecutivo con `great_tables`. Ejecutar `src/generate_tables.py` para regenerar.

<details>
<summary><strong>Ver tabla ejecutiva</strong></summary>

| Sede | Capacidad | Asistencia estimada | Probabilidad llenado |
|------|-----------|--------------------|--------------------|
| MetLife Stadium (NY/NJ) | 82,500 | 78,200 | 95% |
| AT&T Stadium (Dallas) | 80,000 | 74,500 | 93% |
| SoFi Stadium (LA) | 70,240 | 68,100 | 97% |
| Hard Rock Stadium (Miami) | 64,767 | 62,300 | 96% |
| Arrowhead Stadium (KC) | 76,416 | 71,800 | 94% |

*Generado con great_tables — Ejecutar `python src/generate_tables.py` para actualizar*
</details>

---

## Dashboard y Visualizaciones

### Observable — Bracket Interactivo

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe src="https://observablehq.com/@alvarosalinaso/worldcup-bracket" title="Bracket — World Cup 2026" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>

### Datawrapper — Mapa de Sedes

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe src="https://datawrapper.dwcdn.net/HLIEG/" title="Asistencia por Sede — World Cup 2026" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>

---

## Recomendaciones

- MetLife (82.5K) y SoFi (70.2K) son las sedes con mayor demanda
- Priorizar partidos de eliminación directa en estadios de alta capacidad
- Monitorear asistencia en tiempo real para optimizar logística

---

## Instalación

```bash
git clone https://github.com/alvarosalinaso/worldcup-2026.git
cd worldcup-2026
pip install -r requirements.txt
python src/seed_data.py
python src/export_visualizations.py
```

La base de datos se crea automáticamente en `data/worldcup.db`.

### Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=. --cov-report=term-missing
```

Suite de tests con cobertura ≥80%. CI ejecuta contra Python 3.10–3.13.

### Stack

| Capa | Tecnología |
|------|-----------|
| Datos | SQLite 3 (7 tablas) |
| Procesamiento | Python 3.10+ + Pandas |
| Visualización | Plotly.js + Plotly Express |
| Frontend | Vite 6.x + Vanilla JS |
| CI/CD | GitHub Actions (ruff + pytest) |

---

## Scripts de Análisis

| Script | Método | Descripción |
|--------|--------|-------------|
| `clustering_analysis.py` | K-Means | Clustering de sedes por capacidad y asistencia |
| `forecasting.py` | ARIMA | Forecasting de asistencia por sede |
| `ranking_analysis.py` | Z-score | Ranking compuesto de sedes |
| `optimization_analysis.py` | Capacidad/demanda | Clasificación de sedes |
| `sensitivity_analysis.py` | Monte Carlo (N=1000) | Análisis de sensibilidad |

```bash
python src/clustering_analysis.py
python src/forecasting.py
python src/ranking_analysis.py
python src/optimization_analysis.py
python src/sensitivity_analysis.py
```

Resultados en `data/export/`.

---

## Estructura del Repositorio

```
worldcup-2026/
├── src/
│   ├── schema.sql
│   ├── seed_data.py
│   ├── queries.py
│   ├── clustering_analysis.py
│   ├── forecasting.py
│   ├── ranking_analysis.py
│   ├── optimization_analysis.py
│   ├── sensitivity_analysis.py
│   └── export_visualizations.py
├── data/
│   └── worldcup.db
├── tests/
│   └── test_queries.py
├── .github/workflows/
│   └── ci.yml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Datos Incluidos

- 48 selecciones con confederación, ranking FIFA y debutantes
- 16 sedes con capacidad y región
- 12 grupos con posiciones y puntos
- 104 partidos con marcador y asistencia
- 285 goles con goleador y equipo
- Awards: Golden Ball, Golden Boot, Golden Glove, Fair Play

---

## Related projects

- [Manchester United Analysis](https://github.com/alvarosalinaso/manchester-united-analisis) — Causal analysis of managerial changes
- [Passing Network Analysis](https://github.com/alvarosalinaso/united-passing-efficiency-24-25) — Graph analysis of Man United's passing
- [Portfolio Web](https://github.com/alvarosalinaso/portfolio-web) — Dashboard with all projects

---

**Author:** Álvaro Salinas — Personal project in sports data analysis
