# Case 002: Taiwan and mainland China told apart (work in progress)

Started 2026-11-26, follows [case 001](001-han-script-detection.md). Status: measuring. Nothing here is shipped.

## Why

Case 001 left the detector with one answer for Chinese written with characters both scripts share, and that answer is `zh`, which the extension names Simplified Chinese. Run against lines whose origin is known, the second change of case 001 reads Taiwanese lines as mainland Chinese. The owner wants Taiwan and the mainland kept apart, so the test sets have to carry the origin.

## Sets with a known origin

Only counts are kept in this repository. The raw text stays on the research machine, because several of these corpora do not allow redistribution.

| Set | Origin | Lines kept | Register |
|---|---|---|---|
| Common Voice sentence lists, `zh-TW` | Taiwan | 6,000 | written sentences, some chat logs |
| Common Voice, `zh-CN` | mainland | 6,000 | written sentences |
| Common Voice, `zh-HK`, `yue` | Hong Kong | 6,000 each | written sentences, vernacular Cantonese |
| Common Voice, `ja` | Japan | 6,000 | written sentences |
| OpenSubtitles, Traditional file | Taiwan | 6,000 | spoken lines, short |
| OpenSubtitles, Simplified file (first 40 MB) | mainland | 6,000 | spoken lines, short |
| OpenSubtitles, Japanese | Japan | 6,000 | spoken lines, short |
| Bilibili comments, two sets | mainland | 8,000 each | live comments, close to chat |
| Taiwanese forum posts, cut into sentences | Taiwan | 4,000 | forum |
| Hong Kong forum posts, cut into sentences | Hong Kong | 4,000 | forum |
| Niconico comments, four archives | Japan | 12,000 | live comments |
| Wikipedia, same articles converted to three variants | Taiwan, mainland, Hong Kong | in progress | encyclopedia, markers only |

Reference tables, not test lines: OpenCC dictionaries (Taiwan phrases, Hong Kong variants, character tables), Unihan, CLDR likely subtags.

