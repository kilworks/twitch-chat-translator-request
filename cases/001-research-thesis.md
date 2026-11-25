# Case 001, research thesis: why Han-script lines were not translated, and how the fix was planned

Date: 2026-11-25. Products: Kick Chat Translator (KCT) and Twitch Chat Translator (TCT). This is the companion of [case 001](001-han-script-detection.md). Case 001 reports what was changed and measured. This file reports the research that came before the change: the claim, every mechanism with its counts, the data that exists and what it cannot prove, the plan and its decision rule, the review of the plan, the mistakes caught on the way, and what stays open.

Pinned code: KCT `origin/master` at `7d8671a` (3.6.3, merge of PR 90), TCT `origin/master` at `14b3046` (1.1.2, merge of PR 25). Every `file:line` below refers to those commits, prefixed `K:` for KCT and `T:` for TCT. Lines move when the code moves, so a later reader should re-derive them.

Reading key: VERIFIED means read in code or reproduced by a run. INFERENCE means deduced and not measured. Counts are lines or units, never chat content. No chat line, channel name or person is stored here. The few example lines are invented witnesses written for this study.

## 1. Thesis

A store review said that languages written with Han characters (Chinese, Taiwanese, Japanese) are often detected wrongly, the line is taken for the reader's own language, and it is not translated. The reviewer worked around it by turning off "skip messages already in my language".

The research found that:

1. The symptom has several independent causes. The heaviest one is not in the local detector. The translation service answers `en` for a large share of short unmarked Traditional Chinese, and the pipeline deletes the line after the call when that answer equals the reader's language, with no check of the script. An English reader loses those lines after the request was already spent.
2. The reviewer's workaround matches exactly one of the two gates that delete a line. The other gate, the one that fires before any request, is not behind that toggle.
3. The local detector has smaller, separate defects: an over-wide kana range, shared character forms listed as Chinese-only, no bopomofo, and no usable signal on most Han-only lines.
4. A strict source-language allowlist can drop half of the Chinese lines for a reason unrelated to detection.
5. A browser language-detection API is not a lever today.
6. No existing labelled set could judge a change, so the plan builds its own sets and writes its decision rule before scoring.

The right plan is therefore a short list of small guards, each measured before and after, not a new detector.

## 2. The request and its scope

The review is a five-star review of the Twitch extension. It says the extension is free, unlimited and the best the reviewer found. For Chinese, Taiwanese and Japanese it says detection is often wrong, lines are taken for the reader's own language and are not translated, and it guesses that closely related languages in other regions behave the same. It gave no example line, no channel and no reader language, and a store review cannot be answered from the store.

A second remark (start a new page by hand instead of automatically) is a separate feature and was left out.

The owner chose to improve the detection itself instead of translating everything in doubt, and asked for a complete implementation brief for a smaller model, with an unlimited research budget for the brief.

## 3. How a line is deleted (the map that came first)

Reading the code at the pinned commits gave this map.

- There is no setting literally named "skip messages in my language". The user toggle is "Skip messages already in target language" (storage key `ignoreEnglish`, default on). It gates two of the three "already readable" exits. The third is unconditional.
- The pre-request same-language skip (`K:pipeline.ts:329`, `T:pipeline.ts:316`) reads `confidentLanguage()`, the looked-up answer, not `detectLanguageWithBrowser()`, the guess that mixes in franc and the browser detector. So improving the guess changes nothing for that skip. Only the script and lookup layers (`K:langDetect.ts:2434-2524` and `:2573-2629`) can feed it.
- For a Han-only line with no Cantonese, Traditional or Simplified marker, `confidentLanguage` returns `undefined`. The line goes to the engine with `sl=auto`.
- The post-request skip (`K:pipeline.ts:705`, `T:pipeline.ts:648`) is `isSameLanguageAsTarget(result.detectedLang, effTarget) && settings.ignoreEnglish`. It trusts the engine's `detectedLang` with no confidence, no script check, and only behind the toggle. `detectedLang` comes from `K:google.ts:69` (single request) or `:157` (batch: `sourceLangHint ?? engine answer`, with `sl` announced only if the whole batch shares the hint), then `normalizeLang` (`translator/index.ts:123`).
- The English skip (`:296`) has a guard, `hasNonEnglishLetter` (`filters.ts:98`). The post-request gate has none.
- `zh` and `zh-tw` are the same language for every comparison (`isSameLanguageAsTarget`, `filters.ts:107-110`), `yue` is different from both, and `ja` differs from all. The source-language allowlist compares by strict equality (`filters.ts:84`), so there `zh` and `zh-tw` differ. That asymmetry is a trap.
- A forced `sl` is relaxed to `auto` only by the manual retry button.

## 4. Mechanisms M1 to M9

### M1. The post-request gate deletes on the engine's verdict (the heaviest one)

Probes against the service endpoint the extension uses (`sl=auto`, same answers for the single and batch variants on 354 paired requests, for three target languages, and on 10 lines for the second client string):

| Class | n | Detected language returned |
|---|---|---|
| Simplified Chinese | 150 | `zh-CN` 150 |
| Traditional Chinese, no marker (no `sl` sent) | 150 | `en` 148, `ja` 2 |
| Traditional Chinese, with `sl=zh-TW` (the verdict read is the `sl`) | 60 | `en` 60 |
| Written Cantonese, no marker | 60 | `en` 40, `zh-CN` 16, `ja` 2, `yue` 2 |
| Korean | 60 | `ko` 60 |
| Thai | 60 | `th` 60 |
| Arabic | 60 | `ar` 58, `fa` 1, `sd` 1 |
| Russian | 60 | `ru` 51, `ky` 2, `uk` 2, `sr` 2, `bg` 2, `be` 1 |
| Greek | 60 | `el` 60 |
| Hebrew | 60 | `iw` 60 |

