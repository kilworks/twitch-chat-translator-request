// Usage (from the repo root so tsx finds tsconfig.json and the ~/ alias):
//   REPO=<worktree> node --import tsx <annex>/witness/han-witness.mts
// Prints one tab-separated row per witness line. Compare with annex D.1 of the prompt.
import { pathToFileURL } from 'node:url';
const REPO = process.env.REPO ?? '<worktree>';
const load = (p: string) => import(pathToFileURL(`${REPO}/${p}`).href);
const { detectLanguage, confidentLanguage } = await load('src/content/langDetect.ts');
const { isSameLanguageAsTarget, hasNonEnglishLetter, shouldDropBySourceLang } = await load('src/content/filters.ts');

// [label, text]. label = my linguistic judgement of the line; 'amb' = cannot be told from the line alone.
const CASES: Array<[string, string]> = [
  // A. zh-TW / zh with decorative kana-range characters (false ja)
  ['zh-tw', '你好嗎ヽ(´ー`)ノ'],
  ['zh-tw', '好好笑(ノ°▽°)ノ'],
  ['zh-tw', '主播今天好帥ー'],
  ['zh-tw', '史蒂夫・賈伯斯'],
  ['zh-tw', '我の朋友好棒'],
  ['zh', '这是什么情况ー'],
  ['zh', '约翰・史密斯'],
  ['zh', '主播太强了ノ'],
  ['zh', '哈哈哈ヽ(´▽`)/'],
  // B. real Japanese with one or two kana
  ['ja', '神の一手'],
  ['ja', '最高の神回'],
  ['ja', '草生える'],
  ['ja', 'うーん'],
  ['ja', 'ナイス'],
  ['ja', 'お疲れ様です'],
  ['ja', 'コーヒー飲みたい'],
  // C. kana-less Japanese carrying a Japan-only written form (decisive for ja in principle)
  ['ja', '歴史的瞬間'],
  ['ja', '圧勝'],
  ['ja', '逆転'],
  ['ja', '実質無敵'],
  ['ja', '観戦'],
  ['ja', '戦術'],
  ['ja', '総合優勝'],
  ['ja', '対戦'],
  ['ja', '楽勝'],
  ['ja', '変更'],
  ['ja', '続行'],
  ['ja', '売上'],
  // D. kana-less Japanese with shared forms that are in the zh tables (leaks)
  ['ja', '声優最高'],
  ['ja', '東京湾'],
  ['ja', '台湾'],
  ['ja', '湾岸'],
  ['ja', '開幕'],
  ['ja', '公開'],
  ['ja', '開始'],
  ['ja', '萬斎'],
  ['ja', '独裁開始'],
  // E. kana-less Japanese without any marker, ambiguous with Chinese
  ['amb', '草'],
  ['amb', '初見'],
  ['amb', '神回'],
  ['amb', '最強'],
  ['amb', '大草原'],
  ['amb', '最高'],
  ['amb', '感謝'],
  ['amb', '大丈夫'],
  ['amb', '日本語'],
  // F. Chinese without markers
  ['zh', '太强了'],
  ['zh-tw', '太強了'],
  ['zh-tw', '好厲害'],
  ['zh', '好厉害'],
  ['zh', '笑死我了'],
  ['zh', '真的假的'],
  ['zh-tw', '主播好帥'],
  ['zh-tw', '謝謝主播'],
  // G. Chinese with markers (should be decided)
  ['zh-tw', '這個遊戲真的很好玩'],
  ['zh-tw', '今天幾點開台'],
  ['zh', '这个主播真的好'],
  ['zh-tw', '主播好帥嗎'],
  // H. bopomofo chat (Taiwan)
  ['zh-tw', '好ㄉ'],
  ['zh-tw', 'ㄏㄏㄏ'],
  ['zh-tw', '晚安ㄌ大家'],
  ['zh-tw', '對ㄚ'],
  ['zh-tw', '真ㄉ假ㄉ'],
  // I. Cantonese
  ['yue', '你食咗飯未'],
  ['yue', '好正啊'],
  ['yue', '主播真係好叻'],
  // J. Korean with hanja and Han mixes
  ['ko', '한국 韓國'],
  ['ko', '韓國人 한'],
  ['ko', '안녕하세요'],
  // K. Han plus Latin
  ['zh', 'gg 说得对'],
  ['zh', 'I love 你好吗 lol'],
  ['zh-tw', 'GG 太強了'],
  ['ja', 'ww 草'],
  ['ja', '神ゲーww'],
  // L. one-character and digit lines
  ['amb', '好'],
  ['amb', '笑'],
  ['n/a', '666'],
  ['n/a', '233'],
  ['n/a', '888'],
  ['n/a', '5555'],
  // M. added 25/11 after review: invented kana pseudonyms (M3a), one hard kana plus the prolonged mark, floor cases
  ['zh-tw', '@ゆきだるま 這可以嗎0.0'],
  ['zh-tw', '@さくら_12 你好'],
  ['ja', 'あー'],
  ['ja', 'えー'],
  ['ja', 'ラー'],
  ['ja', '先輩ー？'],
  ['ja', '最強の犬ww'],
  ['amb', 'ー'],
  ['ja', 'は'],
];

const READERS = ['en', 'ja', 'zh', 'zh-tw', 'ko'];
console.log(['label', 'text', 'detect', 'confident', 'skipSameLang(readers: ' + READERS.join(',') + ')', 'allowlist[ja]', 'allowlist[zh]', 'allowlist[zh-tw]'].join('\t'));
for (const [label, text] of CASES) {
  const d = detectLanguage(text);
  const c = confidentLanguage(text);
  const skips = READERS.filter((r) => isSameLanguageAsTarget(c, r)).join('|') || '-';
  const al = (l: string) => shouldDropBySourceLang(d, { sourceLangAllowlist: [l] } as never) ?? 'keep';
  console.log([label, text, String(d), String(c), skips, al('ja'), al('zh'), al('zh-tw')].join('\t'));
}
console.log('hasNonEnglishLetter(太強了)=', hasNonEnglishLetter('太強了'));
