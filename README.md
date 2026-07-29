#  FIFA World Cup 2026 — Interactive Dashboard

Dashboard interactivo del Mundial FIFA 2026 construido con **Python, SQLite, Streamlit y Plotly**.

Contiene datos reales del torneo (España campeón, Mbappé máximo goleador con 10 goles, récord de asistencia de 6.8M).

##  Stack

| Capa | Tecnología |
|------|-----------|
| Data | SQLite (normalizado, 6 tablas con FK) |
| Backend | Python + Pandas |
| Visualización | Plotly Express |
| Dashboard | Streamlit |

##  Funcionalidades

- **Tournament Overview** — métricas clave, medallero, awards, mapa de las 16 sedes
- **Group Stage** — tabla de los 12 grupos con indicador de clasificación
- **Knockout Stage** — bracket visual + lista detallada + goles por ronda
- **Top Scorers** — ranking dinámico + Golden Boot + distribución por confederación y ronda
- **Venue Analysis** — asistencia por estadio, % de ocupación, mapa interactivo
- **Team Performance** — tabla completa, scatter GF vs GA, goal difference, timeline de partidos
- **Champion Path** — el camino de España al título con stats
- **Surprises & Debutants** — rendimiento de debutantes (Cape Verde, Curaçao, Jordan, Uzbekistán), ranking completo de 48 equipos, relación FIFA Rank vs rendimiento

##  Cómo ejecutar

```bash
pip install -r requirements.txt
python src/seed_data.py
streamlit run src/app.py
```

##  Estructura del proyecto

```
worldcup-2026/
├── src/
│   ├── schema.sql        # Esquema de base de datos (6 tablas)
│   ├── seed_data.py      # Población con datos reales del torneo
│   ├── queries.py        # 17 queries analíticas con Pandas
│   └── app.py            # Dashboard Streamlit (9 secciones)
├── data/
│   └── worldcup.db       # Base de datos SQLite
├── requirements.txt
└── README.md
```

##  Datos incluidos

- 48 equipos con confederación, ranking FIFA, indicador de debut
- 16 sedes con ciudad, país, capacidad, región
- 12 grupos con posiciones, puntos, diferencia de gol
- 104 partidos con marcador, sede, asistencia
- 285 goles registrados con goleador y equipo
- Awards: Golden Ball, Golden Boot, Golden Glove, Fair Play

## 

**Autor:** Álvaro Salinas — Proyecto de portafolio como Data Analyst