Short public-corpus sentences of 2 to 7 characters, `tl=en`. The translation is correct although the detected language is wrong: an unmarked Traditional sentence about an old man starving is translated correctly and labelled `en`.

On 118 invented chat-style phrases (single and batch endpoints, three target languages):

| Class | n | Detected language | Same translation for `tl=ja` / `zh-TW` / `zh-CN` |
|---|---|---|---|
| Simplified | 34 | `zh-CN` 34 | 0 / 18 / 34 of 34 |
| Traditional | 34 | `zh-CN` 21, `en` 12, `ja` 1 | 0 / 32 / 21 of 34 |
| Japanese in kanji only | 50 | `ja` 35, `zh-CN` 10, `en` 5 | 37 / 20 / 11 of 50 |

So the share of `en` is 99 percent on the corpus sentences but 35 percent (12 of 34) on the chat-style ones. A first estimate of exposure multiplied 66 percent (Han-only lines in Chinese channels) by 64 percent (no sure answer) by the corpus rate and got about 4 lines in 10. A reviewer caught that the chat-style rate is the relevant one, and the estimate was restated as a range of 15 to 42 percent of the lines of Chinese channels exposed to an English reader. It is an inference to measure, not a result.

Effect: an English reader loses the line after the request was paid. For a Japanese reader `en` does not occur, but `ja` comes back for 1 to 2 Traditional lines in 100 and for words that are also Japanese.

Forcing the source removes the defect: with `sl=zh-CN`, `zh-TW` or `ja` the service returns the forced language, and 40 unmarked Traditional lines give identical translations under `sl=auto`, `zh-CN` and `zh-TW` (`tl=en`, one pass; with other target languages 1 to 2 in 34 change). Every extra hint the local detector can give removes lines from M1.

The reviewer's toggle covers exactly `:296` and `:705`. The "same language, sure" gate at `:329` is not behind it. This is the most economical explanation of the report. It was not reproduced on the reviewer's own chat, because no line was given, and the service may vary.

### M2. Most Han-only lines carry no signal

`K:langDetect.ts:2419-2431` (`cantonaisOuChinois`) returns nothing when no table touches. franc-min has no Han model at all (`cmn` maps to `zh`, `languages.ts:98`) and never answers `jpn` for a kana-less line.

Distinct Han-only lines, label = channel-declared language, one evening of chat:

| Class | Lines | No sure answer | Notes |
|---|---|---|---|
| Chinese channels | 8,239 | 59.7 % | published rule: `zh-tw` 38.7 %, `zh` 0.6 %, `yue` 0.9 %, `ja` 0 |
| Japanese channels | 672 | 98.7 % | 9 lines (1.3 %) get a wrong `zh` or `zh-tw` |

With compact lists derived from the Unihan database (proposal A: 200 Traditional-only, 200 Simplified-only, 256 Japan-only characters, about 1,640 bytes gzip): silence on Chinese lines falls to 32.2 percent (`zh-hant` 51.7, `zh` 14.4, `zh-hans` 1.0, `yue` 0.7), 17.0 percent of the Han-only Japanese lines are decided as Japanese, and 5 Japanese-channel lines are flagged as Chinese, of which 4 are genuine Chinese lines posted in a Japanese channel. The real leak is therefore 1 line of 672 (0.15 percent). Four Chinese lines typed with Japanese forms (the character 実) become Japanese (4 of 8,239). The smaller proposal B (100 / 100 / 145, about 940 bytes gzip) was designed but not measured.

Ambiguity floor: lines made only of characters both languages write carry no evidence at all. Estimated at 64 to 68 percent of Han-only Japanese lines and 11 to 15 percent of Chinese ones (measured variously as 81.8 to 82.3 percent of 672 and 30 to 32 percent of 8,239 without separating evidence). For these "unknown" is the correct answer, and the research set the rule: return unknown, never a guess, never skip on script grounds.

Cost model behind that rule: let L be the cost of wrongly skipping a foreign line (a message lost) and b the cost of translating an own-language line (one call; KCT drops a translation identical to the source silently, so b is near 0). Skipping on script grounds is justified only if P(own language | evidence) is at least L/(L+b), which is at least 0.95 for L/b at least 20. A Han-only line with no evidence has a posterior anywhere between 0 and 1 depending on the channel, so the script layer must not skip it.

### M3. The kana count is too wide

`K:langDetect.ts:2466` counts the whole range U+3040 to U+30FF and `:2512` does `if (kana > 0) return 'ja'`. The block contains non-letters: the prolonged sound mark (U+30FC), the middle dot (U+30FB), combining marks U+3099 to U+309C, and U+30A0. It also misses half-width katakana (U+FF66 to U+FF9D) and U+31F0 to U+31FF.

(a) Measured in real chat and verified by execution in both extensions: a kana nickname after an `@` survives mention stripping, because the mention pattern recognises only Latin letters, digits and underscore (`K:emoteParser.ts:6`, `T:emoteParser.ts:8`), and the whole Chinese line comes out as a sure Japanese verdict. 27 of 11,280 eligible non-Japanese lines (0.24 percent), all from the Twitch side. Effect: a Japanese reader loses the line through the non-configurable pre-request skip, and other readers send it with `sl=ja`.

