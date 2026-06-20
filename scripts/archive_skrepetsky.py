#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivador del canal de Telegram "Картинная галерея Семёна Скрепецкого"
(@SemyonSkrepetsky) -> https://t.me/s/SemyonSkrepetsky

Qué hace este script:
  1) Rastrea TODO el historial público del canal, desde el post más reciente
     hasta el PRIMERO de todos. El "scroll hacia el pasado" que ves en el
     navegador es, por debajo, pedir la página con ?before=<id>; este script
     automatiza ese mismo mecanismo en bucle hasta llegar al principio.
  2) Parsea cada post: texto, fotos, vídeos, documentos, fecha, vistas,
     reacciones, enlaces y hashtags.
  3) Descarga los archivos (imágenes y vídeos) a un árbol de carpetas
     organizado por año/mes.
  4) Genera data/catalog.json -> la "base de datos" para la web.

NO necesita instalar nada: usa solo la librería estándar de Python 3.
Ejecútalo desde la carpeta del proyecto:

    python scripts/archive_skrepetsky.py

Opciones útiles:
    --no-media        Solo construye el catálogo JSON (no descarga archivos)
    --limit N         Rastrea como máximo N páginas (para pruebas)
    --channel NAME    Otro canal (por defecto SemyonSkrepetsky)

