/* Bản đồ đình chùa. Có Google Maps API key → Google Maps JS (Advanced Marker + MarkerClusterer);
   chưa có key → Leaflet + nền OpenStreetMap. Lọc, tìm, "gần tôi" chạy hoàn toàn trên trình duyệt. */
(function () {
  "use strict";
  var C = window.LD_MAP || {};
  var COLORS = { chua: "#b8892b", den: "#7a1f1f", dinh: "#8a4b1f", mieu: "#c2410c", phu: "#6b3fa0", khac: "#6f5f52" };
  var BOOK = "#2f6b3a";
  // Tâm lệch ra biển để khung mặc định (zoom 5, cả trên điện thoại) thấy trọn đất liền + Hoàng Sa + Trường Sa.
  var VN = { lat: 15.8, lng: 108.6 };
  // Chủ quyền: luôn hiện nhãn hai quần đảo, không phụ thuộc nền bản đồ (không gom cụm, không bị bộ lọc ẩn).
  var ISLANDS = [
    { lat: 16.5, lng: 112.0, n: "Quần đảo Hoàng Sa", sub: "(Việt Nam)" },
    { lat: 12.3, lng: 113.3, n: "Quần đảo Trường Sa", sub: "(Việt Nam)" }  // phía bắc quần đảo, không đè lên điểm chùa
  ];
  function islandEl(i) {
    var d = document.createElement("div"); d.className = "ld-island";
    d.innerHTML = "<b>" + esc(i.n) + "</b><span>" + esc(i.sub) + "</span>";
    return d;
  }
  var $ = function (id) { return document.getElementById(id); };
  var all = [], kinds = {}, me = null, adapter = null, lastList = [];

  function plain(s) {
    return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function km(a, b) {
    var R = 6371, r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  function fmtKm(d) { return d < 1 ? Math.round(d * 1000) + " m" : (d < 10 ? d.toFixed(1) : Math.round(d)) + " km"; }
  function color(p) { return p.b === 2 ? BOOK : (COLORS[p.k] || COLORS.khac); }
  function detailUrl(p) { return C.detail + p.id; }
  function dirUrl(p) { return "https://www.google.com/maps/dir/?api=1&destination=" + p.lat + "," + p.lng; }

  function popup(p) {
    return '<div class="ld-pop"><b>' + esc(p.n) + "</b><br><span>" + esc(kinds[p.k] || "") + (p.pv ? " · " + esc(p.pv) : "") + "</span>" +
      (p.b === 2 ? '<br><span class="ld-badge on">★ Nhận lễ từ xa</span>' : "") +
      '<br><a href="' + detailUrl(p) + '">' + (p.b === 2 ? "Xem & đặt lễ" : "Xem chi tiết") + "</a> · " +
      '<a href="' + dirUrl(p) + '" target="_blank" rel="noopener">Chỉ đường</a></div>';
  }

  function loadJS(src) {
    return new Promise(function (ok, fail) {
      var s = document.createElement("script"); s.src = src; s.async = true; s.onload = ok; s.onerror = fail;
      document.head.appendChild(s);
    });
  }
  function loadCSS(href) {
    var l = document.createElement("link"); l.rel = "stylesheet"; l.href = href; document.head.appendChild(l);
  }

  /* ---- Google Maps ---- */
  function googleAdapter(el) {
    return new Promise(function (ok, fail) {
      window.__ldGmReady = ok;
      loadJS("https://maps.googleapis.com/maps/api/js?key=" + encodeURIComponent(C.key) +
        "&v=weekly&language=vi&region=VN&libraries=marker&loading=async&callback=__ldGmReady").catch(fail);
    }).then(function () {
      return loadJS("https://unpkg.com/@googlemaps/markerclusterer@2.5.3/dist/index.min.js");
    }).then(function () {
      var g = window.google.maps;
      var map = new g.Map(el, { center: VN, zoom: 5, mapId: C.mapId || "DEMO_MAP_ID", streetViewControl: false,
        mapTypeControl: false, fullscreenControl: true, gestureHandling: "greedy" });
      var info = new g.InfoWindow(), cache = {}, meMarker = null;
      var clusterer = new window.markerClusterer.MarkerClusterer({ map: map });
      ISLANDS.forEach(function (i) {
        new g.marker.AdvancedMarkerElement({ map: map, position: { lat: i.lat, lng: i.lng }, content: islandEl(i),
          title: i.n + " " + i.sub, zIndex: 1, gmpClickable: false });
      });
      function marker(p) {
        if (!cache[p.id]) {
          var pin = new g.marker.PinElement({ background: color(p), borderColor: "#ffffff", glyphColor: "#ffffff",
            scale: p.b === 2 ? 1.1 : 0.8 });
          var m = new g.marker.AdvancedMarkerElement({ position: { lat: p.lat, lng: p.lng }, content: pin.element, title: p.n });
          m.addListener("click", function () { info.setContent(popup(p)); info.open({ map: map, anchor: m }); });
          cache[p.id] = m;
        }
        return cache[p.id];
      }
      return {
        show: function (list) { clusterer.clearMarkers(); clusterer.addMarkers(list.map(marker)); },
        focus: function (p) {
          map.setCenter({ lat: p.lat, lng: p.lng }); map.setZoom(16);
          var m = marker(p); info.setContent(popup(p)); info.open({ map: map, anchor: m });
        },
        fit: function (pts) {
          if (!pts.length) return;
          var b = new g.LatLngBounds(); pts.forEach(function (p) { b.extend({ lat: p.lat, lng: p.lng }); });
          map.fitBounds(b, 40); if (pts.length === 1) map.setZoom(15);
        },
        me: function (pos) {
          if (!meMarker) {
            var dot = document.createElement("div"); dot.className = "ld-me";
            meMarker = new g.marker.AdvancedMarkerElement({ map: map, content: dot, title: "Vị trí của bạn" });
          }
          meMarker.position = pos;
        },
        reset: function () { map.setCenter(VN); map.setZoom(5); }
      };
    });
  }

  /* ---- Leaflet (chưa có key) ---- */
  function leafletAdapter(el) {
    var base = "https://unpkg.com/";
    loadCSS(base + "leaflet@1.9.4/dist/leaflet.css");
    loadCSS(base + "leaflet.markercluster@1.5.3/dist/MarkerCluster.css");
    loadCSS(base + "leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css");
    return loadJS(base + "leaflet@1.9.4/dist/leaflet.js").then(function () {
      return loadJS(base + "leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js");
    }).then(function () {
      var L = window.L;
      el.innerHTML = "";
      var map = L.map(el, { preferCanvas: true }).setView([VN.lat, VN.lng], 5);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
      var group = L.markerClusterGroup({ chunkedLoading: true, showCoverageOnHover: false, maxClusterRadius: 50 });
      map.addLayer(group);
      ISLANDS.forEach(function (i) {
        L.marker([i.lat, i.lng], { interactive: false, keyboard: false, zIndexOffset: -1000,
          icon: L.divIcon({ className: "", html: islandEl(i).outerHTML, iconSize: null }) }).addTo(map);
      });
      var cache = {}, meMarker = null;
      function marker(p) {
        if (!cache[p.id]) {
          cache[p.id] = L.circleMarker([p.lat, p.lng], { radius: p.b === 2 ? 9 : 6, color: "#fff", weight: 1.5,
            fillColor: color(p), fillOpacity: 0.95 }).bindPopup(function () { return popup(p); });
        }
        return cache[p.id];
      }
      return {
        show: function (list) { group.clearLayers(); group.addLayers(list.map(marker)); },
        focus: function (p) {
          var m = marker(p);
          group.zoomToShowLayer(m, function () { m.openPopup(); });
        },
        fit: function (pts) {
          if (!pts.length) return;
          map.fitBounds(L.latLngBounds(pts.map(function (p) { return [p.lat, p.lng]; })), { padding: [30, 30], maxZoom: 15 });
        },
        me: function (pos) {
          if (!meMarker) meMarker = L.circleMarker([pos.lat, pos.lng], { radius: 7, color: "#fff", weight: 3,
            fillColor: "#1a73e8", fillOpacity: 1 }).bindTooltip("Vị trí của bạn").addTo(map);
          else meMarker.setLatLng([pos.lat, pos.lng]);
        },
        reset: function () { map.setView([VN.lat, VN.lng], 5); }
      };
    });
  }

  /* ---- Lọc + danh sách ---- */
  function filtered() {
    var q = plain($("ld-q").value.trim()), k = $("ld-kind").value, pv = $("ld-prov").value, b = $("ld-book").checked;
    return all.filter(function (p) {
      return (!k || p.k === k) && (!pv || p.pv === pv) && (!b || p.b === 2) && (!q || p.q.indexOf(q) >= 0);
    });
  }
  function active() { return $("ld-q").value.trim() || $("ld-kind").value || $("ld-prov").value || $("ld-book").checked || me; }

  function renderList(list) {
    var box = $("ld-list");
    $("ld-count").textContent = list.length === all.length ? "" : "Tìm thấy " + list.length.toLocaleString("vi-VN") + " địa điểm.";
    if (!active()) { box.innerHTML = ""; return; }
    var rows = list.slice();
    if (me) rows.sort(function (a, b) { return a.d - b.d; });
    rows = rows.slice(0, 50);
    lastList = rows;
    box.innerHTML = rows.map(function (p, i) {
      return '<div class="ld-card ld-place-row"><div class="ld-spread"><span><a href="' + detailUrl(p) + '"><b>' + esc(p.n) + "</b></a>" +
        (p.b === 2 ? ' <span class="ld-badge on">★ Nhận lễ</span>' : "") + '<br><span class="ld-muted small">' + esc(kinds[p.k] || "") +
        (p.pv ? " · " + esc(p.pv) : "") + (me ? " · " + fmtKm(p.d) : "") + "</span></span>" +
        '<button type="button" class="ld-btn small secondary" data-i="' + i + '">Xem</button></div></div>';
    }).join("") + (list.length > 50 ? '<p class="ld-muted small">Hiện 50 địa điểm đầu, hãy tìm cụ thể hơn để thu hẹp.</p>' : "");
  }

  var timer = null;
  function apply(fit) {
    var list = filtered();
    if (adapter) {
      adapter.show(list);
      if (fit) {
        if (me) adapter.fit([me].concat(list.slice().sort(function (a, b) { return a.d - b.d; }).slice(0, 8)));
        else if (list.length && list.length < all.length) adapter.fit(list.slice(0, 500));
        else adapter.reset();
      }
    }
    renderList(list);
  }
  function schedule() { clearTimeout(timer); timer = setTimeout(function () { apply(true); }, 250); }

  function locate() {
    var btn = $("ld-near");
    if (!navigator.geolocation) { alert("Trình duyệt không hỗ trợ định vị."); return; }
    btn.disabled = true; btn.textContent = "Đang định vị…";
    navigator.geolocation.getCurrentPosition(function (pos) {
      me = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      all.forEach(function (p) { p.d = km(me, p); });
      if (adapter) adapter.me(me);
      btn.disabled = false; btn.textContent = "📍 Gần tôi";
      apply(true);
    }, function () {
      btn.disabled = false; btn.textContent = "📍 Gần tôi";
      alert("Không lấy được vị trí. Hãy cho phép trình duyệt truy cập vị trí rồi thử lại.");
    }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
  }

  function init() {
    var el = $("ld-map");
    var dataP = fetch(C.data, { credentials: "same-origin" }).then(function (r) { return r.json(); });
    var mapP = (C.key ? googleAdapter(el) : leafletAdapter(el)).catch(function (e) {
      console.error(e);
      el.innerHTML = '<p class="ld-muted" style="padding:16px">Không tải được bản đồ. Danh sách bên dưới vẫn tìm được.</p>';
      return null;
    });
    dataP.then(function (d) {
      kinds = d.kinds;
      var counts = {}, provCounts = {};
      all = d.points.map(function (a) {
        var p = { id: a[0], lat: a[1], lng: a[2], k: a[3], n: a[4], pv: d.provinces[a[5]] || "", b: a[6], q: plain(a[4]) };
        counts[p.k] = (counts[p.k] || 0) + 1; if (p.pv) provCounts[p.pv] = (provCounts[p.pv] || 0) + 1;
        return p;
      });
      Object.keys(kinds).forEach(function (k) {
        if (counts[k]) $("ld-kind").insertAdjacentHTML("beforeend", '<option value="' + k + '">' + esc(kinds[k]) + " (" + counts[k] + ")</option>");
      });
      d.provinces.forEach(function (pv) {
        $("ld-prov").insertAdjacentHTML("beforeend", '<option value="' + esc(pv) + '">' + esc(pv) + " (" + provCounts[pv] + ")</option>");
      });
      return mapP;
    }).then(function (a) {
      adapter = a;
      apply(false);
      var m = /^#p(\d+)$/.exec(location.hash);
      var target = m && all.filter(function (p) { return p.id === +m[1]; })[0];
      if (target && adapter) adapter.focus(target);
    });
    $("ld-q").addEventListener("input", schedule);
    ["ld-kind", "ld-prov", "ld-book"].forEach(function (id) { $(id).addEventListener("change", function () { apply(true); }); });
    $("ld-near").addEventListener("click", locate);
    $("ld-list").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-i]");
      if (b && adapter) { adapter.focus(lastList[+b.dataset.i]); $("ld-map").scrollIntoView({ behavior: "smooth", block: "center" }); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
