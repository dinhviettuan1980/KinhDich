import { parseQue } from './parse.mjs';
import { writeFileSync } from 'fs';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36';

async function getSlugs() {
  const html = await (await fetch('https://dich.kabala.vn/', { headers: { 'User-Agent': UA } })).text();
  const set = new Set([...html.matchAll(/\/que-(\d+)-[a-z0-9-]+/g)].map(m => m[0].slice(1)));
  return [...set].sort((a, b) => Number(a.match(/que-(\d+)/)[1]) - Number(b.match(/que-(\d+)/)[1]));
}

const slugs = await getSlugs();
console.log('Tìm thấy', slugs.length, 'quẻ');
const out = [];
for (const slug of slugs) {
  try {
    const res = await fetch(`https://dich.kabala.vn/${slug}`, { headers: { 'User-Agent': UA } });
    const html = await res.text();
    const q = parseQue(html, slug);
    out.push(q);
    const warn = q.blocks.length < 15 || !q.ten ? '  ⚠️ ÍT/THIẾU' : '';
    console.log(`${String(q.so).padStart(2)} ${q.ten.padEnd(22)} blocks=${q.blocks.length}${warn}`);
  } catch (e) {
    console.log(`✗ ${slug}: ${e.message}`);
  }
  await sleep(500);
}
out.sort((a, b) => a.so - b.so);
writeFileSync('que.json', JSON.stringify(out, null, 1), 'utf8');
console.log('\n→ Đã ghi que.json:', out.length, 'quẻ,', (JSON.stringify(out).length / 1024).toFixed(0), 'KB');
