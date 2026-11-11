/* Thiết bị Linh Địa Việt chạy trên điện thoại Android: loa + camera + micro của máy.
   Giao tiếp: POST /api/device/poll (nhận việc), /api/device/ack, /api/device/evidence — cùng giao thức với Pi. */
(() => {
  const $ = (id) => document.getElementById(id);
  const base = location.pathname.replace(/\/may\/?$/, "");
  const VERSION = "phone-4";
  let cfg = null, stream = null, audioEl = null, actx = null, wakeLock = null;
  let offset = 0;                    // giờ server - giờ máy (ms): phát đúng giờ dù đồng hồ điện thoại lệch
  let current = null;                // job đang xử lý
  const queue = [], seen = new Set(JSON.parse(localStorage.getItem("ld_done") || "[]"));
  let locked = false, pollTimer = null;

  const sleep = (ms) => new Promise((r) => setTimeout(r, Math.max(0, ms)));
  const nowServer = () => Date.now() + offset;
  async function sleepUntilServer(ts) { while (nowServer() < ts) await sleep(Math.min(1000, ts - nowServer())); }
  const logBuf = [];                 // gửi kèm mỗi lần hỏi lệnh → admin/kỹ thuật xem được từ xa
  let step = "chờ lệnh";
  let record = localStorage.getItem("ld_record") !== "0";    // quay video mâm lễ (máy yếu có thể tắt)
  function log(msg, cls = "") {
    logBuf.push(new Date(nowServer()).toISOString().slice(11, 19) + " " + msg); if (logBuf.length > 20) logBuf.shift();
    const li = document.createElement("li");
    li.className = cls; li.textContent = new Date().toLocaleTimeString("vi-VN") + "  " + msg;
    $("log").prepend(li);
    while ($("log").children.length > 60) $("log").lastChild.remove();
  }
  function setState(txt, cls) { const e = $("state"); e.textContent = txt; e.className = "pill " + (cls || ""); }
  const headers = () => ({ Authorization: "Bearer " + cfg.token, "X-Device-Id": cfg.id });

  async function api(path, body, tries = 1) {
    for (let i = 0; i < tries; i++) {
      try {
        const r = await fetch(base + path, { method: "POST", headers: { ...headers(), "Content-Type": "application/json" },
                                             body: JSON.stringify(body || {}) });
        if (r.status === 401) { setState("Sai mã thiết bị", "bad"); throw new Error("401"); }
        if (r.ok) return await r.json();
      } catch (e) { if (String(e.message) === "401") throw e; }
      await sleep(1500 * (i + 1));
    }
    return null;
  }
  const ack = (job, state, detail) => api("/api/device/ack", { job_id: job.job_id, state, detail: detail || "", ts: new Date(nowServer()).toISOString() }, 6);

  async function upload(job, phase, blob, name) {
    for (let i = 0; i < 4; i++) {
      try {
        const fd = new FormData();
        fd.append("job_id", job ? job.job_id : ""); fd.append("phase", phase);
        fd.append("captured_at", new Date(nowServer()).toISOString()); fd.append("file", blob, name);
        const r = await fetch(base + "/api/device/evidence", { method: "POST", headers: headers(), body: fd });
        if (r.ok) return true;
        log(`Tải ${phase} lỗi ${r.status}`, "bad");
        if (r.status >= 400 && r.status < 500) return false;
      } catch (e) { /* mất mạng: thử lại */ }
      await sleep(2000 * (i + 1));
    }
    return false;
  }

  // Camera trên điện thoại hay "đứng hình" sau khi màn hình tắt / trang bị ẩn: track ended/muted hoặc khung hình
  // không chạy nữa (video giữ khung cuối → ảnh chụp lặp lại y hệt). Kiểm tra trước mỗi lần chụp/quay, hỏng thì mở lại.
  // camera sau ("environment") hoặc trước ("user"): chọn theo cách đặt máy trên giá; nhớ trong máy
  let facing = localStorage.getItem("ld_facing") || "environment";
  const media = () => ({ video: { facingMode: facing, width: { ideal: 1280 }, height: { ideal: 720 } },
                         audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
  let cameraOk = false;
  function streamDead() {
    const v = $("cam"), t = stream && stream.getVideoTracks()[0];
    return !t || t.readyState === "ended" || t.muted || v.paused || v.readyState < 2;
  }
  async function frameMoving(ms = 700) {
    const v = $("cam"), t0 = v.currentTime;
    await sleep(ms);
    return v.currentTime > t0;
  }
  async function openCamera() {
    if (stream) stream.getTracks().forEach((t) => t.stop());
    stream = await navigator.mediaDevices.getUserMedia(media());
    $("cam").srcObject = stream;
    await $("cam").play().catch(() => {});
  }
  async function setFacing(f) {
    if (f !== "user" && f !== "environment") return;
    facing = f; localStorage.setItem("ld_facing", f);
    if (current) { log("Đang có lễ — đổi camera sau khi xong", "bad"); return; }
    try { await openCamera(); cameraOk = true; log("Đã chuyển sang camera " + (f === "user" ? "trước" : "sau"), "ok"); }
    catch (e) { cameraOk = false; log("Không đổi được camera: " + e.message, "bad"); }
  }
  async function ensureCamera() {
    if (!streamDead() && (await frameMoving())) return (cameraOk = true);
    log("Camera đứng hình — mở lại", "bad");
    try {
      await openCamera();
      for (let i = 0; i < 10 && $("cam").readyState < 2; i++) await sleep(300);
      cameraOk = !streamDead() && (await frameMoving());
    } catch (e) { log("Không mở lại được camera: " + e.message, "bad"); cameraOk = false; }
    if (cameraOk) log("Camera đã chạy lại", "ok");
    return cameraOk;
  }

  function photo() {
    const v = $("cam");
    if (!v.videoWidth) return Promise.resolve(null);
    const c = document.createElement("canvas"); c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext("2d").drawImage(v, 0, 0);
    return new Promise((res) => c.toBlob(res, "image/jpeg", 0.82));
  }
  async function shoot(job, phase) {
    await ensureCamera();
    const b = await photo();
    if (!b) { log("Chưa có hình từ camera", "bad"); return; }
    if (await upload(job, phase, b, phase + ".jpg")) log("Đã chụp ảnh: " + phase);
  }

  function pickMime() {
    for (const m of ["video/mp4;codecs=avc1.42E01E,mp4a.40.2", "video/mp4", "video/webm;codecs=vp8,opus", "video/webm"])
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(m)) return m;
    return "";
  }
  async function startRecording() {
    if (!record) { log("Không quay video (đã tắt)"); return null; }
    if (!stream) { log("Không có camera để quay", "bad"); return null; }
    const mime = pickMime();
    if (!mime) { log("Trình duyệt không quay được video", "bad"); return null; }
    const track = stream.getVideoTracks()[0];
    try { await track.applyConstraints({ width: { ideal: 640 }, height: { ideal: 480 } }); } catch (e) { /* giữ nguyên */ }
    const chunks = [];
    const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 400000, audioBitsPerSecond: 48000 });
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    const done = new Promise((res) => (rec.onstop = () => res(new Blob(chunks, { type: mime.split(";")[0] }))));
    rec.start(1000);
    log("Bắt đầu quay video (" + mime.split(";")[0] + ")");
    const restore = () => track.applyConstraints({ width: { ideal: 1280 }, height: { ideal: 720 } }).catch(() => {});
    return { rec, done: done.then((b) => { restore(); return b; }), ext: mime.includes("mp4") ? "mp4" : "webm" };
  }

  async function sha256(buf) {
    const d = await crypto.subtle.digest("SHA-256", buf);
    return [...new Uint8Array(d)].map((x) => x.toString(16).padStart(2, "0")).join("");
  }

  async function runJob(job) {
    current = job;
    const cap = job.capture || {};
    const playAt = Date.parse(job.play_at);
    try {
      log("Nhận lệnh phát, giờ " + new Date(playAt).toLocaleTimeString("vi-VN"));
      await ack(job, "received");
      const r = await fetch(job.audio_url);
      if (!r.ok) throw new Error("Tải audio lỗi " + r.status);
      const buf = await r.arrayBuffer();
      if (job.sha256 && (await sha256(buf)) !== job.sha256) throw new Error("File âm thanh sai mã kiểm tra");
      await ack(job, "downloaded");
      if (nowServer() > playAt + 600000) throw new Error("Quá giờ hẹn, bỏ qua");
      const url = URL.createObjectURL(new Blob([buf], { type: "audio/mpeg" }));
      const before = (cap.before_s || 0) * 1000;
      if (before && nowServer() < playAt - before) { await sleepUntilServer(playAt - before); await shoot(job, "before"); }
      step = "kiểm tra camera";
      await sleepUntilServer(playAt - 4000);
      if (record) await ensureCamera();                       // quay bằng luồng camera còn sống
      audioEl.src = url; audioEl.load();                      // nạp sẵn để bấm phát là có tiếng ngay
      audioEl.volume = Math.min(1, (job.volume || 70) / 100);
      step = "chờ giờ phát";
      await sleepUntilServer(playAt);
      if (locked) throw new Error("Hệ thống đang khóa khẩn cấp");
      const ended = new Promise((res, rej) => { audioEl.onended = res; audioEl.onerror = () => rej(new Error("Loa không phát được")); });
      step = "bắt đầu phát";
      await audioEl.play();                                   // loa trước, quay sau: quay video không làm trễ giờ đọc
      setState("Đang đọc sớ", "ok"); log("ĐANG PHÁT bài khấn", "ok");
      ack(job, "playing");
      step = "đang phát";
      const recorder = await startRecording().catch((e) => { log("Không quay được: " + e.message, "bad"); return null; });
      sleep(2000).then(() => cap.at_start !== false && shoot(job, "start"));
      await ended;
      step = "gửi ảnh/video";
      log("Đọc xong", "ok"); setState("Sẵn sàng", "ok");
      ack(job, "done");
      await sleep((cap.after_s ?? 5) * 1000);
      await shoot(job, "after");
      if (recorder) {
        await sleep(3000); recorder.rec.stop();
        const blob = await recorder.done;
        if (blob.size > 1000 && (await upload(job, "video", blob, "mam-le." + recorder.ext))) log("Đã gửi video mâm lễ", "ok");
      }
      URL.revokeObjectURL(url);
    } catch (e) {
      log("Lỗi: " + e.message, "bad"); setState("Lỗi", "bad");
      await ack(job, "error", String(e.message).slice(0, 200));
    } finally {
      seen.add(job.job_id); localStorage.setItem("ld_done", JSON.stringify([...seen].slice(-100)));
      current = null; step = "chờ lệnh"; setState("Sẵn sàng", "ok");
    }
  }
  async function worker() {
    for (;;) { const j = queue.shift(); if (j) await runJob(j); else await sleep(500); }
  }

  function beep() {
    const o = actx.createOscillator(), g = actx.createGain();
    o.frequency.value = 660; g.gain.value = 0.3; o.connect(g); g.connect(actx.destination);
    o.start(); o.stop(actx.currentTime + 1.2);
  }
  function stopAudio() { try { audioEl.pause(); audioEl.dispatchEvent(new Event("ended")); } catch (e) { /* bỏ qua */ } }

  async function status() {
    let battery = null;
    try { const b = await navigator.getBattery(); battery = Math.round(b.level * 100); } catch (e) { /* không hỗ trợ */ }
    const c = navigator.connection || {};
    return { net: c.type === "cellular" ? "4g" : "wifi", rssi: null, version: VERSION, camera: cameraOk ? "phone" : "phone-loi", battery,
             clock_synced: true, clock_offset_ms: Math.round(offset), queue: queue.length + (current ? 1 : 0),
             step, record, log: logBuf.slice(-20) };
  }
  async function poll() {
    try {
      const t0 = Date.now();
      const res = await api("/api/device/poll", await status());
      if (!res) { setState("Mất kết nối server", "bad"); return; }
      offset = Date.parse(res.server_time) - (t0 + Date.now()) / 2;
      locked = res.locked;
      if (locked) { stopAudio(); setState("Khóa khẩn cấp", "bad"); }
      else if (!current) setState("Sẵn sàng", "ok");
      for (const id of res.cancel) {
        const i = queue.findIndex((j) => j.job_id === id);
        if (i >= 0) queue.splice(i, 1);
        if (current && current.job_id === id) stopAudio();
      }
      for (const c of res.control) {
        if (c.type === "stop") stopAudio();
        else if (c.type === "test_tone") { beep(); log("Phát âm thử"); }
        else if (c.type === "capture") shoot(null, "test");
        else if (c.type === "config") {
          if (c.camera) setFacing(c.camera);
          if (typeof c.record === "boolean") { record = c.record; localStorage.setItem("ld_record", record ? "1" : "0");
                                               log(record ? "Bật quay video" : "Tắt quay video", "ok"); }
        }
      }
      for (const j of res.jobs) {
        if (seen.has(j.job_id) || (current && current.job_id === j.job_id) || queue.some((q) => q.job_id === j.job_id)) continue;
        queue.push(j);
      }
      $("offset").textContent = `lệch giờ với server: ${Math.round(offset)} ms`;
    } catch (e) { /* 401 đã báo */ }
  }

  async function start() {
    cfg = { id: $("did").value.trim(), token: $("tok").value.trim() };
    if (!cfg.id || !cfg.token) { alert("Nhập mã thiết bị và token"); return; }
    localStorage.setItem("ld_phone", JSON.stringify(cfg));
    // mở khóa âm thanh NGAY trong lần chạm (trước hộp hỏi quyền camera — sau đó Chrome có thể không coi là thao tác người dùng)
    audioEl = new Audio(); audioEl.setAttribute("playsinline", "");
    actx = new (window.AudioContext || window.webkitAudioContext)();
    audioEl.src = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";
    const unlocked = audioEl.play().then(() => true).catch(() => false);
    actx.resume().catch(() => {});
    try { await openCamera(); cameraOk = true; } catch (e) {
      log("Không mở được camera/micro: " + e.message, "bad");
      stream = null;
    }
    if (!(await unlocked)) log("Chưa mở được âm thanh — chạm vào màn hình một lần", "bad");
    try { wakeLock = await navigator.wakeLock.request("screen"); } catch (e) { log("Không giữ được màn hình sáng — hãy tắt tự khóa màn hình", "bad"); }
    document.addEventListener("visibilitychange", async () => {
      if (document.visibilityState !== "visible") return;
      try { wakeLock = await navigator.wakeLock.request("screen"); } catch (e) { /* bỏ qua */ }
      if (!current) ensureCamera();                           // quay lại trang: khôi phục camera nếu đã dừng
    });
    $("setup").hidden = true; $("run").hidden = false;
    log("Đã bật. Giữ trang này mở, cắm sạc và để màn hình sáng.", "ok");
    setState("Sẵn sàng", "ok");
    await poll(); pollTimer = setInterval(poll, 3000); worker();
  }

  window.addEventListener("DOMContentLoaded", () => {
    const h = new URLSearchParams(location.hash.slice(1));
    let saved = {}; try { saved = JSON.parse(localStorage.getItem("ld_phone") || "{}"); } catch (e) { /* bỏ qua */ }
    $("did").value = h.get("id") || saved.id || ""; $("tok").value = h.get("token") || saved.token || "";
    if (h.get("cam") === "user" || h.get("cam") === "environment") { facing = h.get("cam"); localStorage.setItem("ld_facing", facing); }
    if (h.get("rec") === "0" || h.get("rec") === "1") { record = h.get("rec") === "1"; localStorage.setItem("ld_record", h.get("rec")); }
    $("flip").addEventListener("click", () => setFacing(facing === "user" ? "environment" : "user"));
    if (location.hash) history.replaceState(null, "", location.pathname);   // không để token trên thanh địa chỉ
    $("go").addEventListener("click", start);
  });
})();
