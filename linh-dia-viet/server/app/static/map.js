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
    { lat: 18.0, lng: 112.0, n: "Quần đảo Hoàng Sa", sub: "(Việt Nam)" },  // trên quần đảo, không đè nhãn của nền Google
    { lat: 10.8, lng: 111.7, n: "Quần đảo Trường Sa", sub: "(Việt Nam)" }  // khoảng trống phía tây, không đè điểm chùa (Song Tử Tây…)
  ];
  function islandEl(i) {
    var d = document.createElement("div"); d.className = "ld-island";
    // 3 dòng cho gọn, không đè lên cụm điểm ven biển
    d.innerHTML = "<b>" + esc(i.n).replace("Quần đảo ", "Quần đảo<br>") + "</b><span>" + esc(i.sub) + "</span>";
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
  function dirUrl(p) {  // vị trí gần đúng → để Google tìm theo tên + địa chỉ
    return "https://www.google.com/maps/dir/?api=1&destination=" + (p.aq ? encodeURIComponent(p.aq) : p.lat + "," + p.lng);
  }

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
  /* "Bay" tới một điểm: lướt tâm bản đồ, thu nhỏ ở giữa đường (đi xa thì thu nhiều hơn) rồi phóng to vào điểm. */
  var FLY_MS = 2200;
  function flyTo(map, to, zoom, done) {
    var c = map.getCenter(), from = { lat: c.lat(), lng: c.lng() }, z0 = map.getZoom();
    var hop = Math.min(4, Math.max(1, Math.log2(1 + km(from, to)) / 2));  // độ "bay lên" theo quãng đường
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { map.moveCamera({ center: to, zoom: zoom }); if (done) done(); return; }
    var t0 = null;
    function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
    function step(now) {
      if (t0 === null) t0 = now;
      var t = Math.min(1, (now - t0) / FLY_MS), e = ease(t);
      map.moveCamera({ center: { lat: from.lat + (to.lat - from.lat) * e, lng: from.lng + (to.lng - from.lng) * e },
                       zoom: z0 + (zoom - z0) * e - hop * Math.sin(Math.PI * t) });
      if (t < 1) requestAnimationFrame(step); else if (done) done();
    }
    requestAnimationFrame(step);
  }

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
      var MC = window.markerClusterer;
      // Ngừng gom cụm từ zoom 16 để "focus" (zoom 16) luôn thấy từng điểm.
      var clusterer = new MC.MarkerClusterer({ map: map, algorithm: new MC.SuperClusterAlgorithm({ maxZoom: 15, radius: 60 }) });
      ISLANDS.forEach(function (i) {
        var lbl = islandEl(i); lbl.style.transform = "translateY(50%)";  // Advanced Marker neo đáy → đưa tâm nhãn về toạ độ
        new g.marker.AdvancedMarkerElement({ map: map, position: { lat: i.lat, lng: i.lng }, content: lbl,
          title: i.n + " " + i.sub, zIndex: 1, gmpClickable: false });
      });
      function marker(p) {
        if (!cache[p.id]) {
          var pin = new g.marker.PinElement({ background: color(p), borderColor: "#ffffff", glyphColor: "#ffffff",
            scale: p.b === 2 ? 1.1 : 0.8 });
          var m = new g.marker.AdvancedMarkerElement({ position: { lat: p.lat, lng: p.lng }, content: pin, title: p.n,
            gmpClickable: true });
          m.addEventListener("gmp-click", function () { info.setContent(popup(p)); info.open({ map: map, anchor: m }); });
          cache[p.id] = m;
        }
        return cache[p.id];
      }
      return {
        show: function (list) { clusterer.clearMarkers(); clusterer.addMarkers(list.map(marker)); },
        focus: function (p) {
          info.close();
          flyTo(map, { lat: p.lat, lng: p.lng }, 16, function () {
            // mở theo toạ độ (không neo vào marker: marker có thể chưa được clusterer vẽ lên bản đồ)
            info.setContent(popup(p)); info.setOptions({ position: { lat: p.lat, lng: p.lng }, pixelOffset: new g.Size(0, -34) });
            info.open({ map: map });
          });
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
          map.closePopup();
          map.flyTo([p.lat, p.lng], 16, { duration: FLY_MS / 1000 });
          map.once("moveend", function () { group.zoomToShowLayer(m, function () { m.openPopup(); }); });
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
  /* Tìm kiếm: không dấu, không cần đúng thứ tự, mỗi từ gõ khớp đầu một từ trong tên / tên gọi khác / tỉnh /
     từ khoá + địa chỉ + mô tả (trọng số giảm dần); khớp nguyên cụm được cộng thêm. Ít kết quả quá → nới:
     cho sai 1 chữ cái (từ ≥ 4 ký tự) và thiếu 1 từ (khi gõ ≥ 3 từ). */
  var W = { n: 10, a: 8, pv: 5, x: 2 }, lowRaw = "";
  var PV_ALIAS = { "Hồ Chí Minh": "tp hcm tphcm sai gon saigon thanh pho", "Hà Nội": "hn thu do thang long",
    "Huế": "thua thien co do", "Đà Nẵng": "dn", "Hải Phòng": "hp" };
  function words(s) { return plain(s).split(/[^a-z0-9]+/).filter(Boolean); }
  function near1(a, b) {  // khoảng cách sửa ≤ 1
    if (a === b) return true;
    var la = a.length, lb = b.length;
    if (Math.abs(la - lb) > 1) return false;
    var i = 0, j = 0, diff = 0;
    while (i < la && j < lb) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++diff > 1) return false;
      if (la > lb) i++; else if (lb > la) j++; else { i++; j++; }
    }
    return diff + (la - i) + (lb - j) <= 1;
  }
  function tokScore(t, list, fuzzy) {  // 1 = trùng từ, .7 = khớp đầu từ, .45 = sai 1 chữ
    var best = 0;
    for (var i = 0; i < list.length; i++) {
      var w = list[i];
      if (w === t) return 1;
      if (best < 0.7 && w.lastIndexOf(t, 0) === 0) best = 0.7;
      else if (fuzzy && !best && t.length >= 4 && near1(t, w.slice(0, Math.max(t.length, Math.min(w.length, t.length + 1))))) best = 0.45;
    }
    return best;
  }
  function score(p, toks, phrase, fuzzy) {
    var s = 0, miss = 0, viaAlias = false;
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i], best = 0, f, v;
      for (f in W) {
        if (f === "x" && fuzzy) continue;  // không đoán sai chính tả trong mô tả (quá nhiễu)
        v = tokScore(t, p.w[f], fuzzy) * W[f];
        if (v > best) { best = v; if (f === "a" && v > tokScore(t, p.w.n, fuzzy) * W.n) viaAlias = true; }
      }
      if (!best) miss++; else s += best;
    }
    if (miss > (fuzzy && toks.length >= 3 ? 1 : 0)) return 0;
    // từ gõ đứng liền nhau đúng như trong tên / tên gọi khác ("đền hùng phú thọ": "den hung" ∈ "Đền Hùng")
    for (i = 0; i + 1 < toks.length; i++) {
      var bg = toks[i] + " " + toks[i + 1];
      if ((" " + p.s.n + " ").indexOf(" " + bg + " ") >= 0) s += 6;
      else if ((" " + p.s.a + " ").indexOf(" " + bg + " ") >= 0) s += 4;
    }
    if (p.s.pv && (" " + phrase + " ").indexOf(" " + p.s.pv + " ") >= 0) s += 12;  // gõ trọn tên tỉnh
    for (i = 0; i < p.it.length; i++) {  // gõ trọn một tên gọi khác / từ khoá ("chùa hương" → Chùa Thiên Trù)
      if (p.it[i].w.join(" ") === phrase) { s += 20; viaAlias = true; break; }
    }
    if (lowRaw && p.lo.indexOf(lowRaw) >= 0) s += 12;  // đúng cả dấu: "bái đính" > "Bai Dinh", "yên tử" > "Yên Từ"
    else if (lowRaw && p.loa.indexOf(lowRaw) >= 0) s += 8;
    if (p.s.n.indexOf(phrase) >= 0) s += p.s.n.lastIndexOf(phrase, 0) === 0 || p.s.n.indexOf(" " + phrase) >= 0 ? 40 : 25;
    else if (p.s.a.indexOf(phrase) >= 0) { s += 30; viaAlias = true; }
    else if (toks.length > 1 && p.s.x.indexOf(phrase) >= 0) s += 8;
    p.why = viaAlias ? whyItem(p, toks) : "";
    return s - miss * 15 + (p.b === 2 ? 3 : 0) + (p.pr ? (4 - p.pr) * 2 : 0) - p.w.n.length * 0.2;
  }
  function whyItem(p, toks) {  // cụm tên gọi khác / từ khoá khớp nhiều từ gõ nhất
    var best = null, bn = 0;
    p.it.forEach(function (o) {
      var c = 0; toks.forEach(function (t) { if (tokScore(t, o.w, false)) c++; });
      if (c > bn) { bn = c; best = o; }
    });
    return best ? best.l + ": " + best.t : "";
  }
  function filtered() {
    var raw = $("ld-q").value.trim(), toks = words(raw), phrase = toks.join(" ");
    lowRaw = raw.toLowerCase().normalize("NFC").replace(/\s+/g, " ");
    var k = $("ld-kind").value, pv = $("ld-prov").value, b = $("ld-book").checked, it = $("ld-intent").value;
    var base = all.filter(function (p) {
      return (!k || p.k === k) && (!pv || p.pv === pv) && (!b || p.b === 2) && (!it || p.it_.indexOf(it) >= 0);
    });
    if (!toks.length) {
      base.forEach(function (p) { p.why = ""; });
      // không gõ gì mà có lọc "cầu gì": nơi tiêu biểu (bậc 1 → 3) lên đầu
      return it ? base.sort(function (x, y) { return (x.pr || 9) - (y.pr || 9) || (x.n < y.n ? -1 : 1); }) : base;
    }
    function run(fuzzy, skip, out) {
      base.forEach(function (p) {
        if (skip[p.id]) return;
        var s = score(p, toks, phrase, fuzzy);
        if (s > 0) { p.sc = s + (fuzzy ? 0 : 100); out.push(p); }  // kết quả khớp chặt luôn đứng trước
      });
      return out;
    }
    var hits = run(false, {}, []);
    if (hits.length < 5) {
      var have = {}; hits.forEach(function (p) { have[p.id] = 1; });
      run(true, have, hits);
    }
    return hits.sort(function (x, y) { return y.sc - x.sc || (x.n < y.n ? -1 : 1); });
  }
  function active() {
    return $("ld-q").value.trim() || $("ld-kind").value || $("ld-prov").value || $("ld-intent").value || $("ld-book").checked || me;
  }

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
        (p.b === 2 ? ' <span class="ld-badge on">★ Nhận lễ</span>' : "") +
        (p.pr === 1 ? ' <span class="ld-badge warn">Tiêu biểu</span>' : "") +
        (p.why ? '<br><span class="small">' + esc(p.why) + "</span>"
          : (p.dt ? '<br><span class="small">Thờ: ' + esc(p.dt) + "</span>" : "")) +
        '<br><span class="ld-muted small">' + esc(kinds[p.k] || "") +
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
        var p = { id: a[0], lat: a[1], lng: a[2], k: a[3], n: a[4], pv: d.provinces[a[5]] || "", b: a[6] };
        var x = a[8] || "", al = a[7] || "", kw = a[9] || "", deity = a[10] || "";  // x đã bỏ dấu phía server
        p.it_ = a[11] ? a[11].split(",") : []; p.pr = a[12] || 0; p.aq = a[13] || ""; p.dt = deity;
        // tên gọi khác + từ khoá: từng cụm riêng, để hiện đúng cụm đã khớp dưới kết quả
        p.it = al.split(";").map(function (t) { return { t: t.trim(), l: "Còn gọi" }; })
          .concat(deity ? [{ t: deity, l: "Thờ" }] : [])
          .concat(kw.split(/[,;]/).map(function (t) { return { t: t.trim(), l: "Từ khoá" }; }))
          .filter(function (o) { return o.t; });
        p.it.forEach(function (o) { o.w = words(o.t); });
        p.w = { n: words(p.n), a: words(al + " " + deity + " " + kw), pv: words(p.pv + " " + (PV_ALIAS[p.pv] || "")), x: x ? x.split(" ") : [] };
        p.s = { n: p.w.n.join(" "), a: p.it.map(function (o) { return o.w.join(" "); }).join(" | "), x: x, pv: words(p.pv).join(" ") };
        p.lo = p.n.toLowerCase().normalize("NFC");
        p.loa = p.it.map(function (o) { return o.t.toLowerCase().normalize("NFC"); }).join(" | ");
        counts[p.k] = (counts[p.k] || 0) + 1; if (p.pv) provCounts[p.pv] = (provCounts[p.pv] || 0) + 1;
        return p;
      });
      Object.keys(kinds).forEach(function (k) {
        if (counts[k]) $("ld-kind").insertAdjacentHTML("beforeend", '<option value="' + k + '">' + esc(kinds[k]) + " (" + counts[k] + ")</option>");
      });
      var ic = {};
      all.forEach(function (p) { p.it_.forEach(function (c) { ic[c] = (ic[c] || 0) + 1; }); });
      Object.keys(d.intents || {}).forEach(function (c) {
        if (ic[c]) $("ld-intent").insertAdjacentHTML("beforeend", '<option value="' + c + '">Cầu ' + esc(d.intents[c].toLowerCase()) + " (" + ic[c] + ")</option>");
      });
      if (!Object.keys(ic).length) $("ld-intent").hidden = true;
      d.provinces.forEach(function (pv) {
        $("ld-prov").insertAdjacentHTML("beforeend", '<option value="' + esc(pv) + '">' + esc(pv) + " (" + provCounts[pv] + ")</option>");
      });
      return mapP;
    }).then(function (a) {
      adapter = a;
      var q = /[?&]q=([^&]+)/.exec(location.search);  // từ trang Thần thánh: "Tìm nơi thờ trên bản đồ"
      if (q) $("ld-q").value = decodeURIComponent(q[1].replace(/\+/g, " "));
      var pre = /[?&]cau=([a-z-]+)/.exec(location.search);  // từ trang chi tiết: "Thường cầu: Tài lộc"
      if (pre && $("ld-intent").querySelector('option[value="' + pre[1] + '"]')) { $("ld-intent").value = pre[1]; apply(true); return; }
      apply(false);
      var m = /^#p(\d+)$/.exec(location.hash);
      var target = m && all.filter(function (p) { return p.id === +m[1]; })[0];
      if (target && adapter) adapter.focus(target);
    });
    $("ld-q").addEventListener("input", schedule);
    ["ld-kind", "ld-prov", "ld-intent", "ld-book"].forEach(function (id) { $(id).addEventListener("change", function () { apply(true); }); });
    $("ld-near").addEventListener("click", locate);
    $("ld-list").addEventListener("click", function (e) {
      var b = e.target.closest("button[data-i]");
      if (b && adapter) { adapter.focus(lastList[+b.dataset.i]); $("ld-map").scrollIntoView({ behavior: "smooth", block: "center" }); }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
