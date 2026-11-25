import json, urllib.request, urllib.parse, time
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"}
def single(text, tl, sl):
    q=urllib.parse.urlencode({"client":"gtx","sl":sl,"tl":tl,"dt":"t","q":text})
    req=urllib.request.Request("https://translate.googleapis.com/translate_a/single?"+q, headers=UA)
    d=json.loads(urllib.request.urlopen(req,timeout=20).read().decode())
    return "".join(s[0] for s in d[0] if isinstance(s,list) and isinstance(s[0],str)), d[2] if len(d)>2 else None
rows=[json.loads(l) for l in open('results2.jsonl',encoding='utf-8')]
trad=[r['text'] for r in rows if r['group']=='zh_traditional_unmarked'][:40]
same=diff=0; ex=[]
for t in trad:
    a,_=single(t,'en','auto'); time.sleep(0.25)
    b,db=single(t,'en','zh-CN'); time.sleep(0.25)
    c,dc=single(t,'en','zh-TW'); time.sleep(0.25)
    if a==b==c: same+=1
    else:
        diff+=1; ex.append((t,a,b,c))
print("40 unmarked traditional lines: identical translations auto/zh-CN/zh-TW:",same,"differ:",diff)
for e in ex[:8]: print("  ",e)
# detection echo when forced
t=trad[0]; print("forced zh-CN detected:",single(t,'en','zh-CN')[1],"forced zh-TW detected:",single(t,'en','zh-TW')[1])
