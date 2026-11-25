"""Traditional-only set with Joyo-only exclusion plus a leak list learned on even Japanese lines, leak measured on odd Japanese lines. Aggregates + the leaking chars."""
import sys, os, re, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unihan_lib
F = unihan_lib.load()
sys.stdout.reconfigure(encoding='utf-8')
M = {'zh': 'zh', 'Chinese': 'zh', 'ja': 'ja', 'Japanese': 'ja'}
L = {'zh': set(), 'ja': set()}
for f in glob.glob(r'<raw chat folder, not published>/*.jsonl'):
    if 'heldout' in f.lower():
        continue
    for l in open(f, encoding='utf-8'):
        if '"lang"' not in l:
            continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        k = M.get(d.get('lang'))
        if k:
            L[k].add(re.sub(r'@\S+', ' ', d.get('content', '')))
ja = sorted(L['ja']); zh = sorted(L['zh'])
jtr = [t for i, t in enumerate(ja) if i % 2 == 0]; jte = [t for i, t in enumerate(ja) if i % 2 == 1]
ztr = [t for i, t in enumerate(zh) if i % 2 == 0]; zte = [t for i, t in enumerate(zh) if i % 2 == 1]
JOYO = {cp for cp, v in F['kJoyoKanji'].items() if v == '2010'}
JINMEI = set(F['kJinmeiyoKanji']); J0 = set(F['kJis0'])
GSTD = set(F['kGB0']) | set(F['kTGH'])
def pref(field, wanted):
    return {cp for cp, v in F[field].items() if v.split('-')[0] in wanted}
TSTD = pref('kIRG_TSource', {'T1', 'T2'}) | pref('kIRG_HSource', {'HB1', 'HB2'}) | set(F['kBigFive'])
def variants(field, cp):
    return [int(x[2:].split('<')[0], 16) for x in F[field].get(cp, '').split() if x.startswith('U+')]
trad_forms = {cp for cp in TSTD if any(s != cp for s in variants('kSimplifiedVariant', cp))}
base = {chr(c) for c in trad_forms - GSTD - JOYO}
print('trad forms not in GB2312/TGH and not Joyo: %d' % len(base))
cj = collections.Counter(c for t in jtr for c in set(t) if c in base)
leak = {c for c, n in cj.items() if n >= 1}
print('leak chars (>=1 even Japanese line): %d: %s' % (len(leak), ''.join(sorted(leak))))
core = base - leak
hit = lambda ls, S: sum(1 for t in ls if any(c in S for c in t))
print('TRAD_core size %d' % len(core))
for name, S in (('base (Joyo excluded only)', base), ('core (base minus leak)', core), ('TRAD_noGB_noJstrict (Joyo+Jinmei excluded)', {c for c in open(os.path.join(HERE, '..', 'sets', 'TRAD_noGB_noJstrict.txt'), encoding='utf-8').read()})):
    print('%-44s zh odd lines %5.1f%% (%d/%d) ; ja odd lines %5.2f%% (%d/%d)' % (name, 100 * hit(zte, S) / len(zte), hit(zte, S), len(zte), 100 * hit(jte, S) / len(jte), hit(jte, S), len(jte)))
open(os.path.join(HERE, '..', 'sets', 'TRAD_core_joyoexcl_leakpruned.txt'), 'w', encoding='utf-8', newline='\n').write(''.join(sorted(core)))
open(os.path.join(HERE, '..', 'sets', 'TRAD_leak_chars.txt'), 'w', encoding='utf-8', newline='\n').write(''.join(sorted(leak)))
# which leak chars are Jinmeiyo or JIS-0208 (explains why they are Japanese)
print('leak chars by Japanese tier: jinmei %s ; jis0208 only %s ; neither %s' % (
    ''.join(sorted(c for c in leak if ord(c) in JINMEI)), ''.join(sorted(c for c in leak if ord(c) not in JINMEI and ord(c) in J0)), ''.join(sorted(c for c in leak if ord(c) not in JINMEI and ord(c) not in J0))))