(b) Not observed in real chat: decorative use inside the body of a Chinese line (a kaomoji with `ヽ` or `ノ`, a trailing `ー`, a name written with `・`). 0 occurrences in 14,440 Chinese lines. Across 3.2 million raw lines, 100 lines have Han plus decor-only kana, and 98 of them sit in Japanese-declared channels as ordinary Japanese. Excluding `ー` and `・` from the count costs 12 Japanese lines of 31,607 (0.04 percent). Excluding the soft kana as well (の ノ ヽ ヾ ゝ ゞ ヵ ヶ) would cost 77 (0.24 percent). Of 31,607 distinct Japanese-channel lines, 29,302 carry a hard kana, 65 (0.2 percent) carry only a soft kana plus Han, and 12 carry only `ー` or `・` with Han. In 9,903 Chinese-channel lines, 5 carry a hard kana (genuine Japanese phrases), 0 carry only a soft kana, and 1 carries `・` only (a kaomoji).

Decision: remove mentions and URLs from the script count, count only letters as kana, keep `ー` and `・` inside the total so that one hard kana plus `ー` (a very common chat line) does not fall under the two-character floor, and do not tighten the soft kana. The mechanism for decorative kana is real (nine invented witness lines reproduce it) but its frequency in the data is nil, so it is justified by verified lines, not by volume.

### M4. Chinese tables leak into Japanese

Characters written identically in everyday Japanese (the jōyō list): the Traditional list holds `開` (`K:langDetect.ts:2415`), the Simplified list holds `声` and `湾` (`:2417`). Characters used only in Japanese personal names (jinmeiyō), 17 more in the Traditional list: `這來樣實應萬與樂單賣轉團廣國驗聽氣`. The Cantonese list holds `嬲`, a real Japanese kanji (`K:2374`, with a comment at `:2350-2353`). Unihan audit of the tables (tiered against kJoyoKanji, kJinmeiyoKanji, JIS X 0208, JIS X 0212 and 0213, GB, Big5 and Korean sources):

| Tier | Traditional list | Simplified list | Cantonese list |
|---|---|---|---|
| Everyday Japanese (jōyō) | 1 (開) | 2 (声 湾) | 0 |
| Names only (jinmeiyō) | 17 | 0 | 0 |
| JIS X 0208 only (old forms typed on a Japanese IME) | 24 | 3 | 3 (唔 睇 嬲) |
| JIS X 0212 or 0213 only | 1 | 4 | 12 |
| No Japanese standard | 2 | 25 | 23 |

Observed on the published detector (invented witnesses): the Han-only lines for a bay, a coastline and a voice-actor phrase come out sure Chinese, an invented Japanese phrase containing `開始` and a name containing `萬` come out sure Traditional. For `台湾`, `開幕`, `公開`, `開始` nothing separates Japanese from Chinese, so the right answer is `undefined`, and the current answer is a false certainty.

Leak pruning, learned on the even half of the Japanese lines and scored on the odd half (16,424 Japanese lines, 4,961 Chinese):

| Traditional-only list | Chinese lines hit | Japanese lines hit |
|---|---|---|
| Base minus jōyō (3,389) | 57.1 % | 1.10 % |
| Minus jōyō and jinmeiyō (3,130) | 44.6 % | 0.56 % |
| Base minus 53 leaking characters (3,336) | 52.8 % | 0.13 % |
| The 45 characters in the code today | 37.2 % | 0.33 % |
| First 45 of the pruned, frequency-ranked list | 38.7 % | 0.01 % |
| First 100 | 45.8 % | 0.02 % |
| First 200 | 49.9 % | 0.02 % |
| Minus all of JIS X 0208 (2,085, no pruning) | about 11 % | about 0 % |

The 53 leaking characters are Japanese names and rare words (31 jinmeiyō, 21 JIS X 0208 only, 1 neither); one of them alone occurs in 100 Japanese lines. The conclusion: exclude jōyō only, then prune against a Japanese corpus; excluding all of JIS X 0208 throws away most useful Chinese markers for under one point of Japanese false hits. The ranking comes from Taiwan gaming chat, so recall on Hong Kong or Singapore text is unverified.

No corpus contains a Japanese line without kana among its test lines (public-corpus Japanese: 0 of 120; one labelled chat set: 0 of 25), so no existing test could see this leak. A code comment claims the Japanese overlap is handled, but it only protects lines that carry kana.

### M5. Bopomofo is counted nowhere

U+3105 to U+312F and U+31A0 to U+31BF are the clearest sign of Taiwanese chat (a shorthand where one letter stands for a common syllable or particle). They make up 0.79 percent of distinct Chinese lines (80 lines; 0.61 percent of lines). Observed: `undefined` or an unsure `zh`, never `zh-tw`. Letters by line count: ㄟ 22, ㄤ 9, ㄇ 8, ㄌ 8, ㄏ 7, ㄚ 7, ㄅ 7, ㄜ 5, ㄨ 4.

### M6. The source-language allowlist drops Han lines

`shouldDropBySourceLang` (`K:filters.ts:81`): an `undefined` guess gives `lang_unknown` and the line is dropped, and the comparison is strict, so `zh` differs from `zh-tw` although the selector offers both. Measured on the plain guess path (`detectLanguage`, the path of TCT and of Firefox without the API):

| Allowlist | Chinese lines dropped, test set (167) | Chinese lines dropped, chat sample (11,080) |
|---|---|---|
| `['zh']` | 85 (50.9 %; 65 detected `zh-tw`, 17 `undefined`) | 5,860 (52.9 %) |
| `['zh','zh-tw','yue']` | 20 (12.0 %; 17 in `lang_unknown`) | 1,730 (15.6 %) |
| `['ja','ko']` | 6 of 296 (2.0 %) | 544 of 15,628 (3.5 %) |

For KCT in Chrome or Brave the allowlist reads the browser verdict (`pipeline.ts:291` and `:332`), which is not measured outside a browser. The reviewer did not mention it, so the plan treats it only if measurement gives it weight, and never merges a semantics change for it without the owner.

