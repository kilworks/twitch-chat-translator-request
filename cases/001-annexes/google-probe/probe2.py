"""Second probe: how often does Google's source detection name the READER's language on short, unmarked Han lines
(and on other non-Latin scripts), with sl=auto. Public Tatoeba sentences only (short ones), no chat data.
Detection is independent of tl (seen in probe 1), so tl=en is enough; translation is kept to see correctness.
"""
import json, random, re, sys, time, urllib.parse, urllib.request, urllib.error, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
TAT = r"<folder of the public sentence-corpus exports>"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"}
SINGLE = "https://translate.googleapis.com/translate_a/single"

# the marker lists of origin/master langDetect.ts (CARACTERES_TRADITIONNELS / SIMPLIFIES / CANTONAIS) so that we keep only UNMARKED lines
TRAD = re.compile(r"[這們麼說來對樣學實發應經覺讀體萬與樂區醫點關會單賣輕轉邊團圖廣壓國兩驗歲聲總濟開聽權氣灣嗎]")
SIMP = re.compile(r"[这们么说对样实发应经觉读乐卖轻转边团图广压两验岁声总济开关听权气湾吗]")
CANT = re.compile(r"[唔嘅喺咗哋佢啲嘢冇嗰嚟㗎乜攰嘥噉喎嘞咁睇諗嗮畀冚瞓啱嬲攞搵唞嚿冧揼孭喐嗌]|點解|點樣|邊個|邊度|得閒|屋企|傾偈|靚仔|靚女|鍾意|呢[個度啲隻件間排粒張本]")
HAN = re.compile(r"^[\u3400-\u9fff\uf900-\ufaff]+$")

def get(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("HTTP 429, stopping", file=sys.stderr); raise SystemExit(3)
        raise

def single(text, tl="en"):
    q = urllib.parse.urlencode({"client": "gtx", "sl": "auto", "tl": tl, "dt": "t", "q": text})
    for attempt in range(4):
        try:
            d = get(SINGLE + "?" + q)
            tr = "".join(s[0] for s in d[0] if isinstance(s, list) and isinstance(s[0], str))
            return tr, d[2] if len(d) > 2 and isinstance(d[2], str) else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise
            time.sleep(2 + attempt * 3)
    return None, "ERR"

def sample(name, pred, n, seed=7):
    lines = [l.strip() for l in open(os.path.join(TAT, name + ".txt"), encoding="utf-8") if l.strip()]
    lines = [re.sub(r"[。！？，、.!?,\s]+$", "", l) for l in lines]
    lines = sorted({l for l in lines if pred(l)})
    random.Random(seed).shuffle(lines)
    return lines[:n]

short = lambda l: 2 <= len(l) <= 7
sets = {
    "zh_simplified_unmarked": sample("zh", lambda l: short(l) and HAN.match(l) and not SIMP.search(l) and not TRAD.search(l) and not CANT.search(l), 150),
    "zh_traditional_unmarked": sample("zh-tw", lambda l: short(l) and HAN.match(l) and not SIMP.search(l) and not TRAD.search(l) and not CANT.search(l), 150),
    "zh_traditional_marked": sample("zh-tw", lambda l: short(l) and HAN.match(l) and TRAD.search(l), 60),
    "yue_unmarked": sample("yue", lambda l: short(l) and HAN.match(l) and not CANT.search(l) and not TRAD.search(l) and not SIMP.search(l), 60),
}
# other non-Latin scripts, short lines, to see whether the "en" verdict is Han-specific
other = {"ko": ("ko", lambda l: 2 <= len(l) <= 8), "th": ("th", lambda l: 2 <= len(l) <= 10), "ar": ("ar", lambda l: 2 <= len(l) <= 10),
         "ru": ("ru", lambda l: 2 <= len(l) <= 10), "el": ("el", lambda l: 2 <= len(l) <= 10), "he": ("he", lambda l: 2 <= len(l) <= 10)}
for k, (f, p) in other.items():
    sets["other_" + k] = sample(f, p, 60)

rows = []
_f = open(os.path.join(HERE, "results2.jsonl"), "w", encoding="utf-8")
for g, phrases in sets.items():
    for p in phrases:
        tr, det = single(p, "en")
        r = dict(group=g, text=p, out=tr, detected=det)
        rows.append(r)
        _f.write(json.dumps(r, ensure_ascii=False) + "\n")
        _f.flush()
        time.sleep(0.25)
_f.close()

with open(os.path.join(HERE, "results2.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

agg = collections.defaultdict(collections.Counter)
for r in rows:
    agg[r["group"]][r["detected"]] += 1
out = []
for g, c in agg.items():
    n = sum(c.values())
    out.append(f"{g:26} n={n:3}  " + ", ".join(f"{k}={v}" for k, v in c.most_common()))
open(os.path.join(HERE, "summary2.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("done", len(rows))
