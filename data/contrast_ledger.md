# Ledger de contraste FIFA (revisión 2026-10)

Contraste de los resultados **reales** de `data/worldcup_real.db` (openfootball,
CC0, commit upstream `4b8415d`) contra la fuente **oficial** FIFA: la API
pública que alimenta fifa.com (`api.fifa.com`, competición 17,
temporada 285023 = "FIFA World Cup 2026"). www.fifa.com es una SPA sin
HTML verificable por HTTP simple, por eso se usa su API oficial.

URL FIFA: <https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&language=en&count=500>
Fecha de acceso: 2026-10-19
Regenerar: `python src/verify_against_fifa.py`

| Dato verificado | openfootball (repo) | FIFA (oficial) | URL FIFA | Fecha de acceso | ¿Coincide? |
|---|---|---|---|---|---|
| Final (match 104) | Spain 1-0 Argentina (2026-07-19, New York/New Jersey Stadium) | Spain 1-0 Argentina (id 400021543, asistencia 80663) | <https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&language=en&count=500> | 2026-10-19 | Sí |
| 3er lugar (match 103) | France 4-6 England (2026-07-18, Miami Stadium) | France 4-6 England (id 400021542, asistencia 64478) | <https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&language=en&count=500> | 2026-10-19 | Sí |
| Marcadores de eliminatorias (matches 73-104) | 32 partidos | idénticos | <https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&language=en&count=500> | 2026-10-19 | Sí |
| Totales del torneo | 104 partidos, 308 goles | 104 partidos, 308 goles | <https://api.fifa.com/api/v3/calendar/matches?idCompetition=17&idSeason=285023&language=en&count=500> | 2026-10-19 | Sí |

Notas:

- Sin discrepancias de marcador: no hizo falta corregir datos del repo.
- Diferencias solo de **nombres** entre fuentes (alias): Côte d'Ivoire=Ivory
  Coast, Congo DR=DR Congo, Bosnia and Herzegovina=Bosnia & Herzegovina,
  Cabo Verde=Cape Verde, United States=USA. El repo conserva los nombres
  openfootball.

## Discrepancias detectadas por el script

- (ninguna)