### M7. Browser APIs do not repair this alone

`chrome.i18n.detectLanguage` is already wired (`K:langDetect.ts:2720`, `K:pipeline.ts:291`). Its engine is CLD3, which returns a single `zh` for all Chinese, no `yue`, and marks every input under 50 UTF-8 bytes unreliable. A Han character is 3 bytes, so any line shorter than 17 characters is flagged unreliable by construction. On a labelled set it returns `zh` for all 6 Japanese lines without kana, all unreliable. It feeds the allowlist, the flag and the English skip, not the sure gate at `:329`.

`LanguageDetector` (web API, Chrome 138, Edge 148): measured on 25 November in `--headless=new` with throwaway profiles. Brave: `typeof LanguageDetector` is `undefined` (hard-disabled in its renderer, a Brave browser test asserts its absence, and its engineer said on 20 November it will not be re-enabled as is). Chrome 158 and Edge 158: the function exists and `availability()` returns `unavailable`. Labels are the CLD3 set plus `zh-Hans` and `zh-Hant` by script classification (ties go to `zh-Hans`), no `yue`. No published number exists for short chat or for kana-less Japanese. It is exposed to windows and extension service workers, not to dedicated or shared workers. A design that needs it would give nothing in Brave, so the script layer must carry the load. Other detectors read: franc-min (100 KB, only `cmn`, `jpn`, `kor`, all Han mapped to `cmn`), tinyld (zh, ja, ko, no `yue`, its Asian test languages exclude Han-only Japanese), a rule-based Cantonese detector (MIT, precision 0.983 and recall 0.966 on 420 Hong Kong sentences, in the 2024 EURALI paper), fastText (CC BY-SA, has `yue`, no Hans or Hant). No source read reports a Han-only Japanese versus Chinese accuracy, nor a Traditional versus Simplified identifier on chat-length text.

### M8. TCT is a frozen copy of an older KCT

`T:langDetect.ts` has a single commit in its history: a copy of KCT at 3.3.0 (2026-10-16). It is 2,531 lines against 2,786. KCT made 15 non-merge commits touching the detection core files since then (11 on `langDetect.ts`), none of which reached TCT. The Han layer (`detectByScript`, `cantonaisOuChinois`, the three tables) is byte-identical (`T:langDetect.ts:2230-2381` equals `K:2373-2524`), as are the M1 gate (`T:pipeline.ts:648`) and the same-language gate (`:316`).

Differences that touch Han lines: TCT keeps the older `isNoise` rule that drops `好好` and `对对对` (KCT keeps them through a syllable-word exemption), and `T:pipeline.ts:271` drops a lone `好` (length 1 under 2; KCT counts a Han character as 2 through `chatLength`). TCT has neither `trimForEngine` nor `chatLength`, and its channel language (`T:twitchApi.ts:111`) reaches only the composer. `T:src/content/pipeline.ts` contains 2 NUL bytes, so a plain search skips it and an edit must be checked with `git diff --text`. Porting the 12 missing detection commits was left out of scope and listed for the owner.

### M9. No existing set can judge this work, and the data is thin

- The development set has no Chinese line (Japanese 76, Korean 12, and one Japanese line without kana). The public-corpus Chinese sets are circular (a `cmn` export cut by the same marker lists the rules read). A later labelled set has 167 Chinese lines in 9 channel units, mostly from Taiwan, with no `zh-tw` or `yue` label, and 6 Japanese Han-only lines. The earlier cost panel has no CJK reader and ignores M1. A linear model from the earlier study is worse than the rules on Chinese (0.450 against 0.312).
- Raw chat on the machine: 3,215,059 lines in 237 files, all from one evening (2026-11-22, 16:00 to 22:00 UTC, which is midnight to 7 a.m. in Taiwan). Declared language by platform: Kick Japanese 42,659 lines (170 units), Kick Chinese 187 (1 unit), Kick Korean 33 (2); Twitch `ja` 9,347 (22 units), `zh` 14,253 (44 units), `ko` 259 (12 units), unknown 21,592 (36 units). No `yue`, `zh-TW` or `zh-Hans` label exists anywhere. Chinese here is Taiwanese Twitch, with one unit carrying 66 percent of the lines of the last hour.
- Han-only share by class: 66.4 percent of Chinese lines (6,847 of 10,315 before the cutoff), 88.6 percent in the labelled set (148 of 167), but only 2.0 percent of Japanese lines (989 of 48,954). Length of Han-only lines: Japanese 61.5 percent are 2 characters or fewer; Chinese 20.0 percent.
- Marker split of Han-only Chinese lines, before the cutoff: no marker 3,850, Traditional 2,925, Simplified 72. Of Han-only Japanese lines: no marker 850, Traditional 94, Simplified 44.
- Cross-class collisions: 11 distinct texts (123 lines) appear in both Japanese and Chinese channels, so a label from the channel is noisy on exactly the lines that matter. 794 Han-only lines come from channels with an unknown declared language.
- The declared-language label separates `ja` from `zh` well (0 confusion on 463 labelled lines) but only 154 of those lines are Han-only (6 Japanese), so on Han-only lines its error bound is about 2 percent and 4 of 672 Han-only lines of Japanese channels are in fact Chinese. 8.4 percent of Chinese test lines come from channels not declared Chinese. Declared Korean on Twitch is Korean only 1 time in 20.

