#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpia el "pie" de cada publicación en data/catalog.json:
elimina la fecha, las vistas y los enlaces (el "original ↗" y enlaces externos).

Borra de CADA post estos campos, si existen:
    url, external_link, links, datetime, time_label, views

Luego regenera catalog-data.js (lo que lee la web).
NO toca las fotos ni los vídeos ya descargados. Es seguro ejecutarlo varias veces.

Uso:
    python scripts/limpiar_pie.py
"""

import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "data", "catalog.json")
JS = os.path.join(ROOT, "catalog-data.js")
BACKUP = os.path.join(ROOT, "data", "catalog.backup.json")

CAMPOS_A_BORRAR = ("url", "external_link", "links", "datetime", "time_label", "views")


def main():
    if not os.path.exists(CATALOG):
        print(f"No se encontró {CATALOG}. Ejecuta primero archive_skrepetsky.py.")
        return

    with open(CATALOG, encoding="utf-8") as f:
        data = json.load(f)

    # Copia de seguridad (solo la primera vez)
    if not os.path.exists(BACKUP):
        with open(BACKUP, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Copia de seguridad creada: {BACKUP}")

    posts = data.get("posts", [])
    quitados = {c: 0 for c in CAMPOS_A_BORRAR}
    for p in posts:
        for c in CAMPOS_A_BORRAR:
            if c in p:
                del p[c]
                quitados[c] += 1

    # Guardar catalog.json de forma atómica
    tmp = CATALOG + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CATALOG)

    # Regenerar catalog-data.js (lo que carga la web)
    os.makedirs(os.path.dirname(JS), exist_ok=True)
    with open(JS, "w", encoding="utf-8") as f:
        f.write("window.CATALOG = ")
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"Publicaciones procesadas: {len(posts)}")
    for c, n in quitados.items():
        print(f"   campo '{c}' eliminado en {n} posts")
    print(f"\nActualizado: {CATALOG}")
    print(f"Actualizado: {JS}")
    print("Listo. Abre index.html para comprobarlo.")


if __name__ == "__main__":
    main()
