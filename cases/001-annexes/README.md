# Case 001, annexes

Reproducible material behind the [research thesis](../001-research-thesis.md). Everything here is either invented, aggregated or derived from public data. No chat line, nickname or channel name is included. Scripts that read private chat are published with the path replaced, so they show the method but cannot run without that data.

Pinned code the outputs refer to: Kick Chat Translator `7d8671a`, Twitch Chat Translator `14b3046`. The service answers and browser versions are from 2026-11-25 and may have changed: replay before relying on them.

## witness/

- `han-witness.mts`: runs 89 invented lines through the published detector (`detectLanguage` guess and `confidentLanguage` sure answer) and prints a table. Run from the root of a checkout: `REPO=<worktree> node --import tsx han-witness.mts`.
- `expected.out`: the output on the pinned Kick commit. The first control of the plan is that the unchanged code reproduces it byte for byte. Replayed from this repository's copy of the script on a clean export of `7d8671a`: exit 0, 91 lines, `cmp` identical to `expected.out`. The Python scripts were not replayed from this repository (they need the Unihan files or private chat).

## google-probe/

Probes of the translation endpoint the extension uses, with `sl=auto` and with a forced `sl`.

- `probe.py`: 118 invented short phrases (Simplified, Traditional, Japanese in kanji only), single and batch endpoints, three target languages. `summary.txt` is its aggregate (language detected, and how many translations equal the reference).
- `probe2.py`: 780 short sentences from a public sentence corpus (Tatoeba, CC BY 2.0 FR, not redistributed here), `tl=en`. `summary2.txt` is its aggregate. It writes its outputs next to itself and has no request counter: treat it as a model, not as the collection tool.
- `tl_client_independence.py`, `batch_endpoint_tl_en.py`, `forced_sl_test.py` and their `.out`: the detected language does not depend on the target language or on the client string; the batch endpoint gives the same answers as the single one; a forced source gives identical translations on 40 unmarked Traditional lines (`tl=en`, one run).

## browser-api/

- `apis-check.mjs`, `apis-check.out`: `typeof LanguageDetector` and `availability()` in real Brave, Chrome 158 and Edge 158, with `--headless=new` and throwaway profiles. Set `PLAYWRIGHT_KIT` to a folder that contains Playwright. Brave: undefined. Chrome and Edge: function present, `availability()` is `unavailable`.

## han-tables/

Character lists derived from the Unihan database (Unicode 18.0.0), with the scripts that generate them.

- `sets/JA_STRICT.txt`: 256 characters used in Japanese (jōyō and jinmeiyō) and in no Chinese or Korean standard. `JA_STRICT_vs_ANY_CHINESE.txt`: the same measured against any Chinese source.
- `sets/TRAD_core_joyoexcl_leakpruned.txt`: Traditional-only characters minus jōyō minus the 53 that leak into Japanese chat (3,336). `TRAD_leak_chars.txt`: those 53.
- `sets/compact_TRAD_rank.txt`, `compact_SIMP_rank.txt`: frequency-ordered compact lists, one line of characters with no separator. The order of ties is not reproducible byte for byte, so these files are the reference. `compact_JA_top250.txt`: the 145 Japan-only characters ranked on chat. Despite its name, a `*_top250` file is not a 250-character list (the Traditional one holds 164, the Simplified one, not published here, holds 16).
- `sets/ZF_function_chars.txt`: a statistically selected function-word set that overfitted (11.3 percent leak into held-out Japanese lines). Kept as a negative result: the plan uses 18 hand-picked characters instead.
- `scripts/gen_sets.py`, `ucd_facts.py`, `unihan_lib.py`: generation recipes and Unicode facts (they need the Unihan files). `decide.py`: reference decision procedure for a Han line (about 30 lines of logic). `budget.py`: weight of each proposal against the 2 percent gate. `trad_leak.py`: leak pruning, learned on even Japanese lines and scored on odd ones (reads private chat, path removed).

## Licence notice for the derived lists

The lists are derived from Unihan data. Unicode License v3 (https://www.unicode.org/license.txt) permits using, copying, modifying and distributing the data without restriction, provided its copyright and permission notice appear with all copies of the data files or in associated documentation. The full notice, fetched from the official file on 2026-11-25, is in `NOTICE-UNICODE.txt` and must travel with any copy of these lists. CC-CEDICT and CC-Canto (CC BY-SA) data were used for study only and are not derived into anything published here.
