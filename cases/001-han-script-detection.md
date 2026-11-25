# Case 001: from a store review to a measured change (Han-script lines)

Date: 2026-11-25. Products: Kick Chat Translator and Twitch Chat Translator (same detection code).

## The request

A five-star review of the Twitch extension said, in short: free, unlimited, the best extension the reviewer had found; but for languages written with Han characters (Chinese, Taiwanese, Japanese) the detection is often wrong, the line is taken for the reader's own language and is not translated. The reviewer worked around it by turning off "skip messages already in my language", at the risk of side effects, and guessed that closely related languages in other regions behave the same. A second remark (start translating a new page by hand instead of automatically) was a separate feature and was left out of this work.

The owner chose to fix the detection itself, not to translate everything in doubt.

## What "taken for the reader's language" can mean

Two gates delete a chat line before the reader sees it, and the review does not say which one fired or what the reader's language was, so the first job was to name every path:

1. the local detector is confident the line is in the reader's language;
2. the translation service answers, after the call, with the reader's language.

Measured paths, each with a counted example on a real chat sample:

- The service answers `en` for a large share of short traditional Chinese. For an English reader the second gate then deleted those lines (329 of the 1,133 design lines that have a stored verdict, 14 Japanese and 315 Chinese, were deleted by this path).
- Kana inside an @mention or a link made a Chinese line read as Japanese, so the first gate deleted or mis-sourced it for Japanese readers.
- The middle dot and the long-vowel mark are written by Chinese chat as well, but counted as Japanese kana.
- Some characters were listed as Chinese-only although Japanese writes them too.

## Method

- Two line sets cut by time: a design set (3,608 distinct lines) and a held-out set (3,655 lines, collected later, scored once). Both frozen by hash before any scoring.
- A bench that runs the real gates, per reader (English, Japanese, Chinese, Traditional Chinese, Korean) and per declared language class, and counts: lines wrongly deleted (weight 10), wrong source hints (5), kept-for-nothing lines (1), silence (0.5). Never a single aggregate (a previous study hid a cost of +0.138 on Chinese inside one).
- The decision rule was written and committed before the held-out set was scored. A paired bootstrap by chat unit gives the intervals.
- Controls that must go red first: the reference against itself gives exactly 0; a deliberately broken candidate must lose with an interval that excludes 0 (it did: +5.4 per unit, [3.8, 7.1]); a parity test checks that the bench takes the same decision as the real pipeline on 53 lines.
- Label audit: two independent annotators on 400 han-only lines, plus 20 invented gold lines. Gold: 0 misses in 8 passes. The annotators disagree with the declared channel language on 11.0 percent of Japanese lines and 4.5 percent of Chinese lines, so the declared labels are noisy and the report says so. Two annotators from one model family are not independent evidence.
- A real-browser proof with a faked service: the published build skips a traditional Chinese line answered `en`; the candidate translates it; an English line answered `en` is skipped by both.

## Results (counts only)

First change (engine verdict guard, mention and mark fixes), design set:

- lines deleted for English readers: 329 to 0;
- no other cell rose by more than 1 line; wrong hints 6 to 3 on Chinese;
- cost of the English reader -16.35 per unit [-22.98, -10.15]; Japanese reader -0.218 [-0.510, -0.005];
- speed x0.96 median, x1.02 p95; size +234 bytes gzip.

Second change (marker tables, bopomofo), design set, without engine verdicts: Japanese lines read as Chinese 3.2 percent to 1.1 percent of han-only Japanese lines; silence on han-only Chinese 58.3 to 56.6 percent; but lines removed by a Chinese-only allowlist rose from 773 to 798, which is the documented price (the allowlist case is reported, not a criterion).

## What went wrong, and what is not proven

- The engine verdict collection was cut by a rate limit after 1,133 of 3,608 design lines and the held-out set was never scored. The verdict gate is therefore measured on those 1,133 lines only, and the second change is not judged on held-out data. It stays a draft.
- Not proven: Kick chat (the sets are Twitch plus PC chat), Cantonese (no data), Korean (rare).
- A review cannot be answered from the store (reviews have no developer reply), so the answer to the reviewer is the changelog entry when the change ships.

## Pointers

- Kick Chat Translator, pull request 91 (merged), `docs/han-detection.md`.
- Twitch Chat Translator, pull request 26, same document.