Confident answer of the published detector is itself precise: 3 wrong hints of 1,066 given on clean sets (99.72 percent), 1 of 356 on the labelled set, 162 of 19,283 on the raw pool (125 of them label-noise candidates). Simulated wrong skips on 1,244 clean eligible lines: 1 for a Japanese reader, 2 for a Chinese reader (both labelled Cantonese but standard Chinese). On the pool sample of 26,708 eligible script-bearing lines: wrong skips 32 for a Japanese reader (0.3 percent; 27 kana inside an `@` display name, 5 Japanese words in a Chinese line, 0 decorative kana), 8 for a Chinese reader, 117 for `yue`, 0 for Korean. The earlier cost function (weights unchanged, readers replaced by `ja zh zh-tw yue ko` plus an allowlist reader) gave 0.1362, 0.1326 and 0.1269 on the labelled set for the three browser detectors, carried by silence (0.0967 of 0.1362), 0.0895 on clean sets and 0.1886 on the pool.

The upshot of the baseline: wrong skips are already near zero on every set, so the measurable gain is in silence (about 61 percent of Chinese lines go to the engine) and in the allowlist semantics, and if the reviewer's symptom is the post-request skip the lever is the gate and an engine probe, not the detector.

## 5. Linguistic evidence behind the table design

- Unicode (UCD 18.0.0): hiragana letters U+3041 to U+3096 and U+309D to U+309F, katakana letters U+30A1 to U+30FA, U+30FD to U+30FF, U+31F0 to U+31FF and half-width U+FF66 to U+FF6F and U+FF71 to U+FF9D. The prolonged mark, middle dot and U+30A0 are Common-script punctuation shared with other scripts; U+3001 and U+3002 are shared by all. Bopomofo U+3105 to U+312F and U+31A0 to U+31BF. Han has 103,352 code points; the current regex counts the 64 Yijing hexagrams and ignores planes 2 and 3, `々`, `〆` and `〇`. Hangul misses conjoining jamo U+1100 to U+11FF and half-width forms. Full-width forms need NFKC first or the Japanese `ｗｗｗ` and the Chinese full-width comma are lost, but NFKC applied globally changes other results, so the plan applies it only locally.
- Unihan recipes: Simplified-only = characters in the GB set whose Traditional variant differs, minus Taiwan, minus every Japanese standard, minus Korean (2,358). Traditional-only = characters in the Taiwan or Hong Kong sources with a different Simplified variant, minus GB, minus jōyō or jinmeiyō or JIS (3,389, 3,130, 2,085 or 817 by how much is subtracted). Japan-only = jōyō plus jinmeiyō minus GB, Taiwan and Korean (256; 674 with JIS X 0208). An OpenCC cross-check found that its Japanese shinjitai list is not a Japan-only list (215 of its 403 keys are also Simplified forms), so it was not used.
- Sizes (UTF-8 literal / gzip): Japan-only 256 characters 769 / 602 bytes; Traditional pruned 3,336 characters 10,008 / 7,142; a three-class code point map over the Han block is 27,648 bytes raw and 3,153 gzipped. A literal string beats a range form for frequency-ordered subsets.
- Weight budget: the content script is gated at 2 percent of 69.0 KB gzipped (about 1,413 bytes). Proposal B (411 characters, 940 bytes gzip, 575 net) fits; proposal A (722 characters, 1,640 bytes gzip, 1,275 net) is at the edge; the full sets (13,013 bytes gzip, 19 percent of the budget) do not fit without a deliberate baseline reset. Precedent: the Cantonese round added 5.2 KB gzip (5 percent).
- Function words with zero Japanese lines and 0.3 to 10 percent of Chinese lines (decisive Chinese evidence): 吧 2.46, 啊 1.93, 呢 0.39, 哦 0.29, 喔 3.09, 欸 1.88, 她 0.45, 嘛 0.35, 嗎 4.69, 沒 5.80, 很 4.05, 麼 3.83, 什 1.46, 怎 1.67, 你 10.09, 們 1.24, 吃 2.82, 會 5.23, 對 1.61, 說 2.17, 點 2.51, 裡 0.82, 甚 0.28, 啥 0.66, 偷 0.92, 玩 2.28 percent. Weak evidence that must never decide, because they occur in Japanese chat: 的 (143 Japanese lines), 了 (11), 他 (90), 那 (8), 係 (85, deliberately not a Cantonese marker), and 在 有 我 都 個. A statistically selected 181-character function set overfitted a 336-line Japanese sample and leaked 11.3 percent into held-out Japanese lines, so the plan uses 18 hand-picked characters and checks the leak on 32,000 lines.
- Cantonese: the current list (38 characters plus words) was compared with a published rule-based detector (77 single characters plus about 40 collocation patterns); 8 characters are in the Mandarin standard charset (weak markers). The plan adds no Cantonese marker, because no Cantonese data exists to judge it.
- Digits never vote (the short-word splitter splits on non-letters), and `isNoise` drops digit-only lines before detection, so laughter and number codes (888, 666, 233, 5555) never reach the detector in the pipeline. A Han procedure must ignore digits.
- Literature read: a 1997 CJK algorithm note (order: Hangul, kana, Simplified-only, Chinese-only, words); a 2022 issue on a Rust language detector closing kanji-only Japanese as unrealistic; a 2016 sentence-level Greater China dialect study (character bigrams, 2-way 98.42 percent, 6-way 74 to 89 percent on news); a 2019 platform note on a character-level model for `zh-hans`, `zh-hant` and `ja` on strings up to 5 characters.
- Licences: Unihan data (Unicode License v3, permissive, notice must travel with copies) and the jōyō list (Cabinet notice of 2010, outside Japanese copyright by Article 13, an inference and not legal advice) are allowed. The CC-CEDICT and CC-Canto data (CC BY-SA) must never go in an MIT bundle. OpenCC (Apache 2.0) and the Cantonese detector (MIT) are unnecessary. fastText `lid.176` is CC BY-SA and NLLB `lid218` is CC BY-NC.

