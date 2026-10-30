// Quay video demo quy trình khách hàng trên production (khổ điện thoại), kèm phụ đề + vòng chạm.
// Ghi mốc thời gian đoạn chờ Pi đọc sớ để tua nhanh khi dựng (xem build.sh).
const { chromium } = require("playwright");
const fs = require("fs");

const BASE = "https://tuandv.id.vn/le-chua";
const OUT = __dirname + "/out";
const W = 540, H = 1170;
const LOGIN = process.env.LD_LOGIN || "";  // "email:mật khẩu"
// LD_ITEMS="Hương (nhang)=1;Hoa quả=3" — lễ vật đúng như mâm đang bày trước camera
const ITEMS = (process.env.LD_ITEMS || "Hương (nhang)=3;Nến=1;Hoa tươi=1;Ngũ quả=1;Xôi gấc=2;Gà luộc=1")
  .split(";").map(x => x.split("=")).map(([n, q]) => [n.trim(), +q]);

const OVERLAY = `
(() => {
  const css = \`
  #demo-cap{position:fixed;left:12px;right:12px;bottom:14px;z-index:99999;background:rgba(40,12,12,.92);color:#fff;
    font:600 17px/1.35 system-ui,-apple-system,sans-serif;padding:12px 14px;border-radius:14px;box-shadow:0 6px 24px rgba(0,0,0,.35);
    border-left:5px solid #e0a83a;transition:opacity .3s}
  #demo-cap small{display:block;font-weight:400;font-size:14px;opacity:.85;margin-top:3px}
  .demo-tap{position:fixed;z-index:99998;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;
    background:rgba(224,168,58,.45);border:3px solid #e0a83a;pointer-events:none;animation:demotap .6s ease-out forwards}
  @keyframes demotap{from{transform:scale(.4);opacity:1}to{transform:scale(1.4);opacity:0}}\`;
  const add = () => {
    if (document.getElementById("demo-style")) return;
    const s = document.createElement("style"); s.id = "demo-style"; s.textContent = css; document.head.appendChild(s);
    const saved = sessionStorage.getItem("demo-cap");
    if (saved) window.__cap(...JSON.parse(saved));
  };
  window.__cap = (title, sub) => {
    sessionStorage.setItem("demo-cap", JSON.stringify([title, sub || ""]));
    let el = document.getElementById("demo-cap");
    if (!el) { el = document.createElement("div"); el.id = "demo-cap"; document.body.appendChild(el); }
    el.innerHTML = title + (sub ? "<small>" + sub + "</small>" : "");
  };
  document.addEventListener("pointerdown", e => {
    const d = document.createElement("div"); d.className = "demo-tap";
    d.style.left = e.clientX + "px"; d.style.top = e.clientY + "px";
    document.body.appendChild(d); setTimeout(() => d.remove(), 700);
  }, true);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", add); else add();
})();`;

