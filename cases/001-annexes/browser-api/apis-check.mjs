// Real browsers, throwaway profiles, neutral https page: is the built-in LanguageDetector API exposed?
// node apis-check.mjs   (read-only: no extension, no cookies, no input read)
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const KIT = process.env.PLAYWRIGHT_KIT;
const { chromium } = await import(pathToFileURL(path.join(KIT, 'node_modules/playwright/index.mjs')).href);

const TARGETS = [
  ['brave', 'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'],
  ['chrome', 'C:/Program Files/Google/Chrome/Application/chrome.exe'],
  ['edge', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'],
];
const SAMPLES = ['草', '太強了', '好厲害', '這個遊戲真的很好玩', '主播好帥', '最高の神回', '圧勝', '歴史的瞬間', '你好嗎', 'ありがとう', '我の朋友好棒'];

for (const [name, exe] of TARGETS) {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), `apis-${name}-`));
  let ctx;
  try {
    ctx = await chromium.launchPersistentContext(profile, { executablePath: exe, headless: true, args: ['--headless=new', '--no-first-run', '--no-default-browser-check'] });
    const page = await ctx.newPage();
    await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
    const out = await page.evaluate(async (samples) => {
      const r = { ua: navigator.userAgent, secure: window.isSecureContext, type: typeof LanguageDetector, translator: typeof Translator };
      if (typeof LanguageDetector !== 'undefined') {
        try {
          r.availability = await LanguageDetector.availability();
          if (r.availability === 'available') {
            const d = await LanguageDetector.create();
            r.results = {};
            for (const s of samples) {
              const t0 = performance.now();
              const res = await d.detect(s);
              r.results[s] = { top: res.slice(0, 3).map((x) => `${x.detectedLanguage}:${x.confidence.toFixed(2)}`), ms: +(performance.now() - t0).toFixed(2) };
            }
          }
        } catch (e) {
          r.error = String(e && e.message || e);
        }
      }
      return r;
    }, SAMPLES);
    console.log(name, JSON.stringify(out, null, 1));
  } catch (e) {
    console.log(name, 'LAUNCH/EVAL ERROR', String(e && e.message || e).slice(0, 300));
  } finally {
    try { await ctx?.close(); } catch {}
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
  }
}
