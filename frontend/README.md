## Global Defense Signals Explorer - Frontend

Quick React + Vite app that renders a world choropleth map and shows SIPRI-derived signals on hover.

Prereqs:
- Node 18+
- Backend running at http://127.0.0.1:8000 (FastAPI from this repo)

Install and run:
```bash
cd frontend
npm install
npm run dev
```

Open:
- http://127.0.0.1:5173

How it works:
- The dropdown selects the map metric (cagr_5y_pct, yoy_latest_pct, etc.)
- The map colors countries by `/countries/map-metric?metric=<metric>`
- On hover, the app fetches `/countries/{id}/signals` for the hovered ISO3 country (cached)
- Tooltip shows: latest year, spending, YoY, 5Y CAGR, %GDP, share global, rank and key flags

Configuration:
- Vite dev server proxies `/countries` and `/health` to `http://127.0.0.1:8000`
- Adjust `vite.config.ts` if your backend host/port differs
