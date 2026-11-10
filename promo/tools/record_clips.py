"""Запись клипов нового сайта и 3D-игры для промо-ролика (1080x1920, кадры с реальными таймингами).

Сайт берётся из локальной копии (python3 -m http.server в папке со сборкой), а ответы базы
подменяются НАСТОЯЩИМИ данными, выгруженными из Supabase (data/real.json) — ничего не выдумано.
Одобренные фото пользователей лежат в data/photos/ (используются с ником автора).

python3 record_clips.py http://localhost:8794 out_dir
"""
import sys, os, json, time, base64, shutil
from playwright.sync_api import sync_playwright

BASE, OUT = sys.argv[1].rstrip("/"), sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
REAL = json.load(open(os.path.join(here, "..", "data", "real.json")))
PH = os.path.join(here, "..", "data", "photos")
H = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}

def slowjs(F):
    return """(()=>{const F=%s;const pn=performance.now.bind(performance);const t0=pn();const d0=Date.now();
performance.now=()=>t0+(pn()-t0)*F; const DN=Date.now; Date.now=()=>d0+(DN()-d0)*F;
const raf=window.requestAnimationFrame.bind(window); window.requestAnimationFrame=cb=>raf(()=>cb(performance.now()));
const st=window.setTimeout.bind(window), si=window.setInterval.bind(window);
window.setTimeout=(f,d,...a)=>st(f,(d||0)/F,...a); window.setInterval=(f,d,...a)=>si(f,(d||0)/F,...a);
const fix=()=>{ try{ document.getAnimations().forEach(a=>{ if(a.playbackRate!==F) a.playbackRate=F; }); }catch(e){} raf(fix); }; raf(fix);
// плавная прокрутка по «времени страницы»
window.__scroll=(y,ms)=>{ document.documentElement.style.scrollBehavior="auto"; const y0=scrollY, t0=performance.now();
  const step=()=>{ const k=Math.min(1,(performance.now()-t0)/ms), e=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2; scrollTo(0,y0+(y-y0)*e); if(k<1) raf(step); }; raf(step); };
window.__at=(list)=>{ const t0=performance.now(); for(const [t,f] of list) setTimeout(f,t); };
})();""" % F

def handle(route):
    r = route.request; u = r.url
    if r.method == "OPTIONS": return route.fulfill(status=204, headers=H)
    if "/storage/v1/object/public/roof-photos/" in u:
        fn = os.path.join(PH, u.split("/")[-1])
        if os.path.exists(fn): return route.fulfill(status=200, headers=H, content_type="image/jpeg", body=open(fn, "rb").read())
        return route.fulfill(status=404, headers=H)
    name = u.split("/rpc/")[-1].split("?")[0] if "/rpc/" in u else ""
    a = json.loads(r.post_data or "{}")
    J = lambda v: route.fulfill(status=200, headers=H, content_type="application/json", body=json.dumps(v))
    if name == "register_visit": return J({"count": REAL["visitors"], "banned": False, "user": None})
    if name == "get_comments": return J(REAL["comments"].get(a.get("p_house"), []))
    if name == "house_been_count": return J(0)
    if name == "get_top_photos": return J(REAL["top_photos"])
    if name == "get_top_roofers": return J(REAL["top_roofers"])
    if name == "get_house_of_day": return J(REAL["hod"])
    if name == "get_custom_houses": return J(REAL["custom"])
    if name in ("get_post",): return J(None)
    if name == "get_notifications": return J({"unread": 0, "items": []})
    if name == "get_been": return J([])
    return J(None)

