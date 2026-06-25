// Đổi dương lịch → âm lịch Việt Nam (thuật toán Hồ Ngọc Đức, múi giờ +7).
function jdFromDate(dd, mm, yy) {
  const a = Math.floor((14 - mm) / 12)
  const y = yy + 4800 - a
  const m = mm + 12 * a - 3
  let jd = dd + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045
  if (jd < 2299161) jd = dd + Math.floor((153 * m + 2) / 5) + 365 * y + Math.floor(y / 4) - 32083
  return jd
}
function newMoon(k) {
  const T = k / 1236.85, T2 = T * T, T3 = T2 * T, dr = Math.PI / 180
  let J = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
  J += 0.00033 * Math.sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
  const M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
  const Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
  const F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
  let C = (0.1734 - 0.000393 * T) * Math.sin(M * dr) + 0.0021 * Math.sin(2 * dr * M)
  C -= 0.4068 * Math.sin(Mpr * dr) + 0.0161 * Math.sin(dr * 2 * Mpr)
  C -= 0.0004 * Math.sin(dr * 3 * Mpr)
  C += 0.0104 * Math.sin(dr * 2 * F) - 0.0051 * Math.sin(dr * (M + Mpr))
  C -= 0.0074 * Math.sin(dr * (M - Mpr)) + 0.0004 * Math.sin(dr * (2 * F + M))
  C -= 0.0004 * Math.sin(dr * (2 * F - M)) - 0.0006 * Math.sin(dr * (2 * F + Mpr))
  C += 0.0010 * Math.sin(dr * (2 * F - Mpr)) + 0.0005 * Math.sin(dr * (2 * Mpr + M))
  let dt
  if (T < -11) dt = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
  else dt = -0.000278 + 0.000265 * T + 0.000262 * T2
  return Math.floor(J + C - dt + 0.5 + 7 / 24)
}
function sunLong(jdn) {
  const T = (jdn - 2451545.5 - 7 / 24) / 36525, T2 = T * T, dr = Math.PI / 180
  const M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
  const L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
  let DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * Math.sin(dr * M)
  DL += (0.019993 - 0.000101 * T) * Math.sin(dr * 2 * M) + 0.000290 * Math.sin(dr * 3 * M)
  let L = (L0 + DL) * dr
  L = L - Math.PI * 2 * Math.floor(L / (Math.PI * 2))
  return Math.floor(L / Math.PI * 6)
}
function lm11(yy) {
  const off = jdFromDate(31, 12, yy) - 2415021
  const k = Math.floor(off / 29.530588853)
  let nm = newMoon(k)
  if (sunLong(nm) >= 9) nm = newMoon(k - 1)
  return nm
}
function leapOff(a11) {
  const k = Math.floor((a11 - 2415021.076998695) / 29.530588853 + 0.5)
  let last = 0, i = 1, arc = sunLong(newMoon(k + i))
  do { last = arc; i++; arc = sunLong(newMoon(k + i)) } while (arc != last && i < 14)
  return i - 1
}
export function solar2lunar(dd, mm, yy) {
  const dn = jdFromDate(dd, mm, yy)
  const k = Math.floor((dn - 2415021.076998695) / 29.530588853)
  let ms = newMoon(k + 1)
  if (ms > dn) ms = newMoon(k)
  let a11 = lm11(yy), b11 = a11, ly
  if (a11 >= ms) { ly = yy; a11 = lm11(yy - 1) } else { ly = yy + 1; b11 = lm11(yy + 1) }
  const ld = dn - ms + 1
  const diff = Math.floor((ms - a11) / 29)
  let leap = 0, lm = diff + 11
  if (b11 - a11 > 365) {
    const lo = leapOff(a11)
    if (diff >= lo) { lm = diff + 10; if (diff == lo) leap = 1 }
  }
  if (lm > 12) lm -= 12
  if (lm >= 11 && diff < 4) ly -= 1
  return { day: ld, month: lm, year: ly, leap }
}

const CAN = ['Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý']
const CHI = ['Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi', 'Thân', 'Dậu', 'Tuất', 'Hợi']
export function canChiYear(year) { return `${CAN[(year + 6) % 10]} ${CHI[(year + 8) % 12]}` }

// Chuỗi ngày âm hôm nay (giờ VN), dạng: "ngày 11 tháng 5 năm Bính Ngọ (âm lịch)"
export function lunarTodayText() {
  const [Y, M, D] = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh' })
    .format(new Date()).split('-').map(Number)
  const l = solar2lunar(D, M, Y)
  return `ngày ${l.day} tháng ${l.month}${l.leap ? ' (nhuận)' : ''} năm ${canChiYear(l.year)} (âm lịch)`
}
