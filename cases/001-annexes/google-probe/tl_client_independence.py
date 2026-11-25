import json, urllib.request, urllib.parse, time
rows=[json.loads(l) for l in open('results2.jsonl',encoding='utf-8')]
tr=[r for r in rows if r['group']=='zh_traditional_unmarked'][:8]
print("probe2 (tl=en) outputs:")
for r in tr: print("  ", r['text'], '->', r['out'], '| detected', r['detected'])
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"}
def single(text, tl, sl='auto', client='gtx'):
    q=urllib.parse.urlencode({"client":client,"sl":sl,"tl":tl,"dt":"t","q":text})
    req=urllib.request.Request("https://translate.googleapis.com/translate_a/single?"+q, headers=UA)
    d=json.loads(urllib.request.urlopen(req,timeout=20).read().decode())
    return "".join(s[0] for s in d[0] if isinstance(s,list) and isinstance(s[0],str)), d[2] if len(d)>2 else None
print("same lines, different tl (detected):")
for r in tr[:8]:
    out=[]
    for tl in ('en','ja','fr','zh-CN','de'):
        try:
            t,det=single(r['text'],tl); out.append(f"{tl}:{det}")
        except Exception as e:
            out.append(f"{tl}:ERR")
        time.sleep(0.3)
    print("  ", r['text'], ' '.join(out))
print("client dict-chrome-ex, tl=en vs ja:")
for r in tr[:5]:
    out=[]
    for tl in ('en','ja'):
        try:
            t,det=single(r['text'],tl,client='dict-chrome-ex'); out.append(f"{tl}:{det}")
        except Exception as e:
            out.append(f"{tl}:ERR")
        time.sleep(0.3)
    print("  ", r['text'], ' '.join(out))
