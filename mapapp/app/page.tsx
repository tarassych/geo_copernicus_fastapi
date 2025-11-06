'use client';

import dynamic from 'next/dynamic';
import cachedTiles from '../data/cached-tiles.json';

// Dynamically import Map component with no SSR to avoid window undefined error
const Map = dynamic(() => import('../components/Map'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading map...</p>
      </div>
    </div>
  ),
});

export default function Home() {
  // Original DEM area coordinates
  const demMinLat = 46.062027;
  const demMaxLat = 51.757555;
  const demMinLon = 21.106558;
  const demMaxLon = 38.736462;

  // Add 50km buffer (approximately 0.45 degrees at these latitudes)
  const bufferDegrees = 0.5; // ~55km buffer for safety
  
  const minLat = demMinLat - bufferDegrees;
  const maxLat = demMaxLat + bufferDegrees;
  const minLon = demMinLon - bufferDegrees;
  const maxLon = demMaxLon + bufferDegrees;

  // Map bounds with 50km buffer
  const bounds: [[number, number], [number, number]] = [
    [minLat, minLon],
    [maxLat, maxLon]
  ];

  // Center of the map
  const center: [number, number] = [
    (demMinLat + demMaxLat) / 2,
    (demMinLon + demMaxLon) / 2
  ];

  return (
    <div className="w-full h-screen relative">
      {/* Map Container - Full Screen */}
      <Map 
        center={center} 
        zoom={7} 
        bounds={bounds}
        cachedTiles={cachedTiles}
      />
      
      {/* Legend */}
      <div className="absolute bottom-6 right-6 bg-white rounded-lg shadow-xl p-4 z-[1000] max-w-xs">
        <h3 className="font-bold text-gray-800 mb-3 flex items-center">
          <span className="mr-2">📍</span>
          Map Legend
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex items-center">
            <div className="w-6 h-6 border border-blue-500 mr-3 bg-blue-500 bg-opacity-10"></div>
            <span className="text-gray-700">Cached Tiles ({cachedTiles.length})</span>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-1 border-2 border-green-500 mr-3" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-gray-700">DEM Coverage Area</span>
          </div>
          <div className="flex items-center">
            <div className="w-8 h-1 border-2 border-red-500 mr-3" style={{ borderStyle: 'dashed' }}></div>
            <span className="text-gray-700">Map Boundary (+50km)</span>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            <strong>Coverage:</strong> 97 of 108 tiles<br/>
            <strong>Missing:</strong> 51-52°N band (11 tiles)<br/>
            <strong>Reason:</strong> Data unavailable from OpenTopography
          </p>
        </div>
      </div>
    </div>
  );
}
