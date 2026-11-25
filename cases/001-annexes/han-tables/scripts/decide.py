"""Reference implementation of the Han-line decision procedure of the report (section 8), with COMPACT shippable sets.
Python only to measure; the TypeScript port is a transliteration. Output labels: ja ko yue zh-hans zh-hant zh unknown (zh = Chinese, script unknown).
"""
import sys, os, re, json, unicodedata, collections
HERE = os.path.dirname(os.path.abspath(__file__))
SETS = os.path.join(HERE, '..', 'sets')
rd = lambda n: open(os.path.join(SETS, n + '.txt'), encoding='utf-8').read()

# ---- evidence sets (compact) -------------------------------------------------------------
TRAD = set(rd('TRAD_core_joyoexcl_leakpruned'))            # replaced below by the frequency prefix when COMPACT
SIMP = set(rd('SIMP_noTW_noJany_noK'))
JA = set(rd('JA_STRICT'))
ZF = set('吧啊呢哦喔欸她沒很嘛嗎麼什怎你們吃會對說點裡甚啥偷玩是這')   # zero hits in 32 848 Japanese chat lines; 這 and 是 stay: kanji-only Japanese never has them
CANTO_STRONG = set('嘅喺咗哋佢啲嘢冇嗰嚟㗎攰嘥噉喎咁諗嗮冚瞓啱攞搵唞嚿冧揼孭喐\U000282E2')   # none of them in GB 2312 / TGH
CANTO_WEAK = set('唔乜嘞咩畀睇嬲嗌')                                                           # all in GB 2312: Mandarin uses them too
CANTO_WORDS = re.compile('點解|點樣|邊個|邊度|得閒|屋企|傾偈|靚仔|靚女|鍾意|呢[個度啲隻件間排粒張本]')
SOFT_KANA = set('のノヽヾゝゞヵヶ')                                                          # decorative kana in Chinese chat
KANA = re.compile('[ぁ-ゖゝ-ゟァ-ヺヽ-ヿㇰ-ㇿ]')
HANGUL = re.compile('[ᄀ-ᇿㄱ-ㆎ가-힣ꥠ-ꥼힰ-ퟻ]')
BOPO = re.compile('[ㄅ-ㄯㆠ-ㆿ]')
HAN = re.compile('[㐀-䶿一-鿿豈-﫿\U00020000-\U0003134f]')
CLEAN = re.compile(r'@\S+|https?://\S+|\[emote:[^\]]*\]')


def compact(prefix_trad=200, prefix_simp=200):
    global TRAD, SIMP
    import collections as C
    # frequency orders are produced by compact_curve.py; here we rebuild them from the same inputs
    tr = open(os.path.join(SETS, 'compact_TRAD_rank.txt'), encoding='utf-8').read()
    sm = open(os.path.join(SETS, 'compact_SIMP_rank.txt'), encoding='utf-8').read()
    TRAD = set(rd('TRAD_core_joyoexcl_leakpruned')) if prefix_trad is None else set(tr[:prefix_trad])
    SIMP = set(sm[:prefix_simp])


def decide(raw):
    t = unicodedata.normalize('NFKC', CLEAN.sub(' ', raw))              # folds halfwidth kana, fullwidth latin, compatibility ideographs
    k = KANA.findall(t); han = HAN.findall(t); hg = HANGUL.findall(t); bp = BOPO.findall(t)
    hard_kana = [c for c in k if c not in SOFT_KANA]; soft = [c for c in k if c in SOFT_KANA]
    if not (han or k or hg or bp):
        return 'unknown', 'no CJK'
    if hg and len(hg) * 2 >= len(han):
        return 'ko', 'hangul'                                              # hanja are a minority in Korean chat
    if hard_kana:
        return 'ja', 'kana'                                                 # ー ・ are not in KANA: they never count
    if bp:
        return 'zh-hant', 'bopomofo'
    ch = set(han)
    if ch & CANTO_STRONG or CANTO_WORDS.search(t) or len(ch & CANTO_WEAK) >= 2:
        return 'yue', 'cantonese'
    ja_ev = ch & JA; s = ch & SIMP; tr = ch & TRAD; z = ch & ZF
    zh_ev = s | tr | z
    if len(soft) >= 3 and not zh_ev:
        return 'ja', 'soft kana x3'
    if ja_ev and not zh_ev:
        return 'ja', 'japan-only kanji'
    if ja_ev and zh_ev:
        return 'unknown', 'mixed evidence'
    if s and tr:
        return 'unknown', 'mixed script'
    if tr:
        return 'zh-hant', 'trad-only char'
    if s:
        return 'zh-hans', 'simp-only char'
    if z:
        return 'zh', 'function char'
    return 'unknown', 'shared Han only'


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    compact()
    for line in sys.argv[1:]:
        print(line, decide(line))