## 6. The plan that came out of it

### 6.1 Candidate changes

- F1 (M1): a pure function `trustedVerdict(verdict, text)`. If the verdict's base language is `en` and the text contains a non-English letter, the verdict is discarded (becomes `auto`). It never falls back to the unsure guess, because that would feed an unsure answer into a deleting gate. It applies at the entry of the shared apply path, so cached verdicts (kept 72 hours) are covered too. F1 only lifts suppressions.
- F2 (M3, M4, M5, then M2), in stages, one commit each: (a) strip mentions and URLs from the script count and count only kana letters, keeping `ー` and `・` in the total; (b) prune the Chinese tables (remove `声` and `湾` from the Simplified list, replace the 45 Traditional characters by the first 45 of the pruned ranking, drop `嬲` from the Cantonese list); (c) bopomofo reads as `zh-tw`; then three additive stages gated by thresholds: (d) the 256 Japan-only characters give `ja`, (e) compact Traditional and Simplified lists (proposal B retained if within 3 points of A), (f) 18 Chinese function characters.
- F3 (M6): compare `zh` and `zh-tw` by base language in the allowlist and let an unknown Han line through. Prepared at most, never merged by the work, because the visible behaviour is the owner's call.
- F4: an unknown Han line whose engine verdict is the reader's language (two Japanese words that are also Chinese, for a Japanese reader). Three options measured, one retained, never merged.
- Phase 6 (browser `LanguageDetector`): kept but gated on the owner confirming `available` in their own Chrome, a measured residue F1 and F2 leave, and a feature-detected, memoised, off-hot-path call. Probably not done.

### 6.2 Measurement design

- Two line sets cut by time. `design`: the chat of the evening above. `fresh`: later collection cycles from a remote collection server, Twitch only, with duplicates removed against everything already used (NFKC, lower case, digits to 0, repeats of 3 or more letters to 2). Sets are sealed by SHA-256 and by the list of kept identifiers before any tuning. Service verdicts are collected once and frozen. One request per distinct text, 0.5 s apart, one attempt, stop on HTTP 429 or invalid JSON, with a persistent counter.
- Sample sizes (distinct texts per set): at most 5,000, 40 percent `ja` and 60 percent `zh`, half Han-only in each class, Korean everything available (at most 400); duplicates removed before capping (3 lines per text and per unit, 60 per unit); at least 30 units and 200 lines per class for a bootstrap, otherwise reported without a verdict.
- Label audit: 400 random Han-only lines (200 Japanese-declared, 200 Chinese-declared), two independent annotators (4 batches of 100) plus 20 invented gold lines; mentions replaced by `@uN`, emote names removed, neither the declared language nor the channel shown; an agreement of both is gold, a single `han-ambiguous` is a disagreement; disagreements form an `undecidable` class reported apart; above 3 percent disagreement in a class the work stops and tells the owner. Two annotators of one model family are not independent evidence.
- The bench runs the real gates, extracted as pure functions and called by both the pipeline and the bench, for readers `en`, `ja`, `zh`, `zh-tw`, `ko` (with `ignoreEnglish` on and a minimum length of 2) and three allowlists. Counts per (reader, class), never one aggregate: W lines wrongly deleted (weight 10), S wrong source hints (5), K kept for nothing (1), Z silence (0.5). The weights come from the earlier study so results stay comparable. Paired bootstrap by chat unit, 1,000 draws, seed 0.
- Two printed columns on Han-only lines: Chinese silence, and Japanese leak (Japanese Han-only lines that get a sure Chinese answer over all Han-only Japanese lines; for the Japan-only rule, Chinese lines that get `ja`).
- Speed bench: median of 3 alternating runs in two processes, 5,000 lines. Weight is measured on the release build.
- Mandatory controls, each of which must go red first: reference against itself gives exactly 0; a deliberately broken candidate must lose with an interval excluding 0 (for the first change, feeding the unsure guess to the sure gate when the hint is undefined; for the second, a rule that answers `zh` for every Han-only line); the 89 witness lines must reproduce the expected output byte for byte on the unchanged code and on the extraction commit; a parity test checks that the bench takes the same decision as the real pipeline on 40 lines (10 or more skipped by the sure gate, 10 or more by the verdict gate) with a faked engine.

### 6.3 Decision rule, pre-registered before the fresh set is scored

Three outcomes per criterion: PASS, FAIL, or UNDERPOWERED (fewer than 30 units, fewer than 200 lines, or fewer than 10 units carrying lines concerned by the criterion).

1. W: no cell (reader or allowlist, class) rises by more than 2 lines; the sum of rises is at most 5 percent of the sum of falls.
2. S: no class rises by more than 2 lines.
3. Cost of the `en` and `ja` readers: mean paired difference negative with an upper 95 percent bound under 0. For `ja` power is low (M3a touches 0.2 percent of Chinese lines), so the criterion may read "mean difference negative or zero and no unit rising by more than 1 W" when the interval cannot exclude 0.
4. Speed: p95 of per-line detection time at most 1.25 times the reference, median at most 1.10.
5. Content script grows by at most 4,000 bytes gzip.
6. First change only: K of the `en` reader on Latin lines rises by at most 0.5 percent (F1 sends English lines that carry an accent again).

Attribution of each affected line to a mechanism by the first true rule, in this order: M1, M6, M3a, M3b, M4, M5, M2. Overlaps are counted in each and reported apart. A FAIL is published as it stands and the method is not tuned on the fresh set. A second failure of the same method means change layer.

