"""Generate candidate Han marker sets from open data.
Run:  python -I gen_sets.py        (cwd anywhere; paths are relative to this file)
Inputs : ../unihan/x/Unihan_*.txt (Unicode 18.0.0), ../opencc/*.txt
Outputs: ../sets/*.txt (one string per set, sorted by code point) and ../sets/summary.json
"""
import sys, os, json, gzip, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unihan_lib
F = unihan_lib.load()
OUT = os.path.join(HERE, '..', 'sets')
os.makedirs(OUT, exist_ok=True)
OC = os.path.join(HERE, '..', 'opencc')


def pref(field, wanted):
    return {cp for cp, v in F[field].items() if v.split('-')[0] in wanted}


def keys(field):
    return set(F[field])


def variants(field, cp):
    return [int(x[2:].split('<')[0], 16) for x in F[field].get(cp, '').split() if x.startswith('U+')]


# ---- repertoires -------------------------------------------------------
JOYO = {cp for cp, v in F['kJoyoKanji'].items() if v == '2010'}
JINMEI = keys('kJinmeiyoKanji')
J0 = keys('kJis0')                       # JIS X 0208 (6356 incl. level 1 and 2)
J_OTHER = keys('kJis1') | keys('kJIS0213')  # JIS X 0212 and JIS X 0213
J_STRICT = JOYO | JINMEI                 # modern everyday + names
J_JIS = J_STRICT | J0
J_ANY = J_JIS | J_OTHER
GSTD = keys('kGB0') | keys('kTGH')       # GB 2312 and the 2013 General Standard list (8105)
TSTD = pref('kIRG_TSource', {'T1', 'T2'}) | pref('kIRG_HSource', {'HB1', 'HB2'}) | keys('kBigFive')
KSTD = pref('kIRG_KSource', {'K0', 'K1'})
HKONLY = pref('kIRG_HSource', {'H', 'HD', 'HB0', 'HU'})  # HKSCS characters outside Big5 proper
HAN = lambda cp: 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x323AF

S_TO_T = collections.defaultdict(set)
T_TO_S = collections.defaultdict(set)
for fn, dst in (('STCharacters.txt', S_TO_T), ('TSCharacters.txt', T_TO_S)):
    for l in open(os.path.join(OC, fn), encoding='utf-8'):
        if l.startswith('#') or not l.strip():
            continue
        k, v = l.rstrip('\n').split('\t')
        dst[ord(k)] = {ord(x) for x in v.split(' ')}
OC_JP = {}
for l in open(os.path.join(OC, 'JPShinjitaiCharacters.txt'), encoding='utf-8'):
    if l.startswith('#') or not l.strip():
        continue
    k, v = l.rstrip('\n').split('\t')
    OC_JP[ord(k)] = {ord(x) for x in v.split(' ')}   # shinjitai -> kyujitai(s)? (checked below)

sets = {}
# ---- Japanese only (shinjitai, kokuji, JP forms) ------------------------
sets['JA_STRICT'] = J_STRICT - GSTD - TSTD - KSTD
sets['JA_JIS'] = J_JIS - GSTD - TSTD - KSTD
sets['JA_STRICT_vs_ANY_CHINESE'] = J_STRICT - GSTD - TSTD - KSTD - keys('kGB1') - keys('kGB3') - keys('kGB5') - keys('kGB8') - keys('kTaiwanTelegraph') - keys('kMainlandTelegraph') - pref('kIRG_HSource', {'H', 'HB1', 'HB2'})

# ---- simplified only ----------------------------------------------------
simp_forms = {cp for cp in GSTD if any(t != cp for t in variants('kTraditionalVariant', cp))}
sets['SIMP_raw'] = simp_forms
sets['SIMP_noTW'] = simp_forms - TSTD                       # also not a Big5 character
sets['SIMP_noTW_noJstrict'] = simp_forms - TSTD - J_STRICT   # Japanese everyday does not use it
sets['SIMP_noTW_noJIS'] = simp_forms - TSTD - J_JIS
sets['SIMP_noTW_noJany'] = simp_forms - TSTD - J_ANY
sets['SIMP_noTW_noJany_noK'] = simp_forms - TSTD - J_ANY - KSTD
oc_simp = {s for s, ts in S_TO_T.items() if ts - {s}}
sets['SIMP_opencc_noTW_noJany'] = oc_simp - TSTD - J_ANY
sets['SIMP_final'] = sets['SIMP_noTW_noJany_noK'] & (oc_simp | simp_forms)  # == noTW_noJany_noK, kept for symmetry

# ---- traditional only ---------------------------------------------------
trad_forms = {cp for cp in TSTD if any(s != cp for s in variants('kSimplifiedVariant', cp))}
sets['TRAD_raw'] = trad_forms
sets['TRAD_noGB'] = trad_forms - GSTD
sets['TRAD_noGB_noJstrict'] = trad_forms - GSTD - J_STRICT
sets['TRAD_noGB_noJIS'] = trad_forms - GSTD - J_JIS
sets['TRAD_noGB_noJany'] = trad_forms - GSTD - J_ANY
oc_trad = {t for t, ss in T_TO_S.items() if ss - {t}}
sets['TRAD_opencc_noGB_noJIS'] = oc_trad - GSTD - J_JIS
sets['TRAD_both_unihan_opencc_noGB_noJIS'] = (trad_forms & oc_trad) - GSTD - J_JIS

