# In Memory of Semyon Skrepetsky (@SemyonSkrepetsky)

![Semyon Skrepetsky](channels4_banner.jpg)

Robert Kuzovkov, known as **Semyon Skrepetsky** (Семён Скрепецкий),
1981–2026, was a Russian dissident artist, actionist and caricaturist.
Born in Altai, he emigrated to Poland in 2021 fleeing persecution. Through
painting and performance he ridiculed Putin, Kadyrov, Lukashenko and Russian
propaganda. On 12 June 2026 he staged his final action outside the Russian
Embassy in Berlin. On 15 June 2026 he was shot dead in the Polish town of
Biała Podlaska.

This project preserves the content of his gallery — paintings, performances,
videos and posts — and presents it as a **bilingual memorial website
(Russian / English)**.

**Links:** YouTube channel — <https://www.youtube.com/@СемёнСкрепецкий>

*(Versión en español: [README.es.md](README.es.md))*

## What's in this folder

```
memorial-skrepetsky/
├── data/
│   ├── catalog.json          ← The "database": all posts, media and translations
│   ├── _to_translate.json    ← Queue of unique texts to translate (stable indexes)
│   └── tr/                    ← English translations in batches (000.json, 001.json, …)
├── media/
│   ├── photos/YEAR/MONTH/     ← Downloaded photos and paintings
│   ├── videos/YEAR/MONTH/     ← Downloaded videos
│   └── thumbs/YEAR/MONTH/     ← Video thumbnails
├── index.html                ← The BILINGUAL memorial site (ROOT, ready to publish)
├── catalog-data.js           ← Copy of the catalog the site reads (English included)
├── scripts/
│   ├── archive_skrepetsky.py ← Downloads all the channel content
│   └── merge_translations.py ← Merges data/tr/ translations into the catalog and the site
├── descargar_todo.bat        ← Double-click on Windows to download everything
├── ver_web.bat               ← Double-click on Windows to open the site
├── README.md                 ← This file (English)
└── README.es.md              ← Spanish version
```

> **Ready to publish on a server.** `index.html` is at the **root** and all paths
> are relative (`catalog-data.js`, `data/`, `media/`). Upload the **whole folder**
> to any static host (Netlify, GitHub Pages, Cloudflare Pages, a VPS with
> Nginx/Apache, etc.) and the site works as soon as you open the domain. No
> backend or database required.

### Publishing on GitHub Pages
1. Create a repository and push the whole folder to it.
2. In the repo: **Settings → Pages → Build and deployment → Source: Deploy from a
   branch**, pick your branch and the `/ (root)` folder, then **Save**.
3. The site goes live at `https://<user>.github.io/<repo>/`.

> Note: the `media/` folder is ~1.4 GB. GitHub has a soft repo limit of ~1 GB and
> a 100 MB per-file limit. If the media is too large for GitHub, host the site on
> Netlify/Cloudflare Pages or a VPS instead, or keep `media/` out of the repo and
> serve it from external storage.

## The bilingual site (RU / EN)

**Double-click `ver_web.bat`.** It opens the gallery in your browser through a
small local server (http://localhost:8000/index.html). Keep the black window
open while you browse.

Features:
- **RU / EN language switcher** in the top-right corner. Your choice is saved in
  `localStorage`: next time you open the site, it remembers your language.
- In **EN**, each post shows its translated text; where a translation isn't
  available yet, the Russian original is shown with a discreet note.
- The whole interface (header, biography, search, filters, buttons) is in both
  languages.
- Search and filters (Photos / Videos / Paintings / Text only). Loads in batches
  so it doesn't pull 1.4 GB at once. Click an image to view it full-size.

## English translation status

The catalog contains **1,970 posts** (1,700 with text, 1,584 unique texts).
Translations are done faithfully, one by one, and stored in batches in
`data/tr/`. A first block is translated covering the artist's whole arc
(2018–2025); the remaining posts are shown in Russian until translated.

### How to continue/add translations
1. Open `data/_to_translate.json`: a list of unique Russian texts; each item's
   position (0, 1, 2, …) is its **index**.
2. Create a file in `data/tr/` (e.g. `007.json`): `{ "350": "English…" }`, where
   the key is the text's index.
3. Run `python scripts/merge_translations.py` to merge the translations into the
   catalog and regenerate `catalog-data.js`.

The process is cumulative: add batches whenever you like.

## Re-downloading / updating the content

- **Windows:** double-click `descargar_todo.bat` (requires Python).
- **Terminal:** `python scripts/archive_skrepetsky.py` (`--no-media`, `--limit 5`).
  It is resumable.

## Note

All content comes from the artist's **public** gallery. This archive was created
for memorial purposes, to preserve his work and his meanings ("создатель
смыслов" — "creator of meanings").
