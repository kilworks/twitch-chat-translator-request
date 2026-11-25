import re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ucd')
print('== Blocks (CJK-relevant)')
for l in open(os.path.join(D, 'Blocks.txt'), encoding='utf-8'):
    if re.search(r'CJK|Hangul|Hiragana|Katakana|Bopomofo|Halfwidth|Kanbun|Kangxi|Ideographic|Enclosed|Yijing|Small Kana|Kana|Tangut|Compatibility Forms|Vertical', l) and not l.startswith('#'):
        print(l.strip())
def parse(fn):
    out = []
    for l in open(os.path.join(D, fn), encoding='utf-8'):
        l = l.split('#')[0].strip()
        if not l: continue
        a, b = [x.strip() for x in l.split(';')]
        if '..' in a: lo, hi = [int(x, 16) for x in a.split('..')]
        else: lo = hi = int(a, 16)
        out.append((lo, hi, b))
    return out
sc = parse('Scripts.txt'); sx = parse('ScriptExtensions.txt')
def merge(r):
    r = sorted(r); m = []
    for lo, hi in r:
        if m and lo <= m[-1][1] + 1: m[-1][1] = max(m[-1][1], hi)
        else: m.append([lo, hi])
    return m
for s in ('Hiragana', 'Katakana', 'Hangul', 'Bopomofo', 'Han'):
    rs = merge([(a, b) for a, b, n in sc if n == s])
    print('== Script=%s: %d ranges, %d cps' % (s, len(rs), sum(b - a + 1 for a, b in rs)))
    print(' '.join('%04X-%04X' % (a, b) if a != b else '%04X' % a for a, b in rs))
print('== ScriptExtensions of interest')
for l in open(os.path.join(D, 'ScriptExtensions.txt'), encoding='utf-8'):
    if l.startswith('#') or not l.strip(): continue
    if re.search(r'Hira|Kana|Bopo|Hani|Hang', l.split('#')[0]) :
        print(l.rstrip()[:160])
