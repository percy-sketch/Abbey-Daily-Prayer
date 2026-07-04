# The Abbey Daily

A daily devotional companion from The Abbey at Pawleys Island:

- **Verse** — one of 365 memorable Scripture passages (KJV), walking canonically from Genesis (Jan 1) to Revelation (Dec 31)
- **Catechism** — one question and answer each day from *To Be a Christian: An Anglican Catechism*, cycling through all 368 questions
- **Prayer** — your personal prayer list with daily checkmarks that reset each morning

Works exactly like the Prayer Rotation app: a free static site on GitHub Pages, installed to your phone's home screen.

---

## 1. Set up the site (one time)

1. Go to your GitHub repository (or create a new one, e.g. `abbey-daily`).
2. Upload everything in this folder to the repository root:
   - `index.html`
   - `manifest.json`
   - `sw.js`
   - `icon-192.png`
   - `icon-512.png`
3. In the repo: **Settings → Pages → Source: Deploy from a branch → main / (root) → Save**.
4. After a minute, your app is live at `https://YOUR-USERNAME.github.io/abbey-daily/`

## 2. Generate the catechism file (one time, on any computer)

The catechism text is copyrighted (© 2020 ACNA / Crossway), so it isn't bundled in these files. Instead you generate it from your own PDF:

```
pip install pypdf
python3 extract_catechism.py To-Be-a-Christian.pdf
```

This creates **`catechism.json`** (all 368 Q&As). Upload it to the repository root, right next to `index.html` — the same way `roster.csv` works in the Prayer Rotation app. The app fetches it automatically and stores a copy on your phone.

Until `catechism.json` is uploaded, the Catechism tab shows friendly setup instructions instead of an error.

## 3. Install on your phone

**iPhone:** open the site in Safari → tap the Share button → **Add to Home Screen**.

**Android:** open the site in Chrome → tap the ⋮ menu → **Add to Home screen** (or "Install app").

It opens full-screen like a native app, works offline after the first visit, and your prayer list stays on your device.

## Notes

- Prayer checkmarks reset automatically at midnight each day; your list of people is kept.
- The prayer list is stored only on each phone (localStorage) — it never leaves the device.
- To update the app later, just replace `index.html` in the repo; phones pick up the new version on next open.
