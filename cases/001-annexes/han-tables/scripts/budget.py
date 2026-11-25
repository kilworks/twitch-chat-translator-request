import sys, os, gzip
HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding='utf-8')
S = lambda n: open(os.path.join(HERE, '..', 'sets', n + '.txt'), encoding='utf-8').read()
tr = S('compact_TRAD_rank'); sm = S('compact_SIMP_rank')
ja_full = S('JA_STRICT'); ja145 = S('compact_JA_top250')
zf = '吧啊呢哦喔欸她沒很嘛嗎麼什怎你們吃會對說點裡甚啥偷玩是這'
cs = '嘅喺咗哋佢啲嘢冇嗰嚟㗎攰嘥噉喎咁諗嗮冚瞓啱攞搵唞嚿冧揼孭喐𨋢'
cw = '唔乜嘞咩畀睇嬲嗌'
cur = '這們麼說來對樣學實發應經覺讀體萬與樂區醫點關會單賣輕轉邊團圖廣壓國兩驗歲聲總濟開聽權氣灣嗎' + '这们么说对样实发应经觉读乐卖轻转边团图广压两验岁声总济开关听权气湾吗' + '唔嘅喺咗哋佢啲嘢冇嗰嚟㗎乜攰嘥噉喎嘞咁睇諗嗮畀冚瞓啱嬲攞搵唞嚿冧揼孭喐嗌咩\U000282E2' + '點解點樣邊個邊度得閒屋企傾偈靚仔靚女鍾意呢個呢度呢啲呢隻呢件'
g = lambda s: len(gzip.compress(s.encode('utf-8'), 9))
def row(name, s):
    print('| %s | %d | %d | %d |' % (name, len(s), len(s.encode('utf-8')), g(s)))
print('| list | chars | utf8 bytes | gzip bytes |')
print('|---|---|---|---|')
row('current (45 trad + 34 simp + 38 cantonese chars + words)', cur)
row('TRAD top 100', tr[:100]); row('TRAD top 200', tr[:200]); row('TRAD top 300', tr[:300])
row('SIMP top 100 (Pinlu order)', sm[:100]); row('SIMP top 200', sm[:200]); row('SIMP top 400', sm[:400])
row('JA_STRICT full', ja_full); row('JA learned 145', ja145)
row('ZF function chars', zf); row('Cantonese strong', cs); row('Cantonese weak', cw)
prop = tr[:200] + sm[:200] + ja_full + zf + cs + cw
row('PROPOSAL A (TRAD200 + SIMP200 + JA256 + ZF + CANTO)', prop)
prop2 = tr[:100] + sm[:100] + ja145 + zf + cs + cw
row('PROPOSAL B (TRAD100 + SIMP100 + JA145 + ZF + CANTO)', prop2)
full = S('TRAD_core_joyoexcl_leakpruned') + S('SIMP_noTW_noJany_noK') + ja_full + zf + cs + cw
row('PROPOSAL C full sets (TRAD3336 + SIMP2358 + JA256)', full)
print('2 percent of 69.0 KB gzipped = %.0f bytes ; current lists cost %d bytes gz' % (0.02 * 69.0 * 1024, g(cur)))
# bitmap alternative: one byte-class per code point over U+3400..U+9FFF
import json
sys.path.insert(0, HERE)
import unihan_lib
cls = bytearray(0x9FFF - 0x3400 + 1)
for c in S('TRAD_core_joyoexcl_leakpruned'):
    if 0x3400 <= ord(c) <= 0x9FFF: cls[ord(c) - 0x3400] = 1
for c in S('SIMP_noTW_noJany_noK'):
    if 0x3400 <= ord(c) <= 0x9FFF: cls[ord(c) - 0x3400] = 2
for c in ja_full:
    if 0x3400 <= ord(c) <= 0x9FFF: cls[ord(c) - 0x3400] = 3
import base64
raw = bytes(cls)
print('class map over U+3400..9FFF: %d bytes raw, %d gzip, base64 of gzip %d' % (len(raw), len(gzip.compress(raw, 9)), len(base64.b64encode(gzip.compress(raw, 9)))))
# RLE
runs = []
prev = cls[0]; n = 1
for b in cls[1:]:
    if b == prev: n += 1
    else: runs.append((prev, n)); prev = b; n = 1
runs.append((prev, n))
print('RLE runs', len(runs))
