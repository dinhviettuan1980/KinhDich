import * as cheerio from 'cheerio'
import { readFileSync, writeFileSync } from 'fs'

function noTone(s){return s.normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D')}
function slugify(s){return noTone(s).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}
function tok(t){
  if(/^Tín chủ con là\s*:/i.test(t)) return 'Tín chủ con là: {{ten}}'
  if(/^Ngụ tại\s*:/i.test(t)) return 'Ngụ tại: {{diaChi}}'
  if(/^Hôm nay là ngày/i.test(t)) return 'Hôm nay là {{ngayAm}}.'
  return t
}

const $ = cheerio.load(readFileSync('vk.html','utf8'))
const scope = $('.entry-content,.post-content,.td-post-content,article').first()
const els = []
scope.find('h2,h3,p').each((_,el)=>{
  const tag = el.tagName.toLowerCase()
  const text = $(el).text().replace(/\s+/g,' ').trim()
  if(text) els.push({tag, text})
})
// group theo H2
const sections = []
let cur = null
for(const e of els){
  if(e.tag==='h2'){ cur = {title:e.text, blocks:[]}; sections.push(cur); continue }
  if(!cur) continue
  if(/^Related articles/i.test(e.text)) { cur = null; continue } // hết bài
  cur.blocks.push(e)
}
// chỉ giữ section là văn khấn thật (có lời khấn)
const isPrayer = (b)=> b.some(x=>/Nam mô A Di Đà Phật|Con (lạy|kính lạy|cúi)/i.test(x.text))
const out = []
for(const s of sections){
  if(!/^Văn Khấn/i.test(s.title)) continue
  if(!isPrayer(s.blocks)) continue
  out.push({
    id: out.length+1,
    title: s.title.trim(),
    slug: slugify(s.title),
    blocks: s.blocks.map(b=>({ tag:b.tag, text: b.tag==='p'? tok(b.text): b.text })),
  })
}
writeFileSync('van-khan.json', JSON.stringify(out,null,1),'utf8')
console.log('Số bài văn khấn:', out.length)
out.forEach(v=>{
  const hasTok = v.blocks.some(b=>/\{\{/.test(b.text))
  console.log(` ${String(v.id).padStart(2)} ${v.title.padEnd(40)} blocks=${v.blocks.length} ${hasTok?'(có chỗ điền)':'(KHÔNG có chỗ điền ⚠️)'}`)
})
console.log('\n--- mẫu bài 1 (vài block có token) ---')
out[0].blocks.filter(b=>/\{\{|Nam mô/.test(b.text)).slice(0,5).forEach(b=>console.log(`[${b.tag}] ${b.text.slice(0,80)}`))
