# Case 001, research thesis: why Han-script lines were not translated, and how the fix was planned

Date: 2026-11-25. Products: Kick Chat Translator (KCT) and Twitch Chat Translator (TCT). Companion to [case 001](001-han-script-detection.md), which reports what was changed and measured. This file reports the research that came first: what was claimed, what was checked, what turned out wrong along the way, and what is still open.

## Thesis

A store review said that lines in languages written with Han characters (Chinese, Taiwanese, Japanese) are taken for the reader's own language and are not translated. The research found that this symptom has several independent causes, not one, and that the heaviest one is not in the local language detector at all:

1. The translation service itself answers `en` for a large share of short traditional Chinese, and the pipeline deletes the line after the call when that answer equals the reader's language, with no check on the script. An English reader loses those lines after they were already paid for in requests.
2. The local detector has smaller, separate defects: a kana-range that is too wide, shared character forms listed as Chinese-only, no bopomofo handling, and most Han-only lines carrying no usable signal.
3. A strict source-language allowlist can drop half of the Chinese lines for a reason unrelated to detection.

So the right plan is a short list of small guards, each measured before and after, rather than a new detector. A browser language-detection API was checked as a possible lever and is not one today.

## The request and its scope

The review gave no example line and no reader language. The workaround it reported (turning off "skip messages already in my language") matches exactly one of the two gates that delete a line, which became the first lead. A second remark in the review (start a new page by hand) is a separate feature and was left out.

The owner chose to improve detection itself rather than translate everything in doubt.

## What was established (counts only)

M1. The service verdict. With `sl=auto`, the service returned `en` for 148 of 150 unmarked traditional Chinese sentences from a public sentence corpus and for 12 of 34 invented chat-style lines, with a correct translation each time, and `zh-CN` for 150 of 150 simplified ones. The answer does not depend on the target language or the client parameter. The post-call gate in KCT (`pipeline.ts:705` at the commit studied) deletes the line on that verdict. The gate the reviewer's toggle controls is exactly this one plus the first one; the "same language, sure" gate before the call is not behind the toggle. Not reproduced on the reviewer's own chat, since no line was given.

M2. Silence. 59.7 percent of Han-only Chinese lines have no sure answer from the local rules. A compact list built from the Unihan database (about 1.6 KB gzip) cut silence on those lines to 32.2 percent, decided 17.0 percent of Han-only Japanese lines, and leaked 1 line out of 672 (0.15 percent) to the wrong language. A smaller variant was designed but not measured.

M3. Kana. The accepted range was wider than writing. (a) A kana nickname after an `@` survives the mention pattern, which only sees Latin letters, and gives a sure Japanese verdict: 27 of 11,280 eligible non-Japanese lines (0.24 percent), all from one platform. (b) Decorative use of the long-vowel mark or the middle dot inside Chinese was looked for and not found: 0 in 14,440 Chinese lines, while 98 of 100 lines whose only kana were such signs were real Japanese. The research therefore advised against tightening those soft signs, and the fix kept to what was measured.

M4. Shared forms. Some characters in the Chinese tables are also ordinary Japanese (three common ones and 17 name-use characters), which makes Japanese lines read as Chinese.

M5. Bopomofo is not counted by the detector (0.79 percent of distinct Chinese lines in the sample).

M6. Allowlist. A source-language allowlist of `['zh']` drops 50.9 and 52.9 percent of Chinese lines on the two samples because the engine labels most of them `zh-tw` or unknown; `['zh', 'zh-tw', 'yue']` drops 12.0 and 15.6 percent. This is a settings semantics question and was kept out of the detection fix.

M7. Browser API. The built-in language detector does not exist in one Chromium-based browser tested and reports `unavailable` in two others in fresh profiles. It cannot be the lever for now. The extension already calls the older i18n detector.

M8. The Twitch extension is a frozen copy of an older Kick version: its Han layer is byte-identical, and 12 detection commits are missing. Porting was planned as its own step.

M9. No existing labelled set could judge the change. One earlier set has no Chinese, another was spent. The available data is one evening of one chat plus a collection cycle, which limits what can be proven (see below).

## How the research was run

- Two waves of read-only investigation (11 agents): code map, how a result is consumed, differences between the two extensions, the earlier language-ID study, browser APIs, repo conventions; then data inventory, a measured baseline, and a linguistic audit of the tables.
- Direct probes by the lead: 118 invented phrases and 780 public-corpus sentences against the service, 89 witness lines run through the published detector, and the browser API check in real browsers with throwaway profiles.
- The result was an implementation brief for a smaller model. It went through two adversarial review rounds of four reviewers each (facts against code, numbers against evidence, executability, design). All 75 findings of the second round were folded in.
- Sealed data was never opened by the research: held-out sets stayed unread, and the plan froze sets by hash.

## What the brief decided

- Measure before fixing: a design set (one chat evening) and a fresh set (later collection cycles, Twitch only), cut by time, sealed by hash, service verdicts frozen once.
- A bench that runs the real gates per reader language and counts, with weights for lines deleted wrongly (10), wrong source hints (5), kept-for-nothing lines (1) and silence (0.5). Controls first: the reference against itself must score exactly 0, a deliberately broken candidate must lose.
- A decision rule written before scoring, with outcomes pass, fail, or underpowered.
- Two pull requests per extension. Step 1 (verdict guard, mention and mark fixes) is safe enough to merge on design data. Step 2 (tables, bopomofo, compact lists) stays a draft until the fresh set is read once. The allowlist change and any new verdict option are never merged by this work.
- Bounded permissions: a capped number of service requests with a persistent counter and a pause between requests, read-only access to the collection server with a load check before each step, capped annotation, and tags, releases, store uploads and announcements only on the owner's order.

## Mistakes caught during the research

- A condensed summary of M2 stated a wrong leak count; it was caught by comparing with the reviewed text and the condensation was dropped.
- A function name was cited as existing in one extension when it exists in neither; it is now declared new.
- The date a collection cap was reached was first guessed, then replaced by a read of the server log.
- A kaomoji containing a backtick broke a Markdown code span.
- A duration estimate was off (14,000 requests at 0.5 s is about 2 hours, not "at least 2").
- No third review round was run after the last 75 fixes. Cross references, paths, banned characters and the KCT line references were rechecked by hand; the TCT line references were not.

## Not proven

- The reviewer's exact line and reader language are unknown, so the main cause is a measured mechanism, not a confirmed diagnosis of that review.
- Kick chat, Cantonese and Korean cannot be proven by the data on hand.
- The collection server counts overshoot its own cap for reasons not found, so the volume of fresh lines per language is not known.
- The service can change its behaviour; the first phase of the brief replays the probes and stops on any difference.
- Two annotators from one model family are not independent evidence.

## Outcome

See [case 001](001-han-script-detection.md) for what was implemented, merged and measured (KCT pull request 91, TCT pull request 26, both merged on 2026-11-25), and for the parts that stayed a draft.

## Not published

The working dossier (raw probes, derived tables, review reports, the full brief) stays private: it holds local paths and data derived from third-party chat. This repository keeps counts and method only.
