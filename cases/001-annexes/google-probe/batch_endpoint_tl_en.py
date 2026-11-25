import json, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"}
def multi(texts, tl, client):
    q=urllib.parse.urlencode({"client":client,"sl":"auto","tl":tl})
    body=urllib.parse.urlencode([("q",t) for t in texts]).encode()
    req=urllib.request.Request("https://translate.googleapis.com/translate_a/t?"+q, data=body, headers=UA)
    return json.loads(urllib.request.urlopen(req,timeout=20).read().decode())
batch=["那個老人餓死了","太強了","好厲害","主播好帥","謝謝主播","這個遊戲真的很好玩","太强了","好厉害","草","hello how are you"]
for client in ("gtx","dict-chrome-ex"):
    d=multi(batch,"en",client)
    print(client, [(t, e[1] if isinstance(e,list) and len(e)>1 else e) for t,e in zip(batch,d)])
