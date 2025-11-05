# map_desktop.py
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

HTML = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>MapBuilder — Desktop (Enhanced)</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html,body,#map{height:100%;margin:0;background:#07090b;color:#ddd;font-family:Inter,system-ui}
    .controls{position:absolute;left:12px;top:12px;z-index:1000}
    .search{backdrop-filter: blur(6px); background: rgba(10,12,14,0.6); padding:10px;border-radius:10px}
    input{background:transparent;border:1px solid #2a2f33;padding:8px;color:#eee;border-radius:6px;width:320px}
    button{margin-left:6px;padding:8px;border-radius:6px;background:#111214;color:#fff;border:none}
    .hint{margin-top:6px;color:#9aa0a6;font-size:12px}
    .leaflet-popup-content-wrapper { background: #0b0f12; color: #ddd; border-radius: 8px; }
  </style>
</head>
<body>
  <div id="map"></div>

  <div class="controls">
    <div class="search">
      <input id="q" placeholder="Search country / continent / place (e.g. Uganda, Africa, Europe)" />
      <button id="go">Go</button>
      <button id="world">World</button>
      <div class="hint">Press Enter to search • Double-click to zoom</div>
    </div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const map = L.map('map', { zoomControl:true }).setView([20,0], 2);
    const darkTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    const citiesGeoJSON = {
      "type":"FeatureCollection",
      "features":[
        {"type":"Feature","properties":{"name":"New York, USA","pop":"8.4M"},"geometry":{"type":"Point","coordinates":[-74.0060,40.7128]}},
        {"type":"Feature","properties":{"name":"London, UK","pop":"9.0M"},"geometry":{"type":"Point","coordinates":[-0.1276,51.5074]}},
        {"type":"Feature","properties":{"name":"Tokyo, Japan","pop":"14M"},"geometry":{"type":"Point","coordinates":[139.6917,35.6895]}},
        {"type":"Feature","properties":{"name":"Nairobi, Kenya","pop":"4.4M"},"geometry":{"type":"Point","coordinates":[36.8219,-1.2921]}},
        {"type":"Feature","properties":{"name":"Kampala, Uganda","pop":"1.7M"},"geometry":{"type":"Point","coordinates":[32.5825,0.3476]}},
        {"type":"Feature","properties":{"name":"Sydney, Australia","pop":"5.3M"},"geometry":{"type":"Point","coordinates":[151.2093,-33.8688]}},
        {"type":"Feature","properties":{"name":"Paris, France","pop":"2.1M"},"geometry":{"type":"Point","coordinates":[2.3522,48.8566]}},
        {"type":"Feature","properties":{"name":"Cairo, Egypt","pop":"9.5M"},"geometry":{"type":"Point","coordinates":[31.2357,30.0444]}},
        {"type":"Feature","properties":{"name":"Beijing, China","pop":"21M"},"geometry":{"type":"Point","coordinates":[116.4074,39.9042]}},
        {"type":"Feature","properties":{"name":"Moscow, Russia","pop":"12.5M"},"geometry":{"type":"Point","coordinates":[37.6173,55.7558]}},
        {"type":"Feature","properties":{"name":"Rio de Janeiro, Brazil","pop":"6.7M"},"geometry":{"type":"Point","coordinates":[-43.1729,-22.9068]}}
      ]
    };

    function cityPointToLayer(feature, latlng) {
      const marker = L.circleMarker(latlng, {
        radius: 8,
        weight: 1,
        opacity: 1,
        fillOpacity: 0.9
      });
      const name = feature.properties.name || "City";
      const pop = feature.properties.pop ? (" — pop: " + feature.properties.pop) : "";
      marker.bindPopup(`<strong>${name}</strong><div style="font-size:12px;color:#9aa0a6">${pop}</div>`);
      return marker;
    }

    const citiesLayer = L.geoJSON(citiesGeoJSON, { pointToLayer: cityPointToLayer });

    const countriesGeoJsonUrl = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json';
    let bordersLayer = L.layerGroup();
    async function loadBorders() {
      try {
        const res = await fetch(countriesGeoJsonUrl);
        if(!res.ok) throw new Error('Failed to load borders');
        const geo = await res.json();
        bordersLayer = L.geoJSON(geo, {
          style: function(feature){ return { color: '#6dd3ff', weight: 1, opacity: 0.8, fill: false }; },
          onEachFeature: function (feature, layer) {
            const n = feature.properties && (feature.properties.name || feature.properties.NAME);
            if(n) layer.bindPopup(`<strong>${n}</strong>`);
          }
        });
      } catch(e) { console.warn('Could not load country borders:', e); }
    }
    loadBorders();

    const roadsTiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {opacity:0.65});

    const baseMaps = { "Dark": darkTiles };
    const overlayMaps = { "Cities": citiesLayer, "Borders (load online)": bordersLayer, "Roads (OSM overlay)": roadsTiles };
    let layersControl = L.control.layers(baseMaps, overlayMaps, { collapsed: false }).addTo(map);
    layersControl._lastRequestedShow = [];
    setTimeout(async function(){
      await loadBorders();
      try { layersControl.remove(); } catch(e) {}
      const newOverlayMaps = { "Cities": citiesLayer, "Borders (load online)": bordersLayer, "Roads (OSM overlay)": roadsTiles };
      layersControl = L.control.layers(baseMaps, newOverlayMaps, { collapsed: false }).addTo(map);
    }, 1200);

    citiesLayer.addTo(map);

    async function geocode(q) {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=1`;
      const r = await fetch(url,{headers:{'Accept':'application/json'}});
      const j = await r.json();
      return j[0];
    }

    document.getElementById('go').onclick = async ()=> {
      const q = document.getElementById('q').value.trim();
      if(!q) return;
      const res = await geocode(q);
      if(!res) { alert('Not found'); return; }
      const lat = parseFloat(res.lat), lon = parseFloat(res.lon);
      if(res.boundingbox){
        const bb = res.boundingbox.map(Number);
        const south = bb[0], north = bb[1], west = bb[2], east = bb[3];
        map.fitBounds([[south, west],[north, east]], { maxZoom: 8 });
      } else {
        map.setView([lat,lon], 8);
      }
      if(window._lastSearchMarker) map.removeLayer(window._lastSearchMarker);
      window._lastSearchMarker = L.circleMarker([lat,lon], { radius: 9, color: '#ffd166', weight:2}).addTo(map).bindPopup(res.display_name).openPopup();
    };

    document.getElementById('q').addEventListener('keydown', (e)=>{ if(e.key==="Enter") document.getElementById('go').click(); });
    document.getElementById('world').onclick = ()=>{ map.setView([20,0],2); if(window._lastSearchMarker) map.removeLayer(window._lastSearchMarker); };
    L.control.scale({imperial:false, metric:true}).addTo(map);
  </script>
</body>
</html>
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MapBuilder — Desktop (Enhanced)')
        self.resize(1200,800)
        view = QWebEngineView()
        view.setHtml(HTML, QUrl(''))
        self.setCentralWidget(view)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
