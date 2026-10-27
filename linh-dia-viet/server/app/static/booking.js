// Trang đặt lễ: xem trước sớ, nghe thử TTS, ghi âm (MediaRecorder), hiển thị ngày âm, gửi form.
(function () {
  var form = document.getElementById("booking");
  if (!form) return;
  var csrf = document.querySelector('meta[name="csrf-token"]').content;
  var $ = function (id) { return document.getElementById(id); };
  var errBox = $("form-error");

  function showError(msg) {
    errBox.textContent = msg || "";
    errBox.hidden = !msg;
    if (msg) errBox.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function post(url, body) {
    return fetch(url, { method: "POST", body: body, headers: { "X-CSRF-Token": csrf }, credentials: "same-origin" })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) throw new Error(j.error || j.detail || "Có lỗi xảy ra (" + r.status + ")");
          return j;
        });
      });
  }

  // ---- Chọn nhiều đền ----
  var maxTemples = parseInt(form.dataset.maxTemples, 10) || 100;
  var boxes = function () { return Array.prototype.slice.call(form.querySelectorAll("input[name=den][data-ok]")); };
  function syncTemples() {
    if (!$("temple-count")) return;  // đền đã chọn sẵn từ ngoài
    var n = boxes().filter(function (b) { return b.checked; }).length;
    $("temple-count").textContent = n + " đền";
    boxes().forEach(function (b) { if (!b.checked) b.disabled = n >= maxTemples; });
  }
  form.addEventListener("change", function (e) { if (e.target.name === "den") syncTemples(); });
  $("btn-all") && $("btn-all").addEventListener("click", function () {
    var all = boxes(), on = !all.every(function (b) { return b.checked; });
    all.slice(0, maxTemples).forEach(function (b) { b.checked = on; });
    if (!on) all.forEach(function (b) { b.checked = false; });
    syncTemples();
    all[0] && all[0].dispatchEvent(new Event("change", { bubbles: true }));
  });
  syncTemples();

  // ---- Lễ vật: nút −/+ và tạm tính ----
  function syncItems() {
    var total = 0;
    form.querySelectorAll(".ld-stepper").forEach(function (st) {
      var inp = st.querySelector("input");
      total += (parseInt(inp.value, 10) || 0) * parseInt(st.dataset.price, 10);
    });
    var el = $("items-total");
    if (el) el.textContent = (total * (parseInt(el.dataset.temples, 10) || 1)).toLocaleString("vi-VN") + " ₫";
  }
  form.addEventListener("click", function (e) {
    var b = e.target.closest("[data-step]");
    if (!b) return;
    var inp = b.parentNode.querySelector("input");
    var v = (parseInt(inp.value, 10) || 0) + parseInt(b.dataset.step, 10);
    inp.value = Math.max(0, Math.min(parseInt(inp.max, 10) || 99, v));
    inp.dispatchEvent(new Event("change", { bubbles: true }));
  });
  var itemTimer = null;
  form.addEventListener("change", function (e) {
    if (!/^sl_/.test(e.target.name || "")) return;
    syncItems();
    clearTimeout(itemTimer);  // bấm +/− liên tục: soạn lại sớ một lần sau khi dừng tay
    itemTimer = setTimeout(autoPreview, 600);
  });
  document.body.addEventListener("htmx:afterSwap", syncItems);
  syncItems();

  // ---- Cách khấn ----
  function syncKind() {
    var kind = form.querySelector('[name=cach_khan]:checked').value;
    $("tts-box").hidden = kind !== "tts";
    $("rec-box").hidden = kind !== "recorded";
    $("so-hint-tts").hidden = kind !== "tts";
    $("so-hint-rec").hidden = kind !== "recorded";
  }
  form.querySelectorAll("[name=cach_khan]").forEach(function (r) { r.addEventListener("change", syncKind); });
  syncKind();

  // ---- Phát ngay / hẹn giờ ----
  form.querySelectorAll("[name=khi_nao]").forEach(function (r) {
    r.addEventListener("change", function () {
      $("hen-gio").hidden = form.querySelector("[name=khi_nao]:checked").value !== "hen_gio";
      autoPreview();
    });
  });

  // ---- Sửa thông tin tín chủ ----
  $("btn-edit-info") && $("btn-edit-info").addEventListener("click", function () {
    $("info-fields").hidden = false;
    $("info-summary").hidden = true;
    this.hidden = true;
  });

  // ---- Ngày âm lịch ----
  $("thoi_gian").addEventListener("change", function () {
    var v = this.value;
    if (!v) { $("am-lich").textContent = ""; return; }
    fetch(form.dataset.lunar + "?ngay=" + encodeURIComponent(v.slice(0, 10)), { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) { $("am-lich").textContent = j.text ? "Âm lịch: " + j.text : ""; });
  });

  // ---- Xem trước sớ ----
  var edited = false;
  $("van_ban").addEventListener("input", function () { edited = true; });
  function preview(force) {
    if (edited && !force) return Promise.resolve();
    showError("");
    return post(form.dataset.preview, new FormData(form)).then(function (j) {
      $("van_ban").value = j.text;
      $("van_ban_goc").value = j.text;
      $("multi-note").hidden = !j.multi;
      edited = false;
    }).catch(function (e) { showError(e.message); });
  }
  $("btn-preview").addEventListener("click", function () {
    if (edited && !confirm("Soạn lại sẽ xoá phần bạn đã sửa. Tiếp tục?")) return;
    preview(true);
  });
  // Tự soạn sớ: khi mở trang, khi đổi đền/gói/thông tin (nếu người dùng chưa sửa tay)
  function autoPreview() {
    var has = Array.prototype.some.call(form.querySelectorAll("input[name=den]"),
      function (i) { return i.type === "hidden" || i.checked; });
    if (has) preview(false);
  }
  ["ho_ten", "nam_sinh", "dia_chi", "nguyen_vong", "thoi_gian"].forEach(function (id) {
    $(id).addEventListener("change", autoPreview);
  });
  form.addEventListener("change", function (e) { if (e.target.name === "den") autoPreview(); });
  document.body.addEventListener("htmx:afterSwap", autoPreview);
  if (!$("van_ban").value) autoPreview();

  // ---- Nghe thử ----
  $("btn-listen").addEventListener("click", function () {
    var btn = this;
    var fd = new FormData();
    fd.append("van_ban", $("van_ban").value);
    btn.disabled = true;
    btn.textContent = "Đang tạo giọng đọc…";
    post(form.dataset.tts, fd).then(function (j) {
      var a = $("tts-audio");
      a.src = j.url;
      a.hidden = false;
      a.play().catch(function () {});
    }).catch(function (e) { showError(e.message); })
      .finally(function () { btn.disabled = false; btn.textContent = "▶ Nghe thử giọng đọc"; });
  });

  // ---- Ghi âm ----
  var maxSec = parseInt(form.dataset.maxSeconds, 10) || 300;
  var rec = null, chunks = [], timer = null, started = 0, lastBlob = null;
  function fmt(s) { s = Math.floor(s); return String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0"); }

  function upload(blob, name) {
    var fd = new FormData();
    fd.append("file", blob, name);
    $("rec-status").textContent = "Đang tải lên và chuẩn hoá âm thanh…";
    return post(form.dataset.upload, fd).then(function (j) {
      $("ghi_am").value = j.key;
      $("rec-status").textContent = "Đã lưu bản ghi (" + fmt(j.seconds) + ").";
      $("rec-audio").src = j.url;
      $("rec-audio").hidden = false;
      $("btn-rec-upload").hidden = true;
    }).catch(function (e) { $("rec-status").textContent = ""; showError(e.message); });
  }

  function stopRec() { if (rec && rec.state === "recording") rec.stop(); }

  $("btn-rec").addEventListener("click", function () {
    var btn = this;
    if (rec && rec.state === "recording") { stopRec(); return; }
    if (!navigator.mediaDevices || !window.MediaRecorder) { showError("Trình duyệt không hỗ trợ ghi âm, hãy tải file lên."); return; }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      chunks = [];
      rec = new MediaRecorder(stream);
      rec.ondataavailable = function (e) { if (e.data.size) chunks.push(e.data); };
      rec.onstop = function () {
        clearInterval(timer);
        stream.getTracks().forEach(function (t) { t.stop(); });
        lastBlob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
        $("rec-audio").src = URL.createObjectURL(lastBlob);
        $("rec-audio").hidden = false;
        $("btn-rec-upload").hidden = false;
        btn.textContent = "● Ghi lại";
      };
      rec.start(1000);
      started = Date.now();
      btn.textContent = "■ Dừng";
      $("ghi_am").value = "";
      $("rec-status").textContent = "Đang ghi âm…";
      timer = setInterval(function () {
        var s = (Date.now() - started) / 1000;
        $("rec-time").textContent = fmt(s);
        if (s >= maxSec) stopRec();
      }, 250);
    }).catch(function () { showError("Không truy cập được micro. Hãy cấp quyền hoặc tải file lên."); });
  });

  $("btn-rec-upload").addEventListener("click", function () {
    if (lastBlob) upload(lastBlob, "ghi-am." + ((lastBlob.type.indexOf("mp4") >= 0) ? "m4a" : "webm"));
  });
  $("rec-file").addEventListener("change", function () {
    if (this.files[0]) upload(this.files[0], this.files[0].name);
  });

  // ---- Gửi form ----
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    showError("");
    var kind = form.querySelector("[name=cach_khan]:checked").value;
    var go = function () {
      return post(form.action, new FormData(form)).then(function (j) { window.location = j.redirect; });
    };
    var p = !$("van_ban").value ? preview(true).then(go) : go();
    p.catch(function (err) { showError(err.message); });
  });
})();
