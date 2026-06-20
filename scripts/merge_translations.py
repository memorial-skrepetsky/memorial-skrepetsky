#!/usr/bin/env python3
# Merges English translations (data/tr/*.json, each {"<idx>":"en"}) into the catalog.
# idx refers to position in data/_to_translate.json (each entry has 'ids' + 'ru').
import json, glob, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
units=json.load(open(os.path.join(ROOT,'data','_to_translate.json'),encoding='utf-8'))
tr={}
for f in sorted(glob.glob(os.path.join(ROOT,'data','tr','*.json'))):
    part=json.load(open(f,encoding='utf-8'))
    for k,v in part.items():
        tr[int(k)]=v
# map id -> english
id2en={}
for idx,unit in enumerate(units):
    if idx in tr:
        for pid in unit['ids']:
            id2en[pid]=tr[idx]
cat=json.load(open(os.path.join(ROOT,'data','catalog.json'),encoding='utf-8'))
n=0
for p in cat['posts']:
    if p['id'] in id2en:
        p['text_en']=id2en[p['id']]; n+=1
cat['translated_count']=n
json.dump(cat, open(os.path.join(ROOT,'data','catalog.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
# regenerate catalog-data.js
with open(os.path.join(ROOT,'catalog-data.js'),'w',encoding='utf-8') as f:
    f.write('window.CATALOG=')
    json.dump(cat, f, ensure_ascii=False)
    f.write(';')
print(f'translated units available: {len(tr)} / {len(units)}')
print(f'posts with text_en: {n} / {len(cat["posts"])}')