Es REANUDABLE: si lo paras y lo vuelves a lanzar, salta lo ya descargado.
"""

import os
import re
import sys
import json
import time
import html
import urllib.request
import urllib.error
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CHANNEL = "SemyonSkrepetsky"
BASE = "https://t.me/s/{channel}"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "ru,en;q=0.8",
}

# Rutas (relativas a la raíz del proyecto = carpeta padre de /scripts)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
PHOTOS_DIR = os.path.join(ROOT, "media", "photos")
VIDEOS_DIR = os.path.join(ROOT, "media", "videos")
THUMBS_DIR = os.path.join(ROOT, "media", "thumbs")
CATALOG = os.path.join(DATA_DIR, "catalog.json")

REQUEST_DELAY = 0.8          # segundos entre peticiones de páginas (ser amable)
RETRIES = 3

for d in (DATA_DIR, PHOTOS_DIR, VIDEOS_DIR, THUMBS_DIR):
    os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------------------
# Utilidades de red
# ---------------------------------------------------------------------------
def fetch(url, binary=False):
    """Descarga una URL con reintentos. Devuelve bytes o str (utf-8)."""
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            print(f"   reintento {attempt}/{RETRIES} ({e})", file=sys.stderr)
            time.sleep(2 * attempt)
    print(f"   ! fallo definitivo: {url}\n     {last}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Parseo del HTML del widget público de Telegram
# ---------------------------------------------------------------------------
# Cada mensaje vive en un <div class="tgme_widget_message ..." data-post="canal/ID">
MSG_RE = re.compile(
    r'<div class="tgme_widget_message[^"]*"[^>]*data-post="([^"]+)"(.*?)'
    r'(?=<div class="tgme_widget_message[^"]*"[^>]*data-post=|<div class="tme_messages_more|</section)',
    re.S,
)
PHOTO_RE = re.compile(r"tgme_widget_message_photo_wrap[^>]*background-image:url\('([^']+)'\)")
VIDEO_SRC_RE = re.compile(r'<video[^>]+src="([^"]+)"')
VIDEO_THUMB_RE = re.compile(r"tgme_widget_message_video_thumb[^>]*background-image:url\('([^']+)'\)")
ROUNDVIDEO_RE = re.compile(r'tgme_widget_message_roundvideo[^>]+src="([^"]+)"')
TEXT_RE = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
TIME_RE = re.compile(r'<time[^>]+datetime="([^"]+)"')
VIEWS_RE = re.compile(r'tgme_widget_message_views">([^<]+)<')
LINK_RE = re.compile(r'href="(https?://[^"]+)"')
DOC_TITLE_RE = re.compile(r'tgme_widget_message_document_title[^>]*>([^<]+)<')
# Cursor oficial de "cargar mensajes más antiguos" que pone el propio Telegram.
# Es lo mismo que ocurre al hacer scroll hacia el pasado en el navegador.
MORE_BEFORE_RE = re.compile(r'tme_messages_more[^>]*data-before="(\d+)"')
HREF_BEFORE_RE = re.compile(r'href="[^"]*\?before=(\d+)"')


def clean_text(fragment):
    """Convierte el HTML del cuerpo del mensaje en texto plano legible."""
    if not fragment:
        return ""
    t = fragment
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = re.sub(r'</p>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)        # quita el resto de etiquetas
    t = html.unescape(t)
    t = re.sub(r'\n{3,}', '\n\n', t).strip()
    return t


def parse_page(page_html):
    """Devuelve una lista de posts (dicts) de una página."""
    posts = []
    for m in MSG_RE.finditer(page_html):
        post_path = m.group(1)            # "SemyonSkrepetsky/2476"
        body = m.group(2)
        try:
            msg_id = int(post_path.split("/")[-1])
        except ValueError:
            continue

        photos = PHOTO_RE.findall(body)
        videos = VIDEO_SRC_RE.findall(body) + ROUNDVIDEO_RE.findall(body)
        vthumbs = VIDEO_THUMB_RE.findall(body)
        text_m = TEXT_RE.search(body)
        text = clean_text(text_m.group(1)) if text_m else ""
        time_m = TIME_RE.search(body)
        dt = time_m.group(1) if time_m else None
        views_m = VIEWS_RE.search(body)
        views = views_m.group(1).strip() if views_m else None
        doc_m = DOC_TITLE_RE.search(body)

        # enlaces externos dentro del texto (descartamos búsquedas internas
        # de hashtags y enlaces de previsualización del propio canal)
        links = []
        if text_m:
            for href in LINK_RE.findall(text_m.group(1)):
                href = html.unescape(href)
                if "/s/" in href or "?q=" in href:
                    continue
                if href not in links:
                    links.append(href)
        # hashtags
        tags = re.findall(r'#([^\s#<.,!?]+)', text)

        posts.append({
            "id": msg_id,
            "url": "https://t.me/" + post_path,
            "datetime": dt,
            "text": text,
            "photos": [html.unescape(u) for u in photos],
            "videos": [html.unescape(u) for u in videos],
            "video_thumbs": [html.unescape(u) for u in vthumbs],
            "document": doc_m.group(1).strip() if doc_m else None,
            "views": views,
            "links": links,
            "hashtags": tags,
        })
    return posts


# ---------------------------------------------------------------------------
# Descarga de medios
# ---------------------------------------------------------------------------
def date_folder(dt_iso):
    """'2024-06-12T18:24:00+00:00' -> '2024/06'. Si no hay fecha -> 'sin-fecha'."""
    if not dt_iso:
        return "sin-fecha"
    try:
        d = datetime.fromisoformat(dt_iso.replace("Z", "+00:00"))
        return f"{d.year:04d}/{d.month:02d}"
    except Exception:
        return "sin-fecha"


def download_media(post, do_download=True):
    """Descarga fotos/vídeos del post y añade rutas locales relativas."""
    sub = date_folder(post["datetime"])
    post["local_photos"] = []
    post["local_videos"] = []
    post["local_thumbs"] = []

    def grab(url, base_dir, prefix, idx, ext):
        rel = f"{sub}/{post['id']}_{prefix}{idx}.{ext}"
        dest = os.path.join(base_dir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        relpath = os.path.relpath(dest, ROOT).replace(os.sep, "/")
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            return relpath                       # ya descargado -> saltar
        if not do_download:
            return relpath
        data = fetch(url, binary=True)
        if data:
            with open(dest, "wb") as f:
                f.write(data)
            return relpath
        return None

    for i, url in enumerate(post["photos"]):
        p = grab(url, PHOTOS_DIR, "img", i, "jpg")
        if p:
            post["local_photos"].append(p)
    for i, url in enumerate(post["videos"]):
        p = grab(url, VIDEOS_DIR, "vid", i, "mp4")
        if p:
            post["local_videos"].append(p)
    for i, url in enumerate(post["video_thumbs"]):
        p = grab(url, THUMBS_DIR, "thumb", i, "jpg")
        if p:
            post["local_thumbs"].append(p)


# ---------------------------------------------------------------------------
# Bucle principal de rastreo (retrocede hasta el primer post del canal)
# ---------------------------------------------------------------------------
def next_cursor(page_html, ids):
    """Cursor para la SIGUIENTE página (más antigua).

    Prioriza el valor 'data-before' que el propio Telegram pone en su botón de
    'cargar más antiguos' (idéntico a hacer scroll hacia el pasado). Si no está,
    usa el id más pequeño visto en la página. Devuelve None si no hay más.
    """
    m = MORE_BEFORE_RE.search(page_html)
    if m:
        return int(m.group(1))
    # respaldo: el menor 'before=' que aparezca en algún enlace de la página
    befores = [int(x) for x in HREF_BEFORE_RE.findall(page_html)]
    if ids:
        befores = [b for b in befores if b < min(ids)]
    if befores:
        return min(befores)
    # último respaldo: seguir desde el id más antiguo de la página
    return min(ids) if ids else None


def crawl(channel, do_download=True, max_pages=None):
    all_posts = {}
    base_url = BASE.format(channel=channel)
    before = None
    page_n = 0
    seen_cursors = set()        # evita bucles infinitos
    oldest_seen = None

    while True:
        page_n += 1
        if max_pages and page_n > max_pages:
            print(f"-- límite de {max_pages} páginas alcanzado.")
            break
        url = base_url if before is None else f"{base_url}?before={before}"
        print(f"[página {page_n}] {url}")
        page_html = fetch(url)
        if not page_html:
            print("-- no se pudo descargar la página, fin.")
            break

        posts = parse_page(page_html)
        if not posts:
            print("-- no hay más posts: hemos llegado al PRINCIPIO del canal.")
            break

        ids = [p["id"] for p in posts]
        page_min, page_max = min(ids), max(ids)
        new = 0
        for p in posts:
            if p["id"] not in all_posts:
                download_media(p, do_download)
                all_posts[p["id"]] = p
                new += 1
        oldest_seen = page_min if oldest_seen is None else min(oldest_seen, page_min)
        print(f"   ids {page_min}-{page_max} | nuevos: {new} | "
              f"total: {len(all_posts)} | mas antiguo alcanzado: {oldest_seen}")

        # guardar progreso de forma incremental (reanudable)
        save_catalog(channel, all_posts)

        # ¿hacia dónde retrocedemos? (equivale a "scroll hacia el pasado")
        nxt = next_cursor(page_html, ids)
        if nxt is None:
            print("-- sin cursor anterior: fin del historial.")
            break
        if before is not None and nxt >= before:
            print("-- la paginacion no avanza: fin.")
            break
        if nxt in seen_cursors:
            print("-- cursor repetido (posible bucle): fin.")
            break
        seen_cursors.add(nxt)
        before = nxt
        time.sleep(REQUEST_DELAY)

    if oldest_seen is not None:
        print(f"-- post mas antiguo archivado: #{oldest_seen}")
    return all_posts


def save_catalog(channel, all_posts):
    ordered = sorted(all_posts.values(), key=lambda p: p["id"])
    catalog = {
        "channel": channel,
        "channel_url": f"https://t.me/{channel}",
        "title": "Картинная галерея Семёна Скрепецкого",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "post_count": len(ordered),
        "posts": ordered,
    }
    tmp = CATALOG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CATALOG)

    # Versión .js para que la web funcione abriendo index.html directamente
    # (sin servidor), evitando el bloqueo CORS de fetch() sobre file://
    js_path = os.path.join(ROOT, "catalog-data.js")
    os.makedirs(os.path.dirname(js_path), exist_ok=True)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CATALOG = ")
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        f.write(";\n")


# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    do_download = "--no-media" not in args
    channel = CHANNEL
    max_pages = None
    if "--channel" in args:
        channel = args[args.index("--channel") + 1]
    if "--limit" in args:
        max_pages = int(args[args.index("--limit") + 1])

    print(f"== Archivando @{channel} ==")
    print(f"   Descargar medios: {'SI' if do_download else 'NO (solo catalogo)'}")
    print(f"   Carpeta destino : {ROOT}\n")

    posts = crawl(channel, do_download=do_download, max_pages=max_pages)
    save_catalog(channel, posts)

    print(f"\n== Listo ==")
    print(f"   Posts archivados: {len(posts)}")
    print(f"   Catalogo        : {CATALOG}")
    print(f"   Fotos en        : {PHOTOS_DIR}")
    print(f"   Videos en       : {VIDEOS_DIR}")
    print(f"\nAbre index.html en tu navegador para ver la galeria.")


if __name__ == "__main__":
    main()