# ---- Cantonese ----------------------------------------------------------
cant_read = keys('kCantonese')
no_mand = lambda cp: cp not in F['kMandarin'] and cp not in F['kHanyuPinyin'] and cp not in F['kXHC1983'] and cp not in F['kHanyuPinlu']
sets['CANT_hk_with_reading'] = {cp for cp in HKONLY if cp in cant_read}
sets['CANT_hk_nomandarin'] = {cp for cp in HKONLY if cp in cant_read and no_mand(cp)}
sets['CANT_hk_nomandarin_noJK'] = {cp for cp in sets['CANT_hk_nomandarin'] if cp not in J_ANY and cp not in KSTD}
cc = set()
for cp in cant_read:
    if no_mand(cp) and cp not in F['kJapaneseOn'] and cp not in F['kJapaneseKun'] and cp not in F['kKorean'] and cp not in J_ANY and cp not in KSTD and HAN(cp):
        cc.add(cp)
sets['CANT_anyhan_nomandarin_noJK'] = cc

# ---- write -------------------------------------------------------------
def s(cps):
    return ''.join(chr(c) for c in sorted(cps))

def ranges(cps):
    cps = sorted(cps)
    out = []
    i = 0
    while i < len(cps):
        j = i
        while j + 1 < len(cps) and cps[j + 1] == cps[j] + 1:
            j += 1
        out.append((cps[i], cps[j]))
        i = j + 1
    return out

def js_class(cps, literal=True):
    parts = []
    for a, b in ranges(cps):
        f = (lambda c: chr(c)) if literal else (lambda c: ('\\u%04X' % c) if c < 0x10000 else ('\\u{%X}' % c))
        parts.append(f(a) if a == b else (f(a) + f(b) if b == a + 1 else f(a) + '-' + f(b)))
    return '[' + ''.join(parts) + ']'

summary = {}
for name, cps in sets.items():
    txt = s(cps)
    open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8', newline='\n').write(txt)
    cls = js_class(cps)
    esc = js_class(cps, literal=False)
    bmp = sum(1 for c in cps if c < 0x10000)
    summary[name] = dict(n=len(cps), bmp=bmp, utf8_string=len(txt.encode('utf-8')), gz_string=len(gzip.compress(txt.encode('utf-8'), 9)),
                         utf8_class_ranges=len(cls.encode('utf-8')), gz_class_ranges=len(gzip.compress(cls.encode('utf-8'), 9)),
                         n_ranges=len(ranges(cps)), esc_class_bytes=len(esc.encode('ascii')), gz_esc_class=len(gzip.compress(esc.encode('ascii'), 9)))
json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1)
print('| set | n | utf8 bytes string | gzip string | ranges | utf8 bytes class | gzip class | gzip escaped class |')
print('|---|---|---|---|---|---|---|---|')
for k, v in summary.items():
    print('| %s | %d | %d | %d | %d | %d | %d | %d |' % (k, v['n'], v['utf8_string'], v['gz_string'], v['n_ranges'], v['utf8_class_ranges'], v['gz_class_ranges'], v['gz_esc_class']))

# diagnostics used in the report
print()
print('repertoires: JOYO %d JINMEI %d J0 %d J_OTHER %d GSTD %d TSTD %d KSTD %d HKONLY %d' % (len(JOYO), len(JINMEI), len(J0), len(J_OTHER), len(GSTD), len(TSTD), len(KSTD), len(HKONLY)))
print('simp_forms', len(simp_forms), 'trad_forms', len(trad_forms), 'oc_simp', len(oc_simp), 'oc_trad', len(oc_trad))
print('SIMP unihan-only vs opencc-only (noTW noJany):', len(sets['SIMP_noTW_noJany'] - sets['SIMP_opencc_noTW_noJany']), len(sets['SIMP_opencc_noTW_noJany'] - sets['SIMP_noTW_noJany']))
print('TRAD unihan vs opencc (noGB noJIS):', len(sets['TRAD_noGB_noJIS'] - sets['TRAD_opencc_noGB_noJIS']), len(sets['TRAD_opencc_noGB_noJIS'] - sets['TRAD_noGB_noJIS']))
ja_cur = set('这们么说对样实发应经觉读乐卖轻转边团图广压两验岁声总济开关听权气湾吗')
tr_cur = set('這們麼說來對樣學實發應經覺讀體萬與樂區醫點關會單賣輕轉邊團圖廣壓國兩驗歲聲總濟開聽權氣灣嗎')
cn_cur = set('唔嘅喺咗哋佢啲嘢冇嗰嚟㗎乜攰嘥噉喎嘞咁睇諗嗮畀冚瞓啱嬲攞搵唞嚿冧揼孭喐嗌咩\U000282E2')
for nm, cur, key in (('simp', ja_cur, 'SIMP_noTW_noJany_noK'), ('trad', tr_cur, 'TRAD_noGB_noJIS'), ('trad-strictJ', tr_cur, 'TRAD_noGB_noJstrict')):
    got = {ord(c) for c in cur}
    print(nm, 'current in generated set:', len(got & sets[key]), 'of', len(got), 'missing:', s(got - sets[key]))
got = {ord(c) for c in cn_cur}
for k in ('CANT_hk_with_reading', 'CANT_hk_nomandarin', 'CANT_hk_nomandarin_noJK', 'CANT_anyhan_nomandarin_noJK'):
    print('cant current in', k, len(got & sets[k]), 'of', len(got), 'missing:', s(got - sets[k]))
