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
