// Quay màn hình app THẬT (server giả lập :8100) theo từng vai, ghi mốc thời gian từng câu thoại để dựng phim.
const { chromium } = require(require("path").join(__dirname, "../../playwright/node_modules/playwright"));
const fs = require("fs");

const BASE = "http://127.0.0.1:8100/le-chua";
const D = __dirname;
const OUT = D + "/seg";
const W = 540, H = 1170;
const DUR = JSON.parse(fs.readFileSync(D + "/durations.json"));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const TAP = `document.addEventListener("pointerdown", e => {
  const d = document.createElement("div");
  d.style.cssText = "position:fixed;z-index:99999;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;" +
    "background:rgba(224,168,58,.45);border:3px solid #e0a83a;pointer-events:none;transition:all .6s;left:" + e.clientX + "px;top:" + e.clientY + "px";
  document.body.appendChild(d); requestAnimationFrame(() => { d.style.transform = "scale(1.5)"; d.style.opacity = 0; });
  setTimeout(() => d.remove(), 700); }, true);`;

let browser;
const marks = {};

async function segment(name, who, fn) {
  const ctx = await browser.newContext({
    viewport: { width: W, height: H }, deviceScaleFactor: 1, locale: "vi-VN", timezoneId: "Asia/Ho_Chi_Minh",
    geolocation: { latitude: 21.0333, longitude: 105.79 }, permissions: ["geolocation"],
    recordVideo: { dir: OUT + "/" + name, size: { width: W, height: H } },
  });
  await ctx.addInitScript(TAP);
  const page = await ctx.newPage();
  page.setDefaultTimeout(90000);
  page.on("dialog", d => d.accept());
  const t0 = Date.now();
  const m = marks[name] = { who, lines: [], marks: {} };
  const say = async (id, extra = 300) => { m.lines.push([id, (Date.now() - t0) / 1000]); await sleep(DUR[id] * 1000 + extra); };
  const mark = k => { m.marks[k] = (Date.now() - t0) / 1000; };
  const type = async (sel, text) => { await page.click(sel); await page.type(sel, text, { delay: 45 }); };
  const login = async (email, pw) => {
    await page.goto(BASE + "/dang-nhap");
    await type("#i1", email); await type("#p1", pw);
    await page.click("button:has-text('Đăng nhập')");
    await page.waitForURL(u => !/dang-nhap/.test(u.toString()));
  };
  await fn({ page, say, mark, type, login });
  m.end = (Date.now() - t0) / 1000;
  const video = page.video();
  await ctx.close();
  fs.renameSync(await video.path(), OUT + "/" + name + ".webm");
  fs.writeFileSync(D + "/marks.json", JSON.stringify(marks, null, 1));
  console.log("xong cảnh", name, m.end.toFixed(1), "s");
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  browser = await chromium.launch();
  let groupUrl;

  // ---- 1. Khách: tìm đền cầu may mắn, chọn 3/9 đền, sắm lễ, hẹn giờ, chốt ----
  await segment("khach1", "khach", async ({ page, say, login }) => {
    await login("demo-an@example.com", "demo-password");
    await page.goto(BASE + "/");
    await say("k1");
    await page.click("[data-nhu-cau='may-man']");
    await page.waitForSelector("#found");
    await say("k2", 0);
    await page.mouse.wheel(0, 900); await sleep(1200); await page.mouse.wheel(0, -900); await sleep(600);
    await page.click("#near-me");
    await page.waitForFunction(() => document.querySelectorAll(".ld-dist").length > 0);
    await page.locator("#found").scrollIntoViewIfNeeded();
    await say("k3", 0);
    // bấm vào 1 đền: bản đồ bay từ vị trí khách tới đền + giới thiệu, rồi quay lại danh sách
    await page.locator("h3 a", { hasText: "Phủ Tây Hồ" }).click();
    await page.waitForURL(/\/den\/phu-tay-ho/);
    await page.locator("#ld-gmap").scrollIntoViewIfNeeded();
    await say("k3b", 1500);
    await page.locator("#gioi-thieu").scrollIntoViewIfNeeded();
    await say("k3c", 600);
    await page.goBack();
    await page.waitForSelector(".ld-dist");
    await sleep(800);
    await page.mouse.wheel(0, 500); await sleep(1500);
    for (const name of ["Phủ Tây Hồ", "Chùa Trấn Quốc", "Đền Ngọc Sơn"]) {
      const card = page.locator(".ld-card", { has: page.locator(`h3:has-text("${name}")`) });
      await card.scrollIntoViewIfNeeded(); await sleep(500);
      await card.locator("input[name=den]").check(); await sleep(700);
    }
    await say("k4", 0);
    await page.click("#btn-book");
    await page.waitForURL(/dat-le/);
    await sleep(1200);
    for (const [name, n] of [["Hương (nhang)", 1], ["Hoa tươi", 1], ["Ngũ quả", 1], ["Gà luộc", 1]]) {
      const row = page.locator("#packages > .ld-item", { has: page.locator(`b:text-is("${name}")`) });
      await row.scrollIntoViewIfNeeded(); await sleep(250);
      for (let i = 0; i < n; i++) { await row.locator("[data-step='1']").click(); await sleep(400); }
    }
    await page.locator(".ld-mam-card").first().scrollIntoViewIfNeeded();
    await say("k5", 0);
    await page.fill("#nguyen_vong", "");
    await page.type("#nguyen_vong", "gia đình con năm mới may mắn, bình an, công việc hanh thông", { delay: 30 });
    await page.locator("#nguyen_vong").blur();
    await page.waitForFunction(() => (document.getElementById("van_ban").value || "").includes("hanh thông"));
    await page.locator("#van_ban").scrollIntoViewIfNeeded();
    await page.locator("#van_ban").evaluate(el => el.scrollTop = el.scrollHeight / 3);
    await say("k6", 0);
    await page.click("input[name=khi_nao][value=hen_gio]");
    const at = new Date(Date.now() + 4.5 * 60000); at.setSeconds(0, 0); at.setMinutes(at.getMinutes() + 1);
    const pad = x => String(x).padStart(2, "0");
    const v = `${at.getFullYear()}-${pad(at.getMonth() + 1)}-${pad(at.getDate())}T${pad(at.getHours())}:${pad(at.getMinutes())}`;
    await page.fill("#thoi_gian", v); await page.locator("#thoi_gian").dispatchEvent("change");
    marks.playAt = at.getTime() / 1000;
    await sleep(1500);
    await page.locator("#btn-submit").scrollIntoViewIfNeeded(); await sleep(1500);
    await page.click("#btn-submit");
    await page.waitForURL(/\/don\?moi=/);
    await sleep(1500);
    const ref = new URL(page.url()).searchParams.get("moi");
    groupUrl = BASE + "/don/lo/" + ref;
    marks.ref = ref;
    await page.goto(groupUrl);
    await say("k7", 800);
  });

  // ---- 2. Thủ nhang: lịch lễ của đền, không thấy dữ liệu khách, từ chối đơn sáng mai ----
  await segment("thu_nhang", "thu_nhang", async ({ page, say, login }) => {
    await login("quanly@example.com", "demo12345");
    await page.goto(BASE + "/admin/lich-le");
    await say("t1");
    await say("t2");
    const form = page.locator("form[action*='tu-choi']").first();
    await form.scrollIntoViewIfNeeded();
    await form.locator("input[name=ly_do]").type("Sáng mai đền đóng cửa làm lễ riêng", { delay: 40 });
    await say("t3", 0);
    await form.locator("button").click();
    await page.waitForLoadState(); await sleep(2500);
  });

  // ---- 3. Kiosk: bày mâm ----
  await segment("kiosk", "kiosk", async ({ page, say, login }) => {
    await login("kiosk@example.com", "demo12345");
    await page.goto(BASE + "/admin/lich-le");
    await say("ki1");
    await page.locator("form[action*='mam-le'] button").first().scrollIntoViewIfNeeded();
    await say("ki2", 0);
    await page.locator("form[action*='mam-le'] button").first().click();
    await page.waitForLoadState(); await sleep(2500);
  });

  // ---- 4. Khách theo dõi trang "Lễ đồng thời" tới khi 3 đền xong ----
  await segment("cho_le", "khach", async ({ page, mark, login }) => {
    await login("demo-an@example.com", "demo-password");
    await page.goto(groupUrl);
    await sleep(3000);
    mark("waitStart");
    await page.waitForFunction(() => /đồng thời tại/.test(document.body.innerText), null, { timeout: 900000, polling: 1000 });
    mark("played");
    await page.waitForFunction(() => document.querySelectorAll("#grp video").length >= 3, null, { timeout: 900000, polling: 2000 });
    mark("waitEnd");
    await sleep(5000);
  });

  // ---- 5. Kiosk + thủ nhang nhận cảnh báo mâm lễ thiếu ----
  await segment("canh_bao", "kiosk", async ({ page, say, login }) => {
    await login("kiosk@example.com", "demo12345");
    for (let i = 0; i < 40; i++) {
      await page.goto(BASE + "/admin");
      if (await page.locator(".ld-flash.error", { hasText: "Mâm lễ" }).count()) break;
      await sleep(5000);
    }
    await say("ki3");
    await say("t4");
  });

  // ---- 6. Khách xem lại bằng chứng ----
  await segment("khach2", "khach", async ({ page, say, login }) => {
    await login("demo-an@example.com", "demo-password");
    await page.goto(groupUrl);
    await sleep(800);
    await say("k8", 0);
    await page.locator("#grp .ld-card", { has: page.locator('b:text-is("Đền Ngọc Sơn")') }).locator("a", { hasText: "Chi tiết" }).click();
    await page.waitForLoadState();
    for (let i = 0; i < 20 && !(await page.locator(".ld-check-card").count()); i++) { await sleep(3000); await page.reload(); }
    await page.locator(".ld-check-card").first().scrollIntoViewIfNeeded();
    await say("k9", 1500);
    await page.locator(".ld-photos").first().scrollIntoViewIfNeeded().catch(() => {});
    await sleep(2500);
  });

  // ---- 7. Admin: thiết bị, kiểm duyệt, hoàn tiền, khóa khẩn cấp ----
  await segment("admin", "admin", async ({ page, say, login }) => {
    await login("admin@example.com", "admin-demo-123");
    await page.goto(BASE + "/admin/thiet-bi");
    await say("a1", 0);
    await page.mouse.wheel(0, 1400); await sleep(1500);
    await page.goto(BASE + "/admin/kiem-duyet");
    await say("a2", 0);
    await page.locator("button[value=duyet]").first().click();
    await page.waitForLoadState(); await sleep(1500);
    await page.goto(BASE + "/admin/lich-le?status=refund_requested");
    await say("a3", 0);
    await page.locator("form[action*='hoan-tien'] button").first().click();
    await page.waitForLoadState(); await sleep(1500);
    await page.goto(BASE + "/admin");
    await page.locator("button[name=khoa]").hover();
    await say("a4", 1200);
  });

  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
