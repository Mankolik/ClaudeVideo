// Deterministic frame renderer: steps window.draw(t) through the timeline and saves each canvas frame.
// usage: node render.js <outDir> [fps=30] [workers=4]     (all frames)
//        node render.js <outDir> still t1 t2 t3 ...          (PNG stills at given seconds)
const path = require('path'), fs = require('fs'), http = require('http');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const root = __dirname, mime = { '.html': 'text/html', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const f = path.join(root, decodeURIComponent(req.url.split('?')[0]).replace(/^\/$/, '/index.html'));
  fs.readFile(f, (e, d) => e ? (res.writeHead(404), res.end()) : (res.writeHead(200, { 'content-type': mime[path.extname(f)] || 'application/octet-stream' }), res.end(d)));
});

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(`http://localhost:${port}/index.html?render`);
  await page.evaluate(() => window.ready);
  return page;
}

(async () => {
  const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });

  if (process.argv[3] === 'still') {
    const page = await openPage(browser, port);
    for (const t of process.argv.slice(4).map(Number)) {
      const data = await page.evaluate(t => { window.draw(t); return document.getElementById('c').toDataURL('image/png'); }, t);
      fs.writeFileSync(path.join(out, `still_${String(t).replace('.', '_')}.png`), Buffer.from(data.split(',')[1], 'base64'));
    }
  } else {
    const fps = +process.argv[3] || 30, workers = +process.argv[4] || 4;
    const total = Math.round(30 * fps); let next = 0;
    const t0 = Date.now();
    await Promise.all(Array.from({ length: workers }, async () => {
      const page = await openPage(browser, port);
      for (;;) {
        const n = next++; if (n >= total) break;
        const data = await page.evaluate(t => { window.draw(t); return document.getElementById('c').toDataURL('image/jpeg', 0.95); }, n / fps);
        fs.writeFileSync(path.join(out, `f_${String(n).padStart(4, '0')}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
        if (n % 60 === 0) console.log(`frame ${n}/${total}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
      }
    }));
  }
  await browser.close(); server.close();
})();
