// The daily Instagram post, made by the Studio (buffbets.github.io/studio.html) without a browser window:
// yesterday's slides as PNGs plus the caption.
//
//   node social/daily_post.js STUDIO_DIR RESULTS_JSON OUT_DIR [YYYY-MM-DD]
//
// STUDIO_DIR: a checkout of buffbets/buffbets.github.io. RESULTS_JSON: results.json from ev-bot-results.
// The day defaults to yesterday in New York. Needs Playwright (Chromium).
//
// studio_cover.json: the winning-night cover (the full night's units first, the biggest hit under it), applied to
// the Studio page in memory until the site has it. Each [old, new] pair is skipped once the page no longer has old.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const [studio, results, out, dayArg] = process.argv.slice(2);
if (!studio || !results || !out) {
  console.error('usage: node daily_post.js STUDIO_DIR RESULTS_JSON OUT_DIR [YYYY-MM-DD]');
  process.exit(2);
}
const day = dayArg || new Date(Date.now() - 864e5).toLocaleDateString('en-CA', { timeZone: 'America/New_York' });

let page = fs.readFileSync(path.join(studio, 'studio.html'), 'utf8');
for (const [oldText, newText] of JSON.parse(fs.readFileSync(path.join(__dirname, 'studio_cover.json'), 'utf8'))) {
  if (page.includes(oldText)) page = page.replace(oldText, newText);
}

(async () => {
  const browser = await chromium.launch();
  const tab = await browser.newPage();
  const errors = [];
  tab.on('pageerror', e => errors.push(e.message));
  await tab.route('https://joeybuffo10-wq.github.io/ev-bot-results/results.json*',
    r => r.fulfill({ path: results, contentType: 'application/json' }));
  await tab.route('http://studio.local/**', r => {
    const name = new URL(r.request().url()).pathname;
    return name === '/studio.html' ? r.fulfill({ body: page, contentType: 'text/html' })
      : r.fulfill({ path: path.join(studio, name) });
  });
  await tab.goto('http://studio.local/studio.html', { waitUntil: 'networkidle' });
  await tab.waitForFunction(() => window.buffbets && window.buffbets.dayPost, null, { timeout: 30000 });
  const bets = JSON.parse(fs.readFileSync(results, 'utf8')).bets.filter(b => b.date === day).length;
  if (!bets) { await browser.close(); console.log(`${day}: no graded bets, no post`); process.exit(3); }
  const post = await tab.evaluate(d => window.buffbets.dayPost(d), day);
  await browser.close();
  if (errors.length) throw new Error(errors.join('\n'));
  fs.mkdirSync(out, { recursive: true });
  post.slides.forEach((s, i) =>
    fs.writeFileSync(path.join(out, `buffbets-${day}-${i + 1}.png`), Buffer.from(s.split(',')[1], 'base64')));
  fs.writeFileSync(path.join(out, 'caption.txt'), post.caption);
  console.log(`${day}: ${post.slides.length} slides\n${post.caption}`);
})().catch(e => { console.error(e); process.exit(1); });
