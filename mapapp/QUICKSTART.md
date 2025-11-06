# Quick Start Guide

## 🚀 Running the Application

### Development Mode
```bash
cd mapapp
npm run dev
```
Then open http://localhost:3000

### Production Build (Static Export)
```bash
cd mapapp
npm run build
```

The static site will be generated in the `out/` directory.

### Preview Static Build
```bash
cd mapapp
npx serve@latest out
```

## 📁 Project Structure

```
mapapp/
├── app/
│   ├── page.tsx          # Main page with map
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   └── Map.tsx           # Leaflet map component
├── data/
│   └── ukraine-borders.json  # Ukraine GeoJSON data
├── out/                  # Static export output (after build)
├── next.config.ts        # Next.js config (static export enabled)
└── package.json
```

## 🗺️ Map Features

### Displayed Elements
1. **Ukraine Borders** - Blue outline with yellow fill (national colors)
2. **DEM Coverage Area** - Green dashed rectangle (46.06°N - 51.76°N)
3. **Map Boundaries** - Red dashed rectangle (DEM area + 50km buffer)
4. **Interactive Legend** - Bottom-right corner with coverage stats

### Map Controls
- **Zoom**: Mouse wheel or +/- buttons
- **Pan**: Click and drag
- **Popups**: Click on the green DEM box for coverage info

## 📊 Coverage Information

- **Total Expected Tiles**: 108
- **Downloaded Tiles**: 97 (89.8%)
- **Missing Tiles**: 11 (northern strip 51-52°N)
- **Reason**: Data not available from OpenTopography API

## 🎨 Color Legend

- 🔵 **Blue**: Ukraine border
- 🟢 **Green dashed**: DEM coverage area
- 🔴 **Red dashed**: Map boundary (+50km)
- 💛 **Yellow fill**: Ukraine territory (subtle)

## 🌐 No API Keys Required!

This application uses:
- **OpenStreetMap** tiles (free, no key needed)
- **Leaflet** (open-source mapping library)
- All resources are open and free to use

## 📦 Deployment

The `out/` directory contains a complete static website:
- Upload to any static hosting (GitHub Pages, Netlify, Vercel, S3, etc.)
- No server required
- Works offline after initial load

## 🛠️ Technologies

- Next.js 15 (App Router)
- React 19
- TypeScript
- Leaflet & React-Leaflet
- Tailwind CSS
- OpenStreetMap tiles

