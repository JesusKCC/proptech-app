'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { CentroComercial, LocalComercial } from '../../types';
import { fetchCentrosComerciales, FALLBACK_MALLS } from '../../lib/api';
import { Globe, Layers, MapPin, Building2, RefreshCw } from '../common/Icons';

const ESRI_SATELLITE_URL =
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const ESRI_LABELS_URL =
  'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}';
const ESRI_ATTRIBUTION =
  'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community';

interface PeruSatelliteMapProps {
  onSelectMall?: (mall: CentroComercial) => void;
  selectedMallId?: string;
  className?: string;
  hideCarousel?: boolean;
  searchedLocales?: LocalComercial[];
  searchQuery?: string;
}

export const PeruSatelliteMap: React.FC<PeruSatelliteMapProps> = ({
  onSelectMall,
  selectedMallId,
  className = '',
  hideCarousel = false,
  searchedLocales = [],
  searchQuery = '',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersLayerRef = useRef<any>(null);
  const labelsLayerRef = useRef<any>(null);

  const [malls, setMalls] = useState<CentroComercial[]>(FALLBACK_MALLS);
  const [loading, setLoading] = useState<boolean>(true);
  const [mapReady, setMapReady] = useState<boolean>(false);
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [activeMall, setActiveMall] = useState<CentroComercial | null>(null);

  // 1. Fetch malls
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      try {
        const data = await fetchCentrosComerciales();
        if (isMounted) {
          setMalls(data);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setMalls(FALLBACK_MALLS);
          setLoading(false);
        }
      }
    }
    loadData();

    // Fallback safety timeout: ensure loading state is cleared after at most 1000ms
    const timer = setTimeout(() => {
      if (isMounted) setLoading(false);
    }, 1000);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, []);

  // 2. Load Leaflet script and CSS safely in browser
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Check if Leaflet CSS is already injected
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link');
      link.id = 'leaflet-css';
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    // Check if Leaflet script is already loaded
    if (window.L) {
      setMapReady(true);
      return;
    }

    const existingScript = document.getElementById('leaflet-js');
    if (!existingScript) {
      const script = document.createElement('script');
      script.id = 'leaflet-js';
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.async = true;
      script.onload = () => {
        setMapReady(true);
      };
      document.body.appendChild(script);
    } else {
      existingScript.addEventListener('load', () => setMapReady(true));
      // In case script was already loaded in browser cache
      if (window.L) {
        setMapReady(true);
      }
    }
  }, []);

  // 3. Initialize Map once Leaflet is ready and container exists
  useEffect(() => {
    if (!mapReady || !mapContainerRef.current || mapInstanceRef.current || typeof window === 'undefined') {
      return;
    }

    const L = window.L;
    if (!L) return;

    // Reset container leaflet id if needed to avoid "Map container is already initialized"
    if (mapContainerRef.current && (mapContainerRef.current as any)._leaflet_id) {
      delete (mapContainerRef.current as any)._leaflet_id;
    }

    try {
      // Centered on Peru (Lat: -9.19, Lng: -75.015, Zoom: 6)
      const map = L.map(mapContainerRef.current, {
        center: [-9.19, -75.015],
        zoom: 6,
        minZoom: 4,
        maxZoom: 18,
        zoomControl: false,
      });

      // Custom top-left zoom control
      L.control.zoom({ position: 'topleft' }).addTo(map);

      // Esri World Imagery Satellite Tile Layer
      L.tileLayer(ESRI_SATELLITE_URL, {
        attribution: ESRI_ATTRIBUTION,
        maxZoom: 19,
      }).addTo(map);

      // Optional Labels Tile Layer
      const labelsLayer = L.tileLayer(ESRI_LABELS_URL, {
        pane: 'shadowPane',
        opacity: 0.85,
      });
      if (showLabels) {
        labelsLayer.addTo(map);
      }
      labelsLayerRef.current = labelsLayer;

      // Marker cluster or feature group
      const markersGroup = L.featureGroup().addTo(map);
      markersLayerRef.current = markersGroup;

      mapInstanceRef.current = map;
    } catch (err) {
      console.warn('Leaflet map initialization notice:', err);
    }

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('Leaflet cleanup notice:', e);
        }
        mapInstanceRef.current = null;
      }
    };
  }, [mapReady]);

  // 4. Update markers when malls or map changes
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current || !window.L) return;

    const L = window.L;
    const markersGroup = markersLayerRef.current;
    markersGroup.clearLayers();

    // Check if blueprint exists for mall
    const mallHasBlueprint = (mall: CentroComercial) => {
      const slug = mall.slug || mall.id;
      return slug === 'plaza-center-villa-el-salvador' || mall.id === '8341cdb0-19c2-4c01-8938-cf59fdfe7aa1';
    };

    // Filter malls that match search
    const mallsWithMatchingLocales: { mall: CentroComercial; locales: LocalComercial[] }[] = [];

    malls.forEach((mall) => {
      // Find locales belonging to this mall that are in searchedLocales
      const matchingLocales = searchQuery.trim()
        ? searchedLocales.filter(
            (l) =>
              l.centro_comercial_id === mall.id ||
              l.centro_comercial_id === mall.slug ||
              (l.centro_comercial_nombre &&
                l.centro_comercial_nombre.toLowerCase() === mall.nombre.toLowerCase())
          )
        : [];

      const hasLocalesMatch = matchingLocales.length > 0;
      if (hasLocalesMatch) {
        mallsWithMatchingLocales.push({ mall, locales: matchingLocales });
      }

      const isSelected = selectedMallId === mall.id || activeMall?.id === mall.id;
      const isSearchActive = searchQuery.trim().length > 0;

      // Color scheme based on search matches and selection
      let pinColor = isSelected ? '#10b981' : '#2563eb';
      let glowColor = isSelected ? 'rgba(16, 185, 129, 0.4)' : 'rgba(37, 99, 235, 0.3)';
      let pinOpacity = 1.0;

      if (isSearchActive) {
        if (hasLocalesMatch) {
          pinColor = '#10b981'; // Emerald highlight for malls with matching locales
          glowColor = 'rgba(16, 185, 129, 0.7)';
        } else {
          pinOpacity = 0.35; // Dim other malls when searching specific locales
        }
      }

      const matchBadgeHtml = hasLocalesMatch
        ? `<div style="
            position: absolute;
            top: -22px;
            background: #059669;
            color: #ffffff;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 999px;
            white-space: nowrap;
            box-shadow: 0 2px 6px rgba(0,0,0,0.35);
            border: 1.5px solid #ffffff;
            letter-spacing: 0.02em;
            animation: bounce 1s infinite alternate;
          ">
            ★ ${matchingLocales.length} local${matchingLocales.length > 1 ? 'es' : ''}
          </div>`
        : '';

      const customIcon = L.divIcon({
        className: 'custom-mall-pin',
        iconSize: [40, 48],
        iconAnchor: [20, 46],
        popupAnchor: [0, -42],
        html: `
          <div style="
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            opacity: ${pinOpacity};
            transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
          ">
            ${matchBadgeHtml}
            <div style="
              width: 36px;
              height: 36px;
              border-radius: 50% 50% 50% 0;
              transform: rotate(-45deg);
              background: ${pinColor};
              border: 3px solid #ffffff;
              box-shadow: 0 4px 14px ${glowColor}, 0 2px 4px rgba(0,0,0,0.3);
              display: flex;
              align-items: center;
              justify-content: center;
            ">
              <span style="
                transform: rotate(45deg);
                color: #ffffff;
                font-weight: 800;
                font-size: 13px;
                font-family: sans-serif;
                text-shadow: 0 1px 2px rgba(0,0,0,0.4);
              ">
                ${mall.nombre.charAt(0)}
              </span>
            </div>
            <div style="
              position: absolute;
              bottom: -4px;
              width: 10px;
              height: 4px;
              background: rgba(0, 0, 0, 0.35);
              border-radius: 50%;
              filter: blur(1px);
            "></div>
          </div>
        `,
      });

      const marker = L.marker([mall.lat, mall.lon], { icon: customIcon });

      // Build matching locales section for popup
      const matchingLocalesHtml = hasLocalesMatch
        ? `
          <div style="
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-radius: 8px;
            padding: 8px 10px;
            margin-bottom: 10px;
          ">
            <span style="
              font-size: 10px;
              font-weight: 800;
              color: #065f46;
              text-transform: uppercase;
              display: block;
              margin-bottom: 5px;
            ">
              ✓ ${matchingLocales.length} Local${matchingLocales.length > 1 ? 'es' : ''} Encontrado${matchingLocales.length > 1 ? 's' : ''}:
            </span>
            <div style="max-height: 100px; overflow-y: auto; font-size: 11px;">
              ${matchingLocales
                .slice(0, 5)
                .map(
                  (l) => `
                  <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 3px 0;
                    border-bottom: 1px dashed #d1fae5;
                  ">
                    <span style="font-weight: 700; color: #047857;">${l.nombre_comercial || l.codigo_local}</span>
                    <span style="font-size: 10px; font-family: monospace; background: #10b981; color: white; padding: 1px 5px; border-radius: 4px;">
                      ${l.codigo_local}
                    </span>
                  </div>
                `
                )
                .join('')}
              ${
                matchingLocales.length > 5
                  ? `<div style="font-size: 10px; color: #059669; text-align: center; margin-top: 3px;">+${matchingLocales.length - 5} locales más</div>`
                  : ''
              }
            </div>
          </div>
        `
        : '';

      const hasPlan = mallHasBlueprint(mall);
      const actionButtonHtml = hasPlan
        ? `
          <a href="/planos?mall_id=${mall.id}${matchingLocales.length > 0 ? `&local_id=${matchingLocales[0].id}` : ''}" style="
            display: block;
            text-align: center;
            background: #2563eb;
            color: #ffffff;
            font-weight: 700;
            font-size: 12px;
            padding: 8px 12px;
            border-radius: 8px;
            text-decoration: none;
            box-shadow: 0 2px 6px rgba(37,99,235,0.3);
          ">
            Ver en Plano Arquitectónico &rarr;
          </a>
        `
        : `
          <div style="
            display: block;
            text-align: center;
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
            font-weight: 700;
            font-size: 11px;
            padding: 7px 10px;
            border-radius: 8px;
          ">
            Pendiente Cargar Información
          </div>
        `;

      // Clean, branded popup
      const popupContent = `
        <div style="
          min-width: 250px;
          padding: 6px 2px;
          font-family: system-ui, -apple-system, sans-serif;
        ">
          <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
            <span style="
              background: #dbeafe;
              color: #1e40af;
              font-size: 10px;
              font-weight: 700;
              padding: 2px 6px;
              border-radius: 4px;
              text-transform: uppercase;
            ">${mall.departamento}</span>
            <span style="font-size: 11px; color: #64748b;">${mall.distrito || mall.provincia || ''}</span>
          </div>

          <h4 style="
            font-size: 15px;
            font-weight: 800;
            color: #0f172a;
            margin: 0 0 6px 0;
            line-height: 1.25;
          ">${mall.nombre}</h4>

          <p style="
            font-size: 11px;
            color: #475569;
            margin: 0 0 10px 0;
            line-height: 1.3;
          ">${mall.direccion}</p>

          ${matchingLocalesHtml}

          <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px;
            margin-bottom: 12px;
          ">
            <div>
              <span style="display: block; font-size: 10px; color: #64748b; font-weight: 600;">LOCALES TOTALES</span>
              <strong style="font-size: 14px; color: #0f172a;">${mall.total_locales}</strong>
            </div>
            <div>
              <span style="display: block; font-size: 10px; color: #64748b; font-weight: 600;">SUPERFICIE</span>
              <strong style="font-size: 14px; color: #0f172a;">${mall.superficie_total_m2.toLocaleString()} m²</strong>
            </div>
          </div>

          ${actionButtonHtml}
        </div>
      `;

      marker.bindPopup(popupContent, { maxWidth: 320 });

      marker.on('click', () => {
        setActiveMall(mall);
        if (onSelectMall) onSelectMall(mall);
      });

      markersGroup.addLayer(marker);
    });

    // Auto-focus if there is exactly 1 mall with matching locales during search
    if (mallsWithMatchingLocales.length === 1 && searchQuery.trim()) {
      const targetMall = mallsWithMatchingLocales[0].mall;
      mapInstanceRef.current.setView([targetMall.lat, targetMall.lon], 14, {
        animate: true,
        duration: 1.0,
      });
    }
  }, [malls, selectedMallId, activeMall, onSelectMall, searchedLocales, searchQuery]);

  // 5. Toggle Street Labels
  const handleToggleLabels = () => {
    if (!mapInstanceRef.current || !labelsLayerRef.current) return;
    const map = mapInstanceRef.current;
    const labels = labelsLayerRef.current;

    if (showLabels) {
      map.removeLayer(labels);
      setShowLabels(false);
    } else {
      map.addLayer(labels);
      setShowLabels(true);
    }
  };

  // 6. Reset view to Peru
  const handleResetPeru = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.setView([-9.19, -75.015], 6, {
      animate: true,
      duration: 1.2,
    });
    setActiveMall(null);
  };

  // 7. Focus a specific mall
  const handleFocusMall = (mall: CentroComercial) => {
    setActiveMall(mall);
    if (onSelectMall) onSelectMall(mall);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([mall.lat, mall.lon], 14, {
        animate: true,
        duration: 1.2,
      });
    }
  };

  return (
    <div className={`relative flex flex-col bg-slate-900 rounded-3xl overflow-hidden shadow-2xl border border-slate-700/60 ${className}`}>
      {/* Search match banner over map */}
      {searchQuery.trim() && searchedLocales.length > 0 && (
        <div className="absolute top-4 left-14 z-20 hidden sm:flex items-center gap-2 bg-emerald-950/90 backdrop-blur-md border border-emerald-500/50 text-emerald-100 px-3.5 py-2 rounded-2xl shadow-xl">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-xs font-bold">
            Ubicación satelital: {searchedLocales.length} local{searchedLocales.length > 1 ? 'es' : ''} encontrado{searchedLocales.length > 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* Top Map Toolbar */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-2xl border border-slate-700 shadow-xl">
        <button
          type="button"
          onClick={handleToggleLabels}
          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            showLabels
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
              : 'bg-slate-800 text-slate-400 hover:text-white'
          }`}
          title="Alternar etiquetas y límites geográficos"
        >
          <Layers size={14} />
          <span>{showLabels ? 'Satélite + Etiquetas' : 'Satélite Puro'}</span>
        </button>

        <button
          type="button"
          onClick={handleResetPeru}
          className="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors flex items-center gap-1.5"
          title="Centrar vista completa del Perú"
        >
          <Globe size={14} />
          <span>Vista Perú</span>
        </button>
      </div>

      {/* Map Element */}
      <div
        ref={mapContainerRef}
        id="peru-satellite-map"
        className="w-full h-[460px] md:h-[540px] z-10 bg-slate-950"
      />

      {/* Loading Overlay */}
      {(!mapReady || loading) && (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-slate-900/80 backdrop-blur-sm text-white">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm font-semibold tracking-wide">Cargando Mapa Satelital Esri...</p>
          <p className="text-xs text-slate-400 mt-1">Conectando con servidores GIS y 11 activos comerciales en Perú</p>
        </div>
      )}

      {/* Quick Mall Carousel / Selector Footer — hidden when hideCarousel=true */}
      {!hideCarousel && (
      <div className="bg-slate-950/95 border-t border-slate-800/80 p-3 px-4 z-20">
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Activos Comerciales Geolocalizados ({malls.length})
            </span>
          </div>
          <span className="text-[11px] text-slate-500 hidden sm:inline">
            Haz clic en un activo para enfocarlo en el mapa satelital
          </span>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-slate-700">
          {malls.map((mall) => {
            const isSelected = activeMall?.id === mall.id || selectedMallId === mall.id;
            return (
              <button
                key={mall.id}
                type="button"
                onClick={() => handleFocusMall(mall)}
                className={`flex-shrink-0 text-left px-3 py-2 rounded-xl transition-all border text-xs flex items-center gap-2.5 ${
                  isSelected
                    ? 'bg-blue-600/30 border-blue-500 text-white shadow-md'
                    : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-[11px] ${
                    isSelected ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {mall.nombre.charAt(0)}
                </div>
                <div>
                  <span className="block font-bold text-[12px] truncate max-w-[150px]">
                    {mall.nombre}
                  </span>
                  <span className="block text-[10px] text-slate-400">
                    {mall.departamento} • {mall.total_locales} locales
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
      )}
    </div>
  );
};
