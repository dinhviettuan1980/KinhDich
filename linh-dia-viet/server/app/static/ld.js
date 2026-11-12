// Gắn CSRF token vào mọi request HTMX.
document.addEventListener("htmx:configRequest", function (e) {
  var m = document.querySelector('meta[name="csrf-token"]');
  if (m) e.detail.headers["X-CSRF-Token"] = m.content;
});

// App trên điện thoại (PWA): gợi ý "Thêm vào Màn hình chính" khi mở bằng Safari iPhone mà chưa cài.
(function () {
  var standalone = window.navigator.standalone || window.matchMedia("(display-mode: standalone)").matches;
  if (standalone) document.documentElement.classList.add("ld-app");
  var ios = /iPhone|iPad|iPod/.test(navigator.userAgent) && !/CriOS|FxiOS|EdgiOS/.test(navigator.userAgent);
  var off = false;
  try { off = localStorage.getItem("ld-install-off") === "1"; } catch (e) {}
  if (ios && !standalone && !off) {
    document.addEventListener("DOMContentLoaded", function () {
      var b = document.getElementById("ld-install");
      if (b) b.hidden = false;
    });
  }
})();

// Trang chủ: lọc đền theo nhu cầu (bấm lại để bỏ) và "Gần tôi" (vị trí lấy từ trình duyệt, chỉ gửi lên để sắp xếp).
document.addEventListener("click", function (e) {
  var form = document.getElementById("find");
  if (!form) return;
  var chip = e.target.closest("[data-nhu-cau]");
  if (chip) {
    var box = document.getElementById("nhu_cau"), on = box.value !== chip.dataset.nhuCau;
    box.value = on ? chip.dataset.nhuCau : "";
    form.querySelectorAll("[data-nhu-cau]").forEach(function (c) { c.classList.toggle("on", on && c === chip); });
    form.requestSubmit();
  }
  if (e.target.id === "near-me") {
    var note = document.getElementById("near-note");
    if (!navigator.geolocation) { note.textContent = "Trình duyệt không hỗ trợ định vị."; return; }
    note.textContent = "Đang lấy vị trí…";
    navigator.geolocation.getCurrentPosition(function (p) {
      document.getElementById("lat").value = p.coords.latitude.toFixed(4);
      document.getElementById("lng").value = p.coords.longitude.toFixed(4);
      note.textContent = "Đang sắp xếp theo khoảng cách tới bạn.";
      form.requestSubmit();
    }, function () { note.textContent = "Không lấy được vị trí — hãy cho phép định vị."; }, { timeout: 10000 });
  }
});