The fresh set is read once, after the code is frozen, and scores each prefix of the second change in order; the second change is the longest prefix with no FAIL, later steps are removed by commits, never by a second reading. A second candidate needs a new set of lines.

### 6.4 Merge and delivery rules

- First change (extraction commit, bench, F1, F2(a)) merges when CI is green (3 jobs), the controls are green, and, on `design` only, criteria 1, 2, 4, 5, 6 pass and the `en` and `ja` readers' W falls or stays equal. F1 only lifts suppressions and F2(a) only removes mentions and non-letters from detection, so both are deterministic guards that do not need the fresh set. The description says that previously deleted lines will now be sent to the engine and will consume user quota.
- Second change (F2 (b) to (f)) stays a draft until the fresh set is read; it merges only if no criterion is FAIL or UNDERPOWERED and no allowlist cell rises in W; otherwise it stays ready and the owner decides.
- TCT follows the same two steps after the Kick ones, starting from its own extraction commit as reference, with its own pinned totals re-pinned from a confusion diff and never copied from KCT. The 12 missing detection commits are listed, not ported. TCT's older noise rules (the dropped `好好`) are touched only if measurement shows useful lines lost.
- A real-browser proof: an English reader and an invented Traditional line answered `en` by a faked engine (the published build skips it, the new build shows the translation; an English line answered `en` is skipped by both), and a Japanese reader with an invented kana nickname, offline, with a real pass of 10 invented or public-corpus lines.
- Tags, releases, store uploads and announcements only on the owner's order. No visible string, permission or dependency is added. No line of real chat goes into git.

### 6.5 Permissions the brief grants, and their bounds

- Service requests: 14,000 at most in total (design 5,000, fresh 5,000, F4 2,000, margin), one per 0.5 s, one attempt per text, persistent counter, stop on 429. Duration about 2 hours per 14,000. Texts are sent without nickname or `@` mention or links; the verdict for the nickname case is therefore measured without the nickname although production sends it, and the report says so.
- Collection server: read only, `nice` and `ionice` at lowest priority, a load sample (`vmstat`) before each file group with the last data line read and steal at most 30, one group at a time, 100 MB at most, hashes checked against the remote. The server carries live broadcast, which is why the brief carries those bounds (a past large transfer there pushed steal to 55 to 75 percent and cut a live stream).
- Annotation by sub-agents: 1,200 at most.
- Merge by `gh pr merge --merge` on green CI only. One new documentation page per repository (the one exception to a no-unrequested-docs rule), holding the pre-registered rule, the counts and the Unicode notice.

## 7. How the plan was reviewed

- Research: two waves, 11 read-only agents (code map, consumption of a result, TCT versus KCT, the earlier study, browser APIs, repo conventions, then data inventory, a measured baseline, the linguistic audit), plus direct probes by the lead: 118 invented phrases and 780 public-corpus sentences against the service, 89 witness lines through the published detector, the browser API check in real browsers with throwaway profiles.
- Review: two adversarial rounds of four reviewers each (facts against code, numbers against evidence, executability, design critic; then facts and numbers, logic consistency, executor simulation, policy and safety). Round 2 produced 75 findings, all folded in. Examples of what they caught:
  - The first change could not satisfy its own pre-registered rule: criterion 3 demanded a falling `ja` reader cost, but F1 changes nothing for that reader (difference exactly 0). The rule became per candidate.
  - The fallback "return to the guess when the verdict is discarded" would have fed an unsure answer to a deleting gate and added suppressions, contradicting the claim that F1 only lifts them. It became `auto`.
  - Reading "do not count `ー` and `・` as kana" literally would have made `あー`, `えー`, `ラー` fall under the two-character floor and flip from `ja` to `undefined`. They stay in the total, and became witnesses.
  - The exposure estimate used the corpus rate instead of the chat-style rate (see M1).
  - The real-browser script the brief pointed to could not run as described (it imported a missing folder, overwrote its own environment variable, blocked all network, and answered a fixed Spanish verdict); the brief now says it is a model to adapt.
  - The bench could not import the pipeline under plain Node, so parity became a vitest test not committed.
  - TCT has none of the extracted functions nor `trimForEngine`, so the TCT reference had to be its own extraction commit and the service verdict key had to be replayed with the text TCT sends.
  - No network cap or live steal check was foreseen for the collection server; both were added.
- Sealing: held-out data stayed unread by the whole research. One agent loaded a file containing held-out rows into memory and kept only the development and public-corpus sets; one shell command listed the two held-out file names and was blocked by the permission classifier. No content was read.

## 8. Mistakes caught during the research

