# Embed Snippets - FIFA World Cup 2026

Responsive HTML snippets for embedding interactive visualizations.

---

## 1. Datawrapper Map - Venue Attendance

```html
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe
    title="World Cup 2026 – Venue Attendance"
    src="https://datawrapper.dwcdn.net/ATTACH_YOUR_CHART_ID/"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    allowfullscreen
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>
```

> **Setup:** Upload `data/export/dw_asistencia_sedes.csv` to
> [Datawrapper](https://www.datawrapper.de/) and replace `ATTACH_YOUR_CHART_ID`
> with the published chart ID.

---

## 2. Flourish Sankey - Confederation Advancement

```html
<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
  <iframe
    title="World Cup 2026 – Confederation Advancement"
    src="https://flo.uri.sh/story/ATTACH_YOUR_STORY_ID/embed"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    allowfullscreen
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>
```

> **Setup:** Upload `data/export/flourish_sankey_avance.csv` to
> [Flourish](https://flourish.studio/) as a Sankey diagram and replace
> `ATTACH_YOUR_STORY_ID` with the published story ID.

---

## 3. Observable Interactive Bracket

```html
<div style="position:relative;padding-bottom:75%;height:0;overflow:hidden;max-width:100%;">
  <iframe
    title="World Cup 2026 – Interactive Bracket"
    src="https://observablehq.com/embed/ATTACH_YOUR_NOTEBOOK_ID?cells=chart"
    style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
    loading="lazy"
    allowfullscreen
    referrerpolicy="no-referrer-when-downgrade">
  </iframe>
</div>
```

> **Setup:** Publish an Observable notebook using `data/export/observable_bracket.csv`
> and replace `ATTACH_YOUR_NOTEBOOK_ID` with the published notebook ID.

---

## Quick Start

1. Run the export script:
   ```bash
   python src/export_visualizations.py
   ```
2. CSV files are generated in `data/export/`.
3. Upload each CSV to the corresponding platform.
4. Replace the placeholder IDs in the snippets above.
5. Paste the HTML into your page or README.

## Responsive Notes

- All embeds use the `padding-bottom` trick for aspect-ratio-responsive sizing.
- `max-width: 100%` prevents horizontal overflow on narrow screens.
- `loading="lazy"` defers loading until the embed scrolls into view.
- `allowfullscreen` enables fullscreen toggle on the embedded content.