const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();  // Chrome thật quay bị dải xám dưới đáy → dùng Chromium (không phát H.264)
  const ctx = await browser.newContext({
    viewport: { width: W, height: H }, deviceScaleFactor: 1, locale: "vi-VN",
    timezoneId: "Asia/Ho_Chi_Minh", recordVideo: { dir: OUT, size: { width: W, height: H } },
  });
  const t0 = Date.now();
  const mark = {};
  await ctx.addInitScript(OVERLAY);
  const page = await ctx.newPage();
  page.setDefaultTimeout(60000);
  const cap = (t, s) => page.evaluate(([t, s]) => window.__cap(t, s), [t, s]);
  const type = async (sel, text) => { await page.click(sel); await page.type(sel, text, { delay: 55 }); await sleep(250); };
  const scrollTo = async (sel) => { await page.locator(sel).first().scrollIntoViewIfNeeded(); await sleep(700); };

  // 1–2. Tài khoản: LD_LOGIN="email:mật khẩu" → đăng nhập tài khoản có sẵn (đã có hồ sơ + thẻ); không thì đăng ký mới
  let email;
  if (LOGIN) {
    email = LOGIN.slice(0, LOGIN.indexOf(":"));
    await page.goto(BASE + "/dang-nhap");
    await cap("Bước 1 · Đăng nhập", "Khách đã có tài khoản: hồ sơ tín chủ và thẻ thanh toán lưu sẵn");
    await sleep(1500);
    await type("#i1", email);
    await type("#p1", LOGIN.slice(LOGIN.indexOf(":") + 1));
    await page.click("button:has-text('Đăng nhập')");
    await page.waitForURL(u => !/dang-nhap/.test(u.toString()));
  } else {
    // 1. Đăng ký
    await page.goto(BASE + "/dang-ky");
    await cap("Bước 1 · Đăng ký tài khoản", "Họ tên, ngày sinh, địa chỉ — đủ để lập tờ sớ, chỉ nhập một lần");
    await sleep(1500);
    await type("#n", "Nguyễn Văn An");
    await page.fill("#ns", "1985-03-12"); await sleep(600);
    await type("#dc", "Cầu Giấy, Hà Nội");
    email = "khach-" + Math.random().toString(16).slice(2, 8) + "@example.com";
    await type("#i", email);
    await type("#p", "demo-password");
    await sleep(600);
    await page.click("button:has-text('Tiếp tục')");

    // 2. Thẻ
    await page.waitForURL(/tai-khoan\/the/);
    await cap("Bước 2 · Liên kết thẻ thanh toán", "Bản thử nghiệm: thẻ giả lập, không trừ tiền thật");
    await sleep(1500);
    await type("#so_the", "4242 4242 4242 4242");
    await type("#het_han", "12/28");
    await type("#cvc", "123");
    await sleep(500);
    await page.click("button:has-text('Liên kết thẻ')");
  }

  // 3. Chọn đền
  await page.waitForURL(u => !/tai-khoan/.test(u.toString()));
  await cap("Bước 3 · Chọn đền, chùa", "Đền có thiết bị tại chỗ sẽ hiện “trực tuyến”");
  await sleep(2200);
  await page.click("text=Đền Ngọc Sơn");
  await page.waitForURL(/den-ngoc-son/);
  await cap("Bước 3 · Đền Ngọc Sơn", "Bảng giá lễ vật bán lẻ tại đền");
  await sleep(1500);
  await page.mouse.wheel(0, 500); await sleep(1500);
  await page.mouse.wheel(0, 500); await sleep(1200);
  await page.click("text=Sắm lễ và đặt lễ");

  // 4. Lễ vật
  await page.waitForURL(/dat-le/);
  await cap("Bước 4 · Sắm lễ vật", "Bấm + / − chọn số lượng từng món, tạm tính tự cộng");
  await sleep(1200);
  for (const [name, n] of ITEMS) {
    const row = page.locator(".ld-item", { has: page.locator(`b:text-is("${name}")`) });
    await row.scrollIntoViewIfNeeded(); await sleep(300);
    for (let i = 0; i < n; i++) { await row.locator("[data-step='1']").click(); await sleep(420); }
  }
  await scrollTo("#items-total"); await sleep(1500);

  // 5. Dâng sớ
  await scrollTo("#nguyen_vong");
  await cap("Bước 5 · Dâng sớ", "Viết nguyện vọng — tờ sớ tự soạn theo tín chủ, đền và lễ vật đã chọn");
  await page.fill("#nguyen_vong", "");
  await type("#nguyen_vong", "gia đình con được mạnh khỏe, bình an, công việc hanh thông");
  await page.locator("#nguyen_vong").blur();
  await page.waitForFunction(() => (document.getElementById("van_ban").value || "").includes("hanh thông"), null, { timeout: 30000 });
  await scrollTo("#van_ban");
  await sleep(1500);
  await page.locator("#van_ban").evaluate(el => el.scrollTop = el.scrollHeight / 2); await sleep(1500);
  await page.locator("#van_ban").evaluate(el => el.scrollTop = el.scrollHeight); await sleep(1500);
  await cap("Bước 5 · Ai đọc sớ?", "Giọng đọc tự động — hoặc tự đọc và ghi âm");
  await scrollTo("input[name=cach_khan][value=tts]"); await sleep(1800);

  // 6. Khi nào đọc
  await scrollTo("input[name=khi_nao][value=ngay]");
  await cap("Bước 6 · Khi nào đọc", "Đọc ngay khi mâm lễ bày xong — hoặc hẹn giờ (có ngày âm lịch)");
  await page.click("input[name=khi_nao][value=hen_gio]"); await sleep(1500);
  await page.click("input[name=khi_nao][value=ngay]"); await sleep(1500);

  // 7. Chốt
  await scrollTo("#btn-submit");
  await cap("Bước 7 · Chốt lễ", "Trừ tiền vào thẻ đã liên kết — không phải qua trang thanh toán");
  await sleep(2200);
  await page.click("#btn-submit");
  await page.waitForURL(/\/don\?moi=/);
  await cap("Lịch sử lễ", "Đơn vừa chốt nằm ở đầu danh sách");
  await sleep(2500);
  await page.click("a.ld-hist.new");
  await page.waitForURL(/\/don\/\d+$/);
  const orderUrl = page.url();
  await cap("Bước 8 · Thiết bị tại đền nhận lệnh và đọc sớ", "Trạng thái cập nhật trực tiếp: xếp lịch → nhận lệnh → đang đọc → ảnh mâm lễ");
  await sleep(4000);
  await page.mouse.wheel(0, 250);
  mark.waitStart = (Date.now() - t0) / 1000;
  await page.waitForFunction(() => /Hoàn tất/.test(document.querySelector("#status .ld-badge")?.textContent || ""),
                             null, { timeout: 420000, polling: 1000 });
  mark.waitEnd = (Date.now() - t0) / 1000;
  await sleep(2500);

  // 9. Xem lại
  await page.request.get(orderUrl + "/clip", { timeout: 180000 });  // dựng clip trước để không phải chờ
  await page.reload();
  for (let i = 0; i < 30 && !(await page.locator(".ld-check-card").count()); i++) {  // AI nhận diện ảnh lúc khấn (≤ ~5 phút)
    await sleep(10000); await page.reload();
  }
  mark.waitEnd = (Date.now() - t0) / 1000;  // đoạn chờ nhận diện cũng tua nhanh
  await cap("Bước 9 · Kiểm tra mâm lễ", "Camera + AI đếm từng lễ vật, đối chiếu với đơn: đủ / thiếu / thừa");
  await scrollTo(".ld-check-card"); await sleep(4000);
  await cap("Bước 9 · Video tại đền", "Quay mâm lễ kèm tiếng đọc sớ thu tại chỗ — bật tiếng để nghe");
  await scrollTo("video.ld-clip"); await sleep(1500);
  await sleep(3500);  // clip có tiếng được ghép vào cuối video demo
  await scrollTo(".ld-photos"); await sleep(2500);
  await page.click("text=Lịch sử lễ");
  await page.waitForURL(/\/don$/);
  await cap("Lịch sử lễ", "Mọi lễ đã đặt — bấm vào để xem lại bất cứ lúc nào");
  await sleep(3500);

  const clip = await page.request.get(orderUrl + "/clip");
  fs.writeFileSync(OUT + "/clip.mp4", await clip.body());
  const video = page.video();
  await ctx.close();
  await browser.close();
  fs.renameSync(await video.path(), OUT + "/screen.webm");
  fs.writeFileSync(OUT + "/marks.json", JSON.stringify({ ...mark, order: orderUrl, email, login: !!LOGIN }, null, 1));
  console.log(JSON.stringify({ ...mark, order: orderUrl, email }));
})().catch(e => { console.error(e); process.exit(1); });