def record(ctx, url, dur, F, out, init=None, actions="", vw=(432, 768), scale=2.5, settle=1500):
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    pg = ctx.new_page()
    pg.route("https://hmkecihzribgeguzcwkt.supabase.co/**", handle)
    for pat in ["https://fonts.googleapis.com/**", "https://unpkg.com/**", "https://commons.wikimedia.org/**", "https://*.tile.openstreetmap.org/**", "https://*.basemaps.cartocdn.com/**"]:
        pg.route(pat, lambda r: r.abort())
    pg.goto(url); pg.wait_for_timeout(settle)
    if init: pg.evaluate(init)
    if actions: pg.evaluate("__at([" + actions + "])")
    cdp = ctx.new_cdp_session(pg)
    frames = []; t0 = time.time(); end = t0 + dur / F
    while time.time() < end:
        sy = cdp.send("Runtime.evaluate", {"expression": "scrollY", "returnByValue": True})["result"]["value"]
        r = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 88, "optimizeForSpeed": True,
                                                "clip": {"x": 0, "y": sy, "width": vw[0], "height": vw[1], "scale": scale}})
        frames.append(((time.time() - t0) * F, r["data"]))
    for i, (ts, d) in enumerate(frames):
        open(os.path.join(out, f"{i:05d}.jpg"), "wb").write(base64.b64decode(d))
    json.dump([ts for ts, _ in frames], open(os.path.join(out, "times.json"), "w"))
    pg.close(); print(out, "кадров:", len(frames), "≈fps:", round(len(frames) / dur, 1))

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"),
                          args=["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    ctx = b.new_context(viewport={"width": 432, "height": 768}, device_scale_factor=2.5, service_workers="block")
    ctx.add_init_script("try{localStorage.setItem('roof_token','');localStorage.removeItem('roof_token');localStorage.setItem('roofer_doors','true')}catch(e){}")
    ctx.add_init_script(slowjs(0.25))
    S = BASE + "/index.html"
    # 1. первый экран сайта — фото с крыши и заголовок
    record(ctx, S, 4.2, 0.25, f"{OUT}/hero", init="document.getElementById('authScreen')&&(document.getElementById('authScreen').style.display='none')",
           actions="[600,()=>__scroll(120,3200)]")
    # 2. рулетка: прокрутка к кнопке, «Крутить», карточка
    record(ctx, S, 6.0, 0.25, f"{OUT}/spin", init="document.getElementById('authScreen').style.display='none'; scrollTo(0,document.querySelector('.panel').getBoundingClientRect().top+scrollY-90)",
           actions="[300,()=>document.getElementById('spin').click()],[3300,()=>__scroll(document.getElementById('card').getBoundingClientRect().top+scrollY-70,1400)]")
    # 3. поиск «1812» → ЖК «Корона» с настоящими фото с крыши
    record(ctx, S, 7.0, 0.25, f"{OUT}/korona", init="document.getElementById('authScreen').style.display='none'; scrollTo(0,document.querySelector('.panel').getBoundingClientRect().top+scrollY-90)",
           actions="""[200,()=>{const q=document.getElementById('q'); q.focus(); let s='1812 126',i=0; const ty=()=>{ q.value=s.slice(0,++i); q.dispatchEvent(new Event('input')); if(i<s.length) setTimeout(ty,110); }; ty(); }],
                      [1700,()=>document.querySelector('#qres .mrow').click()],
                      [2600,()=>__scroll(document.querySelector('.comments').getBoundingClientRect().top+scrollY-60,1800)],
                      [4700,()=>__scroll(document.querySelector('.comments').getBoundingClientRect().top+scrollY+330,1900)]""")
    # 4. фильтры: ТЦ / Светлогорск
    record(ctx, S, 4.6, 0.25, f"{OUT}/filters", init="document.getElementById('authScreen').style.display='none'; scrollTo(0,document.querySelector('.panel').getBoundingClientRect().top+scrollY-90)",
           actions="""[300,()=>{const c=document.getElementById('cat'); c.value='hotel'; c.dispatchEvent(new Event('change'));}],
                      [900,()=>{const d=document.getElementById('district'); d.value='@Светлогорск'; d.dispatchEvent(new Event('change'));}],
                      [1500,()=>document.getElementById('spin').click()]""")
    # 5. топ видов с крыш (настоящие одобренные фото)
    record(ctx, S, 4.0, 0.25, f"{OUT}/top", init="document.getElementById('authScreen').style.display='none'; scrollTo(0,document.getElementById('roofers-sec').getBoundingClientRect().top+scrollY-70)",
           actions="[700,()=>__scroll(document.getElementById('top-sec').getBoundingClientRect().top+scrollY-70,1800)]")
    # 6. 3D-игра на автопилоте
    G = BASE + "/game/index.html?auto"
    record(ctx, G, 9.0, 0.02, f"{OUT}/game", settle=3500,
           actions="[30,()=>document.getElementById('play').click()],[60,()=>document.getElementById('skip1').click()]")
    b.close()
