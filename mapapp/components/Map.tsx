'use client';

import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in Leaflet with Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapProps {
  center: [number, number];
  zoom: number;
  bounds: [[number, number], [number, number]];
  cachedTiles: string[];
}

// Parse tile name like "N50E026" to get bounds [[50, 26], [51, 27]]
function parseTileName(tileName: string): [[number, number], [number, number]] {
  const latMatch = tileName.match(/([NS])(\d{2})/);
  const lonMatch = tileName.match(/([EW])(\d{3})/);
  
  if (!latMatch || !lonMatch) {
    throw new Error(`Invalid tile name: ${tileName}`);
  }
  
  const latDir = latMatch[1];
  const latNum = parseInt(latMatch[2], 10);
  const lonDir = lonMatch[1];
  const lonNum = parseInt(lonMatch[2], 10);
  
  const lat = latDir === 'N' ? latNum : -latNum;
  const lon = lonDir === 'E' ? lonNum : -lonNum;
  
  return [[lat, lon], [lat + 1, lon + 1]];
}

export default function Map({ center, zoom, bounds, cachedTiles }: MapProps) {
  useEffect(() => {
    // Initialize map only on client side
    const map = L.map('map', {
      center: center,
      zoom: zoom,
      maxBounds: bounds,
      maxBoundsViscosity: 0.5,
    });

    // Add OpenStreetMap tile layer (no API key required)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    // Add boundary box rectangle
    const boundaryRect = L.rectangle(bounds, {
      color: '#ff0000',
      weight: 2,
      fillOpacity: 0,
      dashArray: '5, 10',
    }).addTo(map);

    // Add markers for the corners of the DEM coverage area
    const demBounds: [[number, number], [number, number]] = [
      [46.062027, 21.106558],
      [51.757555, 38.736462]
    ];
    
    const demRect = L.rectangle(demBounds, {
      color: '#00ff00',
      weight: 2,
      fillOpacity: 0,
      dashArray: '5, 5',
    }).addTo(map);
    
    demRect.bindPopup('DEM Coverage Area (89.8% complete)');

    // Add cached tile boundaries
    cachedTiles.forEach((tileName) => {
      try {
        const tileBounds = parseTileName(tileName);
        const tileRect = L.rectangle(tileBounds, {
          color: '#0066ff',
          weight: 1,
          opacity: 0.6,
          fillColor: '#0066ff',
          fillOpacity: 0.1,
        }).addTo(map);
        
        tileRect.bindPopup(`Tile: ${tileName}<br/>Cached: ✓`);
        
        // Add tile name label in the center of the tile
        const centerLat = (tileBounds[0][0] + tileBounds[1][0]) / 2;
        const centerLon = (tileBounds[0][1] + tileBounds[1][1]) / 2;
        
        const label = L.marker([centerLat, centerLon], {
          icon: L.divIcon({
            className: 'tile-label',
            html: `<div style="color: #66b3ff; font-size: 11px; font-weight: 600; text-shadow: 0 0 3px white, 0 0 3px white, 0 0 3px white; white-space: nowrap;">${tileName}</div>`,
            iconSize: [60, 20],
            iconAnchor: [30, 10],
          }),
          interactive: false,
        }).addTo(map);
      } catch (error) {
        console.error(`Error parsing tile ${tileName}:`, error);
      }
    });

    // Fit map to boundary box
    map.fitBounds(bounds);

    // Cleanup on unmount
    return () => {
      map.remove();
    };
  }, [center, zoom, bounds, cachedTiles]);

  return <div id="map" className="w-full h-full" />;
}

