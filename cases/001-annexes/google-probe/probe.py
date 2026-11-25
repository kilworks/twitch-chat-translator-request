"""Synthetic probe: what does Google's web translate endpoint answer on short Han-only lines?

Invented generic phrases only (no chat data, no names). Mirrors the extension's two calls:
  single: GET translate_a/single?client=gtx&sl=..&tl=..&dt=t&q=..   -> data[2] = detected, data[0] = segments
  multi : POST translate_a/t?client=gtx&sl=auto&tl=..  with repeated q -> [translation, detected] per line
Output: results.jsonl and summary.txt next to this script.
"""
import json, sys, time, urllib.parse, urllib.request, urllib.error, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"}
SINGLE = "https://translate.googleapis.com/translate_a/single"
MULTI = "https://translate.googleapis.com/translate_a/t"

ZH_S = "太强了 好厉害 真的假的 笑死我了 主播好帅 加油 晚安 恭喜 好看 太棒了 好强 不错 可以啊 谢谢主播 感谢 好家伙 超强 太扯了 看不懂 笑死 太夸张了 好猛 无敌了 超好笑 傻眼了 太神了 没问题 辛苦了 好可爱 太可怕了 牛逼 绝了 笑哭 离谱".split()
ZH_T = "太強了 好厲害 真的假的 笑死我了 主播好帥 加油 晚安 恭喜 好看 太棒了 好強 不錯 可以啊 謝謝主播 感謝 好傢伙 超強 太扯了 看不懂 笑死 太誇張了 好猛 無敵了 超好笑 傻眼了 太神了 沒問題 辛苦了 好可愛 太可怕了 超扯 好扯 笑翻 太狂了".split()
JA_K = "草 初見 神回 最強 大草原 歴史的瞬間 神 感謝 優勝 最高 天才 完璧 無理 確定 開幕 公開 声優 湾岸 台湾 東京 大丈夫 了解 無敵 名試合 一撃 完全勝利 逆転 圧勝 神対応 感動 初心者 猛者 達人 速報 乙 同接 歓声 全員集合 安定 神配信 事故 炎上 今北産業 御意 宣伝 応援 拍手 乾杯 運営 配信".split()
GROUPS = {"zh_simplified": ZH_S, "zh_traditional": ZH_T, "ja_kanji_only": JA_K}
TARGETS = ["ja", "zh-CN", "zh-TW"]

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("HTTP 429, stopping", file=sys.stderr); raise SystemExit(3)
        raise

def single(text, sl, tl):
    q = urllib.parse.urlencode({"client": "gtx", "sl": sl, "tl": tl, "dt": "t", "q": text})
    d = get(SINGLE + "?" + q)
    tr = "".join(s[0] for s in d[0] if isinstance(s, list) and isinstance(s[0], str))
    return tr, d[2] if len(d) > 2 and isinstance(d[2], str) else None

def multi(texts, sl, tl):
    q = urllib.parse.urlencode({"client": "gtx", "sl": sl, "tl": tl})
    body = urllib.parse.urlencode([("q", t) for t in texts]).encode()
    d = get(MULTI + "?" + q, data=body)
    out = []
    for e in d:
        pair = e if isinstance(e, list) else [e]
        out.append((pair[0], pair[1] if len(pair) > 1 else None))
    return out

rows = []
def rec(**k):
    rows.append(k)

for g, phrases in GROUPS.items():
    for tl in TARGETS:
        for p in phrases:
            tr, det = single(p, "auto", tl)
            rec(group=g, endpoint="single", sl="auto", tl=tl, text=p, out=tr, detected=det, same=(tr.strip() == p.strip()))
            time.sleep(0.3)
        for i in range(0, len(phrases), 10):
            chunk = phrases[i:i + 10]
            res = multi(chunk, "auto", tl)
            for p, (tr, det) in zip(chunk, res):
                rec(group=g, endpoint="multi", sl="auto", tl=tl, text=p, out=tr, detected=det, same=(tr.strip() == p.strip()))
            time.sleep(0.4)

# forced source: what happens when we TELL Google the source (the hint path)
for g, forced in (("zh_simplified", "zh-CN"), ("zh_traditional", "zh-TW"), ("ja_kanji_only", "ja")):
    for tl in ("ja", "zh-TW", "zh-CN"):
        if tl.lower().split("-")[0] == forced.lower().split("-")[0] and tl != "zh-TW" and tl != "zh-CN":
            pass
        for p in GROUPS[g]:
            tr, det = single(p, forced, tl)
            rec(group=g, endpoint="single_forced", sl=forced, tl=tl, text=p, out=tr, detected=det, same=(tr.strip() == p.strip()))
            time.sleep(0.3)

with open(os.path.join(HERE, "results.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# summary
lines = []
agg = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    key = (r["group"], r["endpoint"], r["sl"], r["tl"])
    agg[key]["n"] += 1
    agg[key]["same"] += 1 if r["same"] else 0
    agg[key]["det=" + str(r["detected"])] += 1
for key in sorted(agg):
    c = agg[key]
    dets = {k[4:]: v for k, v in c.items() if k.startswith("det=")}
    lines.append(f"{key[0]:15} {key[1]:13} sl={key[2]:6} tl={key[3]:6} n={c['n']:3} same={c['same']:3}  detected={dict(sorted(dets.items(), key=lambda kv: -kv[1]))}")
open(os.path.join(HERE, "summary.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("done", len(rows), "rows")
