// Registry 64 quẻ cho module Chu Dịch Nguyên Tác — tái dùng HEXAGRAMS (id, tên, upper/lower)
// đã có sẵn trong app, không tạo bản sao. status: 'ready' = đã có file hexagram-XX.json
// đầy đủ nguyên tác (đã tra cứu + đối chiếu nguồn).
import { HEXAGRAMS } from '../hexagrams'
import hexagram01 from './hexagram-01.json'
import hexagram02 from './hexagram-02.json'
import hexagram03 from './hexagram-03.json'
import hexagram04 from './hexagram-04.json'
import hexagram05 from './hexagram-05.json'
import hexagram06 from './hexagram-06.json'
import hexagram07 from './hexagram-07.json'
import hexagram08 from './hexagram-08.json'
import hexagram09 from './hexagram-09.json'
import hexagram10 from './hexagram-10.json'
import hexagram11 from './hexagram-11.json'
import hexagram12 from './hexagram-12.json'
import hexagram13 from './hexagram-13.json'
import hexagram14 from './hexagram-14.json'
import hexagram15 from './hexagram-15.json'
import hexagram16 from './hexagram-16.json'
import hexagram17 from './hexagram-17.json'
import hexagram18 from './hexagram-18.json'
import hexagram19 from './hexagram-19.json'
import hexagram20 from './hexagram-20.json'
import hexagram21 from './hexagram-21.json'
import hexagram22 from './hexagram-22.json'
import hexagram23 from './hexagram-23.json'
import hexagram24 from './hexagram-24.json'
import hexagram25 from './hexagram-25.json'
import hexagram26 from './hexagram-26.json'
import hexagram27 from './hexagram-27.json'
import hexagram28 from './hexagram-28.json'
import hexagram29 from './hexagram-29.json'
import hexagram30 from './hexagram-30.json'
import hexagram31 from './hexagram-31.json'
import hexagram32 from './hexagram-32.json'
import hexagram33 from './hexagram-33.json'
import hexagram34 from './hexagram-34.json'
import hexagram35 from './hexagram-35.json'
import hexagram36 from './hexagram-36.json'
import hexagram37 from './hexagram-37.json'
import hexagram38 from './hexagram-38.json'
import hexagram39 from './hexagram-39.json'
import hexagram40 from './hexagram-40.json'
import hexagram41 from './hexagram-41.json'
import hexagram42 from './hexagram-42.json'
import hexagram43 from './hexagram-43.json'
import hexagram44 from './hexagram-44.json'
import hexagram45 from './hexagram-45.json'
import hexagram46 from './hexagram-46.json'
import hexagram47 from './hexagram-47.json'
import hexagram48 from './hexagram-48.json'
import hexagram49 from './hexagram-49.json'
import hexagram50 from './hexagram-50.json'
import hexagram51 from './hexagram-51.json'
import hexagram52 from './hexagram-52.json'
import hexagram53 from './hexagram-53.json'
import hexagram54 from './hexagram-54.json'
import hexagram55 from './hexagram-55.json'
import hexagram56 from './hexagram-56.json'
import hexagram57 from './hexagram-57.json'
import hexagram58 from './hexagram-58.json'
import hexagram59 from './hexagram-59.json'
import hexagram60 from './hexagram-60.json'
import hexagram61 from './hexagram-61.json'
import hexagram62 from './hexagram-62.json'
import hexagram63 from './hexagram-63.json'
import hexagram64 from './hexagram-64.json'

const READY_DATA = {
  1: hexagram01,
  2: hexagram02,
  3: hexagram03,
  4: hexagram04,
  5: hexagram05,
  6: hexagram06,
  7: hexagram07,
  8: hexagram08,
  9: hexagram09,
  10: hexagram10,
  11: hexagram11,
  12: hexagram12,
  13: hexagram13,
  14: hexagram14,
  15: hexagram15,
  16: hexagram16,
  17: hexagram17,
  18: hexagram18,
  19: hexagram19,
  20: hexagram20,
  21: hexagram21,
  22: hexagram22,
  23: hexagram23,
  24: hexagram24,
  25: hexagram25,
  26: hexagram26,
  27: hexagram27,
  28: hexagram28,
  29: hexagram29,
  30: hexagram30,
  31: hexagram31,
  32: hexagram32,
  33: hexagram33,
  34: hexagram34,
  35: hexagram35,
  36: hexagram36,
  37: hexagram37,
  38: hexagram38,
  39: hexagram39,
  40: hexagram40,
  41: hexagram41,
  42: hexagram42,
  43: hexagram43,
  44: hexagram44,
  45: hexagram45,
  46: hexagram46,
  47: hexagram47,
  48: hexagram48,
  49: hexagram49,
  50: hexagram50,
  51: hexagram51,
  52: hexagram52,
  53: hexagram53,
  54: hexagram54,
  55: hexagram55,
  56: hexagram56,
  57: hexagram57,
  58: hexagram58,
  59: hexagram59,
  60: hexagram60,
  61: hexagram61,
  62: hexagram62,
  63: hexagram63,
  64: hexagram64,
}

export const CHU_DICH_REGISTRY = HEXAGRAMS.map((h) => ({
  id: h.id,
  name: h.name,
  status: READY_DATA[h.id] ? 'ready' : 'soon',
}))

export function getHexagramDetail(id) {
  return READY_DATA[Number(id)] || null
}