Known limits: the subtitle files are labelled by file name only (5.1 percent of the Simplified file's Han-only lines still read as Traditional, so some of it is mislabelled); Common Voice sentences are read aloud, not typed; the Simplified subtitles are a prefix of the file; none of this is Twitch or Kick chat.

## First reading: what the detector says on lines of known origin

Share of Han-only lines by answer of `confidentLanguage`. First figure: current `master`. Second: with the second change of case 001 (open pull requests). `none` means no answer.

| Set (origin) | zh-tw | zh (Simplified) | yue | none |
|---|---|---|---|---|
| Subtitles (Taiwan) | 54.3 to 50.3 | 1.4 to **22.7** | 0 to 0 | 44.4 to 27.0 |
| Common Voice (Taiwan) | 44.5 to 39.2 | 0 to **8.3** | 0 to 0 | 55.5 to 52.5 |
| Forum (Taiwan) | 66.3 to 67.1 | 0.2 to **11.7** | 0 to 0 | 33.5 to 21.2 |
| Common Voice (Hong Kong) | 16.9 to 15.3 | 0 to 4.7 | 40.6 to 40.5 | 42.5 to 39.5 |
| Common Voice (mainland) | 0 to 0 | 30.3 to 47.6 | 0 to 0 | 69.7 to 52.4 |
| Subtitles (mainland) | 5.1 to 5.0 | 41.5 to 64.0 | 0.1 to 0.1 | 53.4 to 31.0 |
| Bilibili (mainland) | 0.1 to 0.1 | 38.0 to 56.1 | 0.1 to 0.1 | 61.7 to 43.6 |

Reading: the second change helps the mainland (silence 70 to 52 percent on one set) and hurts Taiwan, where up to 22.7 percent of lines now read as mainland Chinese. The lines that cause it use characters shared by both scripts. That step is now reverted (next section).

## What was done with it (2026-11-26)

The function-character step of case 001's second change is reverted in both open pull requests. Without it, Taiwanese lines read as Simplified Chinese stay at 1.5 percent (subtitles), 0.2 (forum) and 0 (Common Voice), the same as before the change. The price is that the mainland gain went with it: silence on mainland Common Voice lines is 69.7 percent on master, 52.4 with the step, 70.8 without.

## Vocabulary markers from the OpenCC tables: too rare to help

The OpenCC Taiwan phrase tables give 796 mainland terms and 753 Taiwan terms. Share of Han-only lines that contain a term of one side only:

| Set (origin) | mainland term | Taiwan term |
|---|---|---|
| Common Voice (Taiwan) | 1.0 | 3.7 |
| Subtitles (Taiwan) | 0.7 | 0.7 |
| Forum (Taiwan) | 1.0 | 2.6 |
| Common Voice (mainland) | 3.7 | 3.6 |
| Subtitles (mainland) | 0.8 | 0.5 |
| Bilibili (mainland) | 2.2 to 1.2 | 0.3 to 0.2 |

At most a few percent of lines carry a marker and the two sides are not clean (Common Voice mainland has as many Taiwan terms as mainland terms). Vocabulary is not a lever for chat-length lines. The script itself (Traditional against Simplified characters) stays the main signal.

## Wikipedia variants: what the smaller table costs

The same 400 articles converted by MediaWiki to the Taiwan, Hong Kong and mainland variants (808 to 810 Han-only lines each). Share read as Traditional (`zh-tw`) on master and on the open change without the reverted step: Taiwan 71.2 to 59.2, Hong Kong 71.0 to 59.1. Mainland lines with no answer: 54.6 to 56.0. The smaller Traditional table loses recall on Traditional text (Common Voice Taiwan 44.5 to 39.2, subtitles 54.3 to 50.3 as well) and gains nothing on the mainland side. What it buys is fewer Japanese lines read as Chinese. A narrower fix is open: keep the old table and remove only the characters that Japanese also writes.

## Narrow candidate: five shared characters removed (failed its own rule)

The rule was written before scoring (see the detection notes in the extension repository). The candidate removed `開` and `萬` from the Traditional list, `声` and `湾` from the Simplified list and `嬲` from the Cantonese list, and added nothing.

- Japanese leak, passed: among 987 Han-only Japanese lines that contain one of the five characters (taken from 8.3 million Niconico comments, subtitles and Wikipedia), the share read as Chinese fell from 94.1 to 1.5 percent.
- Chinese recall, failed: the share of the expected answer fell by more than the 0.3 points allowed on most sets: Taiwan 1.1 to 2.8 points, Hong Kong 0.9 to 2.7, mainland 0.4 to 1.4 (Cantonese unchanged).
- Why it cannot be split: a line whose only marker is one of these characters is ambiguous between Japanese and Chinese, so removing the marker moves those lines from a right answer to silence in Chinese chat and from a wrong answer to silence in Japanese chat. Lines decided by the character alone: Taiwan 157 (`開`) and 47 (`萬`) of 13,994; mainland 82 (`声`) and 60 (`湾`) of 27,555.
- How often it matters on the Japanese side: 828 of 362,323 Han-only Niconico comments (0.23 percent of them, 0.01 percent of all comments) against 1.1 percent of Han-only Taiwanese lines for `開` alone.

Decision: not merged, not opened as a pull request. The tables stay as they are on `master`.

## Marker lists chosen from the data (pull request open)

About 340,000 distinct Han-only lines of known origin (Taiwan, mainland, Hong Kong, Cantonese, Japan), cut by a hash of the line into train, dev and test. The 45-character Traditional and Simplified lists become 506 and 592 characters, picked one at a time by newly covered Chinese lines per Japanese line flagged, under a Japanese budget picked on dev. The rule was written before the test split was read, amended once for the Cantonese price, and read once.

| Test split | master | candidate |
|---|---|---|
| Taiwanese lines named Traditional | 59.3 % | 77.8 % |
| Mainland lines named Simplified | 37.8 % | 82.4 % |
| Han-only Japanese lines read as Chinese | 1.13 % | 0.73 % |
| Cantonese lines read `yue` | 52.0 % | 52.0 % |
| Cantonese lines read Traditional (price) | 25.1 % | 36.6 % |

Weight +3,275 bytes gzip, speed 0.95 times. On real Twitch chat declared Chinese (33,852 lines, not used to choose anything): no answer 62.9 to 46.3 percent. Not tried: a Cantonese marker list chosen the same way (56 to 60 percent `yue` on dev but 0.5 to 2.4 percent of Taiwanese lines named Cantonese), a character n-gram classifier, Kick chat.

## Next

- Wikipedia articles converted to the three variants, to see which characters differ between them (running).
- A script-neutral answer is no longer the first need: with the step reverted, the detector does not name a script it cannot see. What is open is the held-out reading of what remains (tables and bopomofo), whose cost interval for English and Japanese readers includes 0.
- A held-out reading on a set never used to choose anything, with the rule written before scoring.
