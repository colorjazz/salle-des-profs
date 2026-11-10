import re, subprocess, time, json, html, sys
BASE='https://www.quebec.ca'
PREF='/education/prescolaire-primaire-et-secondaire/programmes-formations-evaluation/'
depart=[PREF+'programme-formation-ecole-quebecoise/primaire', PREF+'programme-formation-ecole-quebecoise/secondaire',
        PREF+'epreuves-ministerielles-evaluation-apprentissages/cadres-evaluation/primaire-secondaire']
vus=set(); file=list(depart); pdfs={}; pages=0
while file and pages < 80:
    p=file.pop(0)
    if p in vus: continue
    vus.add(p)
    r=subprocess.run(['curl','-sS','-m','30',BASE+p],capture_output=True,text=True); pages+=1
    t=r.stdout
    titre=html.unescape(re.sub(r'\s+',' ',(re.search(r'<title>(.*?)</title>',t,re.S) or [None,''])[1])).strip()
    for m in re.finditer(r'href="([^"]+\.pdf)[^"]*"[^>]*>(.*?)</a>',t,re.S):
        u=m.group(1); u=u if u.startswith('http') else 'https://www.quebec.ca'+u if u.startswith('/') else u
        lib=html.unescape(re.sub(r'<[^>]+>|\s+',' ',m.group(2))).strip()
        if 'cdn-contenu.quebec.ca' in u and u not in pdfs: pdfs[u]={'libelle':lib,'page':p,'titre_page':titre}
    for m in re.finditer(r'href="(%s[^"#?]+)"'%re.escape(PREF),t):
        q=m.group(1).rstrip('/')
        if q not in vus and ('programme-formation-ecole-quebecoise/' in q or 'cadres-evaluation/' in q): file.append(q)
    time.sleep(0.4)
json.dump(pdfs,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('pages lues',pages,'PDF trouves',len(pdfs),'reste en file',len(file))