- A condensed summary of M2 stated a wrong leak count (4 Chinese lines of 672 given `ja`); caught by comparing with the reviewed text, and the condensation was dropped.
- A function name was cited as existing in TCT while it exists in neither extension; it is now declared new.
- The date a collection cap was reached was first guessed (about 09:12 on 23 November, probably the server's local time), then replaced by a read of the server log: the Japanese class is first capped at the cycle launched at 11:11 and the Chinese class at 14:52, the server is on CET, and the cap applies at the launch of a cycle.
- The first reading of `vmstat 2 3` was ambiguous: the first data line is the average since boot, so the brief says to read the last data line.
- "At least 2 hours" for 14,000 requests at 0.5 s is 1 h 57, so "about 2 hours".
- A section title said "ten lines" for eight items.
- A kaomoji containing a backtick broke a Markdown code span.
- A first report of the kana-in-mention case said KCT was not exposed because the detector receives text without mentions; execution in both extensions showed it is exposed for non-ASCII nicknames.
- A statistically selected function-word set overfitted (11.3 percent leak) and was replaced by a hand-picked one.
- No third review round was run after the 75 fixes. Cross-references, paths, banned characters and the KCT line references were rechecked by hand (66 of 66); the TCT line references were not.

## 9. Witness lines (invented, run on the published detector)

The detector's `detectLanguage` guess and `confidentLanguage` sure answer for each. These are the controls the plan reproduces byte for byte (89 rows in the full output, a selection here). "Sure" is what decides `sl` and the pre-request skip.

| Group | Example (invented) | Gold | Guess | Sure |
|---|---|---|---|---|
| Chinese with a soft kana or a mark (M3b) | ``你好嗎ヽ(´ー`)ノ`` | zh-tw | ja | ja |
| | `主播今天好帥ー` | zh-tw | ja | ja |
| | `史蒂夫・賈伯斯` | zh-tw | ja | ja |
| | `我の朋友好棒` | zh-tw | ja | ja |
| Real Japanese, few kana (controls) | `神の一手`, `草生える`, `うーん`, `ナイス` | ja | ja | ja |
| Japanese without kana, Japan-only forms (M2) | `歴史的瞬間` | ja | zh | undefined |
| | `圧勝`, `逆転`, `観戦`, `売上` | ja | undefined | undefined |
| Shared forms in Chinese tables (M4) | `声優最高`, `東京湾`, `湾岸` | ja | zh | zh |
| | `独裁開始`, `萬斎` | ja | zh-tw | zh-tw |
| | `台湾`, `開幕`, `公開`, `開始` | ambiguous | zh or zh-tw | same |
| Han-only, nothing decides | `草`, `初見`, `神回`, `大丈夫` | ambiguous | undefined or zh | undefined |
| Chinese without a marker | `太強了`, `太强了`, `主播好帥` | zh-tw or zh | zh | undefined |
| Chinese with a marker (controls) | `這個遊戲真的很好玩`, `主播好帥嗎` | zh-tw | zh-tw | zh-tw |
| Bopomofo (M5) | `好ㄉ`, `ㄏㄏㄏ`, `對ㄚ` | zh-tw | undefined | undefined |
| | `晚安ㄌ大家` | zh-tw | zh | undefined |
| Cantonese | `你食咗飯未` | yue | yue | yue |
| | `好正啊` | yue | zh | undefined |
| Korean with hanja | `한국 韓國` | ko | zh | undefined |
| | `韓國人 한` | ko | zh-tw | zh-tw (known limit) |
| Han plus Latin | `gg 说得对` | zh | zh | zh |
| | `ww 草` | ja | es | undefined |
| Number codes | `666`, `233`, `888` | none | en | undefined |
| Kana nickname in a mention (M3a) | `@ゆきだるま 這可以嗎0.0` | zh-tw | ja | ja |
| Floor cases | `あー`, `えー`, `ラー`, `先輩ー？`, `最強の犬ww` | ja | ja | ja |
| | `ー`, `は` | amb / ja | undefined | undefined |

After the planned changes the plan expects: the `ー`-or-`・`-only kana rows stop being `ja` while the rows with a hard kana, a soft kana alone, or `あー`-like lines stay `ja`; the shared-form rows become `undefined`; the bopomofo rows become `zh-tw`; the mention row becomes `zh-tw` (by `嗎`) after the table step; the invented Japan-only rows become `ja`.

Of 40 hand-judged lines, the published detector was wrong or misleading on 11, and the new rules answer unknown on 13, of which 9 are genuinely ambiguous. Five more are decidable only with larger lists or word knowledge.

## 10. What is not proven

- The reviewer's exact line and reader language are unknown, so the main cause is a measured mechanism, not a confirmed diagnosis of that review. Only an example line, a channel and a reader language would confirm it; the store listing allows asking.
- Every number comes from one evening of Taiwanese Twitch chat plus Japanese chat of the same window. Kick chat, Cantonese, Hong Kong or Singapore Chinese, mainland Simplified chat (54 lines with a Simplified marker) and Korean cannot be proven by this data. The Simplified list has no real-chat evaluation worth the name.
- Labels are channel-declared. 117 lines of Chinese-declared channels are read as Cantonese by the detector, unverified (no Cantonese gold exists).
- Proposal B was not measured. Ten jinmeiyō characters stay in the Traditional list for lack of occurrence in the Japanese chat measured, a residual risk for proper names.
- A hard kana alone inside a kaomoji (`ツ`, `ヮ`) still gives a sure `ja` on a Latin or Chinese line (not measured).
- The collection server's counters overshoot its own cap (Japanese 137,907 and Chinese 127,237 against 100,000, which is 38 and 27 percent over) for a cause not found, so the number of fresh lines per language per cycle was not measured.
- The service can change its behaviour. The first phase of the brief replays 20 fixed probe lines and stops on any difference, and the last phase replays them again.
- Allowlist behaviour in KCT inside Chrome and Brave (browser verdict) is not measured outside a browser.
- Two annotators from one model family are not independent evidence. They agreed on 468 of 469 labelled CJK lines, which cannot separate an easy line from a shared blind spot.

## 11. Outcome

See [case 001](001-han-script-detection.md) for what was implemented, merged and measured (KCT pull request 91 and TCT pull request 26, both merged on 2026-11-25), and for the parts that stayed a draft. That case reports its own sets (a design set of 3,608 distinct lines, with the service verdict collection cut by a rate limit after 1,133 lines and the held-out set never scored), which is a narrower outcome than the plan above foresaw. The two documents were written by different working sessions and differ on set sizes and wording; where they differ, case 001 is the record of what was run.

## 12. Not published

The working dossier (raw probes, derived tables and lists, review reports, the 83 KB implementation brief) stays private: it holds local paths and data derived from third-party chat. This repository keeps counts and method only.
