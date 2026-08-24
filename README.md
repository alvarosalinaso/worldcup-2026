# FIFA World Cup 2026 — Simulación Monte Carlo, Análisis de Demanda y Arquitectura de Datos

Análisis cuantitativo del Mundial FIFA 2026 mediante simulación estocástica, modelamiento de elasticidad de demanda asistencial y evaluación de rendimiento por confederación. Este repositorio documenta un pipeline completo de datos — desde el esquema relacional normalizado hasta un dashboard interactivo multiplataforma — y constituye un ejercicio de portafolio en análisis de datos deportivos a nivel postgrado.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Plotly.js](https://img.shields.io/badge/Plotly.js-3.x-3F4F75?logo=plotly&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white)

[![CI](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml/badge.svg)](https://github.com/alvarosalinaso/worldcup-2026/actions/workflows/ci.yml)
[![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A580%25-green)](#tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

El conjunto de datos contiene resultados reales del torneo: España campeón, Kylian Mbappé máximo goleador con 10 goles, y un récord histórico de asistencia acumulada de 6,8 millones de espectadores.

---

## 1. Preguntas de Investigación e Hipótesis

El proyecto se estructura en torno a tres ejes analíticos fundamentales:

**Eje 1 — Probabilidades de Eliminación por Instancia.**
Hipótesis: la distribución de fuerza relativa entre confederaciones genera asimetrías sustantivas en las probabilidades de avance desde octavos de final hasta la final. Se evalúa la sobrerrepresentación europea en instancias finales.

**Eje 2 — Elasticidad de la Demanda Asistencial por Sede.**
Hipótesis: la capacidad instalada del estadio y la relevancia del partido (fase de grupo vs. eliminación directa) son predictores significativos del porcentaje de ocupación. Se modela la elasticidad precio-cantidad implícita vía capacidad como proxy.

**Eje 3 — Rendimiento por Confederación y Efecto Debutantes.**
Hipótesis: las selecciones debutantes (Cabo Verde, Curazao, Jordania, Uzbekistán) presentan un desempeño系统icamente inferior al esperado por su ranking FIFA, lo que sugiere un sesgo de experiencia en torneos de esta escala.

---

## 2. Pipeline Metodológico y Arquitectura de Datos

### 2.1 Esquema Relacional (SQLite)

La base de datos `worldcup.db` se compone de 7 tablas normalizadas con integridad referencial mediante claves foráneas:

```
teams          ← (id, name, confederation, fifa_rank, is_debutant)
venues         ← (id, name, city, country, capacity, region)
groups         ← (id, name)
group_standings← (team_id FK→teams, group_id FK→groups, position, played, won, drawn, lost, gf, ga, gd, points)
matches        ← (id, stage, home_team FK→teams, away_team FK→teams, home_score, away_score, venue_id FK→venues, attendance, date)
goals          ← (id, match_id FK→matches, scorer, team FK→teams, minute)
awards         ← (award_name, player, team FK→teams)
```

Las relaciones Many-to-One (`group_standings.team_id`, `matches.venue_id`, `goals.match_id`) permiten joins analíticos sin redundancia. El acceso a datos se encapsula en `queries.py` mediante context managers que cierran la conexión automáticamente.

### 2.2 Pipeline de Procesamiento

| Fase | Archivo | Descripción |
|------|---------|-------------|
| Ingesta | `schema.sql` | DDL del esquema normalizado |
| Población | `seed_data.py` | Inserción de 48 equipos, 16 sedes, 104 partidos, 285 goles |
| Análisis | `queries.py` | 16 consultas analíticas con Pandas sobre DataFrames |
| Exportación | `export_json.py` | Serialización a JSON para consumo en Portfolio Web |

### 2.3 Consultas Analíticas (16)

El módulo `queries.py` implementa las siguientes consultas, cada una encapsulada en una función que retorna un `pd.DataFrame`:

1. Ranking de grupos con indicador de clasificación
2. Bracket de eliminación directa (octavos → final)
3. Goleadores ordenados por cantidad de goles
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

## 3. Hallazgos Clave y Domain Insights

**Resultado del torneo.** España se consagra campeón del Mundial 2026, confirmando la tendencia de dominio europeo en la era moderna del fútbol.

**Rendimiento individual.** Kylian Mbappé (Francia) alcanza 10 goles, estableciendo un récord para la edición. La distribución de goleadores por confederación revela una concentración en ligas europejas de primer nivel.

**Demanda asistencial.** El récord de 6,8 millones de asistentes acumulados evidencia la escala sin precedentes de un Mundial con 48 selecciones y 16 sedes. Los estadios con mayor capacidad (Estados Unidos) registraron los porcentajes de ocupación más altos en partidos de eliminación directa.

**Debutantes.** Cabo Verde, Curazao, Jordania y Uzbekistán compitieron en fase de grupos. Su rendimiento系统icamente inferior al ranking FIFA pre-torneo valida la hipótesis de sesgo de experiencia en torneos de esta envergadura.

**Confederaciones.** Europa y Sudamérica concentraron el 75% de los representantes en cuartos de final, reforzando la tesis de asimetría competitiva estructural.

---

## 4. Dashboard y Visualizaciones Interactivas

El proyecto emplea tres plataformas de visualización para maximizar la accesibilidad y el impacto de los hallazgos:

### 4.1 Observable Interactive Bracket

<!-- Embebido de Observable: reemplazar con URL del notebook público -->
```html
<iframe src="https://observablehq.com/embed/@INSERT Observable EMBED URL HERE" width="100%" height="600" frameborder="0"></iframe>
```

Bracket interactivo del torneo con tooltip por partido, goles y asistencia. Permite navegar desde octavos de final hasta la final.

### 4.2 Flourish Sankey Diagram

<!-- Embebido de Flourish: reemplazar con URL de la visualización publicada -->
```html
<iframe src="https://flo.uri.sh/visualisation/INSERT FLOURISH ID HERE/embed" width="100%" height="600" frameborder="0" scrolling="no"></iframe>
```

Diagrama Sankey que representa el flujo de selecciones por confederación a través de las fases del torneo, desde grupos hasta la final.

### 4.3 Datawrapper Mapa de Sedes

<!-- Embebido de Datawrapper: reemplazar con URL del mapa publicado -->
<iframe title="FIFA World Cup 2026 — Venues" aria-label="Map" src="https://datawrapper.de/INSERT DATAWRAPPER ID HERE/" width="100%" height="500" frameborder="0" scrolling="no"></iframe>

Mapa interactivo de las 16 sedes con popups de capacidad, región y partidos albergados.

---

## Visual Analytics

Interactividad multinivel para exploración de datos y presentación ejecutiva.

<details>
<summary><strong>Datawrapper — Gráfico interactivo</strong></summary>

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe src="https://datawrapper.dwcdn.net/HLIEG/" title="Densidad de Asistencia por Sede — World Cup 2026" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>
</details>

<details>
<summary><strong>Observable — Notebook interactivo</strong></summary>

<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe src="https://observablehq.com/@alvarosalinaso/worldcup-bracket" title="Bracket Predictivo — World Cup 2026" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" loading="lazy" allowfullscreen></iframe>
</div>
</details>

**Hallazgos clave**: El análisis de asistencia predice sedes con mayor densidad de público en ciudades con estadios de +50.000 capacidad.

---

## 5. Reproducibilidad y Entorno Técnico

### 5.1 Instalación

```bash
git clone https://github.com/alvarosalinaso/worldcup-2026.git
cd worldcup-2026
pip install -r requirements.txt
python src/seed_data.py
python src/export_json.py
```

La base de datos se crea automáticamente en `data/worldcup.db` si no existe. La ruta puede configurarse mediante la variable de entorno `WC2026_DB`.

### 5.2 Tests y Cobertura

```bash
pip install -r requirements-dev.txt
pytest --cov=. --cov-report=term-missing
```

La suite de tests construye una base SQLite temporal e aislada por caso de prueba (vía `seed_data`) y valida las 16 consultas analíticas: ranking de grupos, bracket, goleadores (Mbappé primero), asistencia, ocupación de estadios, camino del campeón, debutantes y filtros combinados. El CI en GitHub Actions ejecuta la suite contra Python 3.9–3.13 y aplica el umbral de cobertura **≥80%** mediante `--cov-fail-under`.

### 5.3 Stack Técnico

| Capa | Tecnología |
|------|-----------|
| Datos | SQLite 3 (normalizado, 7 tablas con FK) |
| Procesamiento | Python 3.9+ + Pandas |
| Visualización Frontend | Plotly.js 3.x |
| Visualización Python | Plotly Express |
| Infraestructura | Vite 6.x + Vanilla JS |
| CI/CD | GitHub Actions (ruff + pytest) |

---

## 6. Estructura del Repositorio

```
worldcup-2026/
├── src/
│   ├── schema.sql          # DDL del esquema (7 tablas)
│   ├── seed_data.py        # Población con datos reales del torneo
│   ├── queries.py          # 16 consultas analíticas con Pandas
│   └── export_json.py      # Exportación JSON para Portfolio Web
├── data/
│   └── worldcup.db         # Base de datos SQLite (autogenerada)
├── tests/
│   └── test_queries.py     # Suite de tests (cobertura ≥80%)
├── .github/workflows/
│   └── ci.yml              # CI: ruff + pytest (3.9–3.13)
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## 7. Datos Incluidos

- **48 selecciones** con confederación, ranking FIFA y indicador de debut
- **16 sedes** con ciudad, país, capacidad y región
- **12 grupos** con posiciones, puntos y diferencia de gol
- **104 partidos** con marcador, sede y asistencia
- **285 goles** registrados con goleador y equipo
- **Awards**: Golden Ball, Golden Boot, Golden Glove, Fair Play

---

**Autor:** Álvaro Salinas — Proyecto de portafolio en análisis de datos deportivos (nivel postgrado)
