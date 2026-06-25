import * as cheerio from 'cheerio';
export function parseQue(html, slug) {
  const $ = cheerio.load(html);
  const so = Number((slug.match(/que-(\d+)/) || [])[1]) || null;
  const scope = $('main').length ? $('main').first() : $('body');
  const raw = [];
  scope.find('h1,h2,h3,p,ul,ol,table').each((_, el) => {
    const tag = el.tagName.toLowerCase();
    const $el = $(el);
    if (tag === 'table') {
      const rows = [];
      $el.find('tr').each((_, tr) => {
        const cells = [];
        $(tr).find('th,td').each((_, td) => cells.push($(td).text().replace(/\s+/g, ' ').trim()));
        if (cells.some(c => c)) rows.push(cells);
      });
      if (rows.length) raw.push({ tag, rows });
    } else if (tag === 'ul' || tag === 'ol') {
      const items = [];
      $el.find('li').each((_, li) => { const t = $(li).text().replace(/\s+/g, ' ').trim(); if (t) items.push(t); });
      if (items.length) raw.push({ tag: 'ul', items });
    } else {
      const text = $el.text().replace(/\s+/g, ' ').trim();
      if (text && text.length > 1 && text !== '︾') raw.push({ tag, text });
    }
  });
  let start = raw.findIndex(b => b.tag === 'h1' && /QUẺ SỐ/i.test(b.text || ''));
  if (start < 0) start = Math.max(0, raw.findIndex(b => b.tag === 'h1'));
  let end = raw.findIndex((b, i) => i > start && b.tag === 'h2' && /64\s*Quẻ/i.test(b.text || ''));
  if (end < 0) end = raw.length;
  const h1 = raw[start]?.text || '';
  let ten = '', trieu = '';
  const m = h1.match(/QUẺ SỐ\s*\d+\s*[:\-]\s*(.+)/i);
  if (m) { const parts = m[1].split(/\s+-\s+/); ten = (parts[0] || '').trim(); trieu = parts.slice(1).join(' - ').trim(); }
  const blocks = raw.slice(start + 1, end).filter(b => !/Quay lại Bảng/i.test(b.text || ''));
  return { so, slug, ten, trieu, url: `https://dich.kabala.vn/${slug}`, blocks };
}
