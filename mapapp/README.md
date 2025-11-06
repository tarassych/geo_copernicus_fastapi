# Copernicus DEM Coverage Map

An interactive Next.js application displaying the Copernicus DEM tile coverage area with Ukraine country borders.

## Features

- 🗺️ **Interactive Map** using Leaflet (no API keys required)
- 🇺🇦 **Ukraine Borders** displayed with national colors
- 📊 **DEM Coverage Visualization** showing 97/108 tiles (89.8% coverage)
- 🎯 **Boundary Markers** for both DEM area and map limits (+50km buffer)
- 📱 **Responsive Design** with Tailwind CSS
- ⚡ **Static Export** for easy deployment

## Map Boundaries

- **DEM Coverage Area**: 46.06°N - 51.76°N, 21.11°E - 38.74°E
- **Map View Area**: DEM area + 50km buffer on all sides
- **Missing Coverage**: Northern strip (51-52°N) - 11 tiles unavailable from OpenTopography

## Technology Stack

- **Next.js 15** with App Router
- **React 19**
- **TypeScript**
- **Leaflet** & **React-Leaflet** for mapping
- **Tailwind CSS** for styling
- **OpenStreetMap** tiles (no API key required)

## Getting Started

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the map.

### Build for Production

```bash
npm run build
```

This creates a static export in the `out/` directory.

### Preview Production Build

```bash
npm run build
npx serve@latest out
```

## Map Legend

- **Blue Line**: Ukraine border (from GeoJSON data)
- **Green Dashed Box**: DEM coverage area (89.8% complete)
- **Red Dashed Box**: Map boundary with 50km buffer

## Deployment

The application is configured for static export and can be deployed to:

- GitHub Pages
- Netlify
- Vercel
- Any static hosting service

Simply upload the contents of the `out/` directory after building.

## Data Sources

- **Map Tiles**: © OpenStreetMap contributors
- **DEM Data**: Copernicus Global DEM via OpenTopography
- **Ukraine Borders**: Simplified GeoJSON polygon

## License

This project was created for visualizing Copernicus DEM data coverage.
