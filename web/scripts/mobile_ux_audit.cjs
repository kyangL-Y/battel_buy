const { chromium, devices } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const pages = [
    ['mobile-home', 'http://127.0.0.1:4273/'],
    ['mobile-buyer', 'http://127.0.0.1:4273/?role=buyer'],
    ['mobile-trend', 'http://127.0.0.1:4273/?role=buyer&tab=trend'],
    ['mobile-alerts', 'http://127.0.0.1:4273/?role=buyer&tab=alerts'],
    ['mobile-supplier', 'http://127.0.0.1:4273/?role=supplier'],
  ];

  for (const [name, url] of pages) {
    const ctx = await browser.newContext({ ...devices['iPhone 13'], locale: 'zh-CN' });
    const page = await ctx.newPage();
    const errors = [];
    page.on('console', (m) => {
      if (['error', 'warning'].includes(m.type())) errors.push(`${m.type()}: ${m.text()}`);
    });
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await page.screenshot({ path: `/mnt/e/battel/web/test-results/${name}.png`, fullPage: true });
    const info = await page.evaluate(() => ({
      title: document.title,
      url: location.href,
      bodyText: document.body.innerText.slice(0, 1200),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      overflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      buttons: [...document.querySelectorAll('button')].slice(0, 30).map((b) => b.innerText.trim()).filter(Boolean),
      inputs: [...document.querySelectorAll('input, textarea, select')].length,
    }));
    console.log(`\n## ${name}`);
    console.log(JSON.stringify({ ...info, errors }, null, 2));
    await ctx.close();
  }
  await browser.close();
})();
