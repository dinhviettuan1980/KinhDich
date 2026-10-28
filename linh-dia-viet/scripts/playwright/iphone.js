// Chụp các màn hình chính trên khổ iPhone (Safari) + kiểm tra tràn ngang, để soát giao diện "app".
const { chromium, devices } = require("playwright");
const fs = require("fs");
const BASE = "https://tuandv.id.vn/le-chua";
const OUT = __dirname + "/iphone";
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const { defaultBrowserType, ...iphone } = devices["iPhone 13"];
  const ctx = await browser.newContext({ ...iphone, locale: "vi-VN", timezoneId: "Asia/Ho_Chi_Minh" });
  const page = await ctx.newPage();
  page.setDefaultTimeout(60000);
  const shots = [];
  const shot = async (name) => {
    const over = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
    shots.push(`${name}: tràn ngang ${over}px`);
  };
  await page.goto(BASE + "/dang-ky"); await shot("1-dang-ky");
  await page.fill("#n", "Nguyễn Văn An"); await page.fill("#ns", "1985-03-12"); await page.fill("#dc", "Cầu Giấy, Hà Nội");
  await page.fill("#i", "ip-" + Math.random().toString(16).slice(2, 8) + "@example.com"); await page.fill("#p", "demo-password");
  await page.click("button:has-text('Tiếp tục')");
  await page.waitForURL(/tai-khoan\/the/); await shot("2-the");
  await page.fill("#so_the", "4242 4242 4242 4242"); await page.fill("#het_han", "12/28"); await page.fill("#cvc", "123");
  await page.click("button:has-text('Liên kết thẻ')"); await page.waitForLoadState("networkidle");
  await page.goto(BASE + "/"); await shot("3-trang-chu");
  await page.goto(BASE + "/den/den-ngoc-son"); await shot("4-den");
  const href = await page.getAttribute("a[href*='dat-le?den=']", "href");
  await page.goto("https://tuandv.id.vn" + href); await shot("5-dat-le");
  await page.goto(BASE + "/don"); await shot("6-lich-su");
  await page.goto(BASE + "/don/23").catch(() => {});
  console.log(shots.join("\n"));
  const m = await (await page.request.get(BASE + "/manifest.webmanifest")).json();
  console.log("manifest:", m.short_name, m.display, m.icons.length, "icon");
  await browser.close();
})();
