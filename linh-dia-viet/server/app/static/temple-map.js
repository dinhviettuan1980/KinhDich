/* Bản đồ trang đền: bắt đầu ở vị trí khách (nếu có), "bay" tới đền rồi thả ghim.
   Có key → Google Maps; chưa có key hoặc key bị từ chối → OpenStreetMap (Leaflet). */
(function () {
  const box = document.getElementById("ld-gmap");
  if (!box) return;
  const ds = box.dataset;
  const temple = { lat: +ds.lat, lng: +ds.lng };
  const home = ds.homeLat ? { lat: +ds.homeLat, lng: +ds.homeLng } : null;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const load = (tag, attrs) => new Promise((ok, fail) => {
    const el = Object.assign(document.createElement(tag), attrs, { onload: ok, onerror: fail });
    document.head.appendChild(el);
  });

  // ---- Google Maps ----
  async function flyGoogle(map, G) {
    await sleep(700);
    map.panTo(temple);
    await sleep(1300);
    for (let z = map.getZoom() + 1; z <= 16; z++) { map.setZoom(z); await sleep(380); }
    const pin = new G.Marker({ position: temple, map, animation: G.Animation.DROP, title: ds.name });
    await sleep(700);
    new G.InfoWindow({ content: `<b style="font:600 15px system-ui">${ds.name}</b>` }).open({ map, anchor: pin });
  }

  window.ldInitMap = function () {
    const G = google.maps;
    const map = new G.Map(box, {
      center: home || temple, zoom: home ? 12 : 13, disableDefaultUI: true, zoomControl: true, gestureHandling: "cooperative",
    });
    if (home) {
      new G.Marker({ position: home, map, title: "Vị trí của bạn",
        icon: { path: G.SymbolPath.CIRCLE, scale: 9, fillColor: "#346ebe", fillOpacity: 1, strokeColor: "#fff", strokeWeight: 3 } });
      new G.Polyline({ path: [home, temple], map, strokeOpacity: 0, icons: [{
        icon: { path: "M 0,-1 0,1", strokeOpacity: 1, strokeColor: "#7a1f1f", scale: 3 }, offset: "0", repeat: "14px" }] });
    }
    G.event.addListenerOnce(map, "tilesloaded", () => flyGoogle(map, G));
  };

  // ---- OpenStreetMap (Leaflet) ----
  let osmStarted = false;
  async function osm() {
    if (osmStarted) return;
    osmStarted = true;
    box.innerHTML = "";
    await load("link", { rel: "stylesheet", href: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" });
    await load("script", { src: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" });
    const map = L.map(box, { zoomControl: true, attributionControl: true }).setView(home || temple, home ? 12 : 13);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" }).addTo(map);
    if (home) {
      L.circleMarker(home, { radius: 9, color: "#fff", weight: 3, fillColor: "#346ebe", fillOpacity: 1 })
        .addTo(map).bindTooltip("Vị trí của bạn");
      L.polyline([home, temple], { color: "#7a1f1f", weight: 3, dashArray: "8 8" }).addTo(map);
    }
    await sleep(900);
    map.flyTo(temple, 16, { duration: 2.6 });
    map.once("moveend", () => {
      const pin = L.marker(temple).addTo(map);
      const el = pin.getElement();
      if (el) el.animate([{ transform: el.style.transform + " translateY(-60px)", opacity: 0 },
                          { transform: el.style.transform, opacity: 1 }], { duration: 450, easing: "ease-out" });
      setTimeout(() => pin.bindPopup(`<b>${ds.name}</b>`).openPopup(), 500);
    });
  }

  window.gm_authFailure = osm;  // Google gọi khi key không hợp lệ / chưa bật Maps JavaScript API
  if (ds.key) {
    load("script", { async: true,
      src: "https://maps.googleapis.com/maps/api/js?key=" + encodeURIComponent(ds.key) +
           "&callback=ldInitMap&loading=async&language=vi&region=VN" }).catch(osm);
  } else {
    osm();
  }
})();
