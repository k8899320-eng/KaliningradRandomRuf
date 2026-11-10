import json, time, subprocess, os, glob
from playwright.sync_api import sync_playwright

H = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "*", "Access-Control-Allow-Methods": "*"}

def J(route, obj, status=200):
    route.fulfill(status=status, headers=H, content_type="application/json", body=json.dumps(obj))

def supa(route):
    r = route.request
    if r.method == "OPTIONS":
        return route.fulfill(status=204, headers=H)
    u = r.url
    name = u.split("/rpc/")[-1] if "/rpc/" in u else ""
    if name == "register_visit":
        return J(route, {"count": None, "banned": False, "user": {"nick": "V1n41k", "admin": False}})
    if name == "get_comments":
        return J(route, [])
    if name == "get_post":
        return J(route, None)
    if name == "get_ankets":
        return J(route, [])
    if "/rest/v1/comments" in u:  # таблица лидеров игры
        return J(route, [])
    return J(route, {})

def block(route):
    route.abort()

CAPTION_CSS = """
#cap{position:fixed;left:0;right:0;z-index:2147483000;display:flex;justify-content:center;pointer-events:none;padding:0 18px}
#cap .c{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-weight:900;color:#fff;text-align:center;
  font-size:34px;line-height:1.12;letter-spacing:-.01em;padding:14px 18px;border-radius:22px;
  background:rgba(10,12,18,.78);box-shadow:0 18px 50px -10px rgba(0,0,0,.8);border:2px solid rgba(255,176,61,.55);
  animation:pop .45s cubic-bezier(.2,1.4,.4,1) both}
#cap .c em{font-style:normal;color:#ffb03d}
#cap .s{display:block;font-size:19px;font-weight:700;color:#cfd5e1;margin-top:6px}
@keyframes pop{from{transform:scale(.6) translateY(20px);opacity:0}to{transform:none;opacity:1}}
#hand{position:fixed;z-index:2147483001;font-size:46px;pointer-events:none;transition:all .45s ease;filter:drop-shadow(0 6px 10px rgba(0,0,0,.6))}
"""

def caption(pg, html, top=None, bottom=None):
    pos = f"top:{top}px" if top is not None else f"bottom:{bottom}px"
    pg.evaluate("""([css, html, pos])=>{
      if(!document.getElementById('capcss')){ const s=document.createElement('style'); s.id='capcss'; s.textContent=css; document.head.appendChild(s); }
      let c=document.getElementById('cap'); if(c) c.remove();
      c=document.createElement('div'); c.id='cap'; c.setAttribute('style',pos); c.innerHTML='<div class="c">'+html+'</div>'; document.body.appendChild(c);
    }""", [CAPTION_CSS, html, pos])

def hand(pg, sel):
    pg.evaluate("""(sel)=>{ const el=document.querySelector(sel); if(!el) return; const r=el.getBoundingClientRect();
      let h=document.getElementById('hand'); if(!h){ h=document.createElement('div'); h.id='hand'; h.textContent='👆'; document.body.appendChild(h);
        h.style.left=(r.left+r.width/2-10)+'px'; h.style.top=(innerHeight)+'px'; }
      requestAnimationFrame(()=>{ h.style.left=(r.left+r.width/2-10)+'px'; h.style.top=(r.top+r.height/2)+'px'; }); }""", sel)

def nohand(pg):
    pg.evaluate("()=>{ const h=document.getElementById('hand'); if(h) h.remove(); }")

BOT = """()=>{ clearInterval(window.__bot); window.__bot=setInterval(()=>{
  if(state!=='play'||player.dead||hang||fin) return;
  const wx=camX+player.x;
  if(player.ground && player.on){ const r=player.on; if(r.x+r.w-wx<14){ jumpPress(); setTimeout(jumpRelease,400); } }
},5)}"""


F = 0.3  # замедление времени на странице
SLOWJS = """(()=>{const F=%s;const pn=performance.now.bind(performance);const t0=pn();const d0=Date.now();
performance.now=()=>t0+(pn()-t0)*F; const DN=Date.now; Date.now=()=>d0+(DN()-d0)*F;
const raf=window.requestAnimationFrame.bind(window); window.requestAnimationFrame=cb=>raf(()=>cb(performance.now()));
const st=window.setTimeout.bind(window), si=window.setInterval.bind(window);
window.setTimeout=(f,d,...a)=>st(f,(d||0)/F,...a); window.setInterval=(f,d,...a)=>si(f,(d||0)/F,...a);
const fix=()=>{ try{ document.getAnimations().forEach(a=>{ if(a.playbackRate!==F) a.playbackRate=F; }); }catch(e){} raf(fix); }; raf(fix);
})();""" % F

marks = {}
os.makedirs("raw", exist_ok=True)
for f in glob.glob("raw/*.webm"): os.remove(f)

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": 432, "height": 768}, device_scale_factor=2.5, service_workers="block")
    ctx.add_init_script(SLOWJS)
    ctx.add_init_script("try{localStorage.setItem('roof_token','demo');localStorage.setItem('roof_nick','V1n41k');localStorage.setItem('roofer_best','0')}catch(e){}")
    pg = ctx.new_page()
    pg.route("https://hmkecihzribgeguzcwkt.supabase.co/**", supa)
    for pat in ["https://commons.wikimedia.org/**", "https://tile.openstreetmap.org/**", "https://unpkg.com/**", "https://fonts.googleapis.com/**"]:
        pg.route(pat, block)
    import base64
    frames=[]
    cdp = ctx.new_cdp_session(pg)
    capturing=[False]
    def grab():
        y=cdp.send("Runtime.evaluate",{"expression":"window.scrollY","returnByValue":True})["result"].get("value",0) or 0
        r=cdp.send("Page.captureScreenshot",{"format":"jpeg","quality":90,"optimizeForSpeed":True,"clip":{"x":0,"y":y,"width":432,"height":768,"scale":2.5}})
        frames.append((time.time(), r["data"]))
    def start_cast(): capturing[0]=True
    def W(ms):
        end=time.time()+ms/1000/F
        while time.time()<end:
            if capturing[0]: grab()
            else: time.sleep(0.02)
    t0 = time.time()
    mark = lambda k: marks.__setitem__(k, time.time())

    pg.goto("http://localhost:8800/index.html")
    pg.add_style_tag(content="#photo,#thumbs,#map{display:none!important} .topbar{display:none} html,body{scroll-behavior:auto!important}")
    pg.wait_for_timeout(1500)
    start_cast(); W(200)

    # 1. Хук
    mark("s1")
    caption(pg, "Куда залезть сегодня<br>в <em>Калининграде?</em> 🏢", top=300)
    W(2600)

    # 2. Рандомайзер
    mark("s2")
    pg.evaluate("document.querySelector('.panel').scrollIntoView({block:'center'})")
    W(500)
    caption(pg, "Жми — и сайт выдаст<br><em>случайную высотку</em> 🎰", top=40)
    hand(pg, "#spin"); W(700)
    pg.click("#spin"); nohand(pg)
    W(3300)
    pg.evaluate("document.getElementById('card').scrollIntoView({block:'start'})")
    caption(pg, "Адрес, этажность<br>и <em>панорама</em> улицы 📍", bottom=60)
    W(2300)

    # 3. Фото с крыш и комментарии
    mark("s3")
    pg.evaluate("document.getElementById('comments').scrollIntoView({block:'start'})")
    caption(pg, "Делись <em>видом с крыши</em> 📷<br><span class='s'>фото, лайки, комментарии</span>", bottom=70)
    hand(pg, ".filebtn"); W(2400); nohand(pg)

    # 4. Карта и избранное
    mark("s4")
    pg.evaluate("window.scrollTo(0,0)"); W(300)
    pg.evaluate("document.getElementById('stats').scrollIntoView({block:'center'})")
    caption(pg, "<em>676 высоток</em> города<br>в одном месте 🗺️", top=60)
    W(2200)

    # 5. Игра
    mark("s5")
    pg.goto("http://localhost:8800/game/index.html")
    W(500)
    pg.evaluate("startDoors(); startRun(); speed=330;")
    pg.evaluate(BOT)
    caption(pg, "Мини-игра: <em>убеги от полиции</em><br>по крышам 🚨", top=95)
    W(4200)

    # 6. CTA
    mark("s6")
    pg.goto("http://localhost:8800/index.html")
    pg.add_style_tag(content=".topbar{display:none}")
    W(700)
    pg.evaluate("""()=>{ const d=document.createElement('div'); d.innerHTML=`<div style="position:fixed;inset:0;z-index:2147482000;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;text-align:center;padding:24px;
       background:radial-gradient(500px 400px at 50% 40%,rgba(255,106,61,.35),transparent 70%),rgba(8,10,16,.92);font-family:system-ui,sans-serif;color:#fff;animation:fi .5s both">
       <div style="font-size:70px">🏢</div>
       <div style="font-weight:900;font-size:40px;line-height:1.05">РУФ·РАНДОМАЙЗЕР<br><span style="color:#ff6a3d">КАЛИНИНГРАД</span></div>
       <div style="font-weight:800;font-size:22px;background:#ffb03d;color:#1a0d06;border-radius:14px;padding:12px 16px;line-height:1.25">k8899320-eng.github.io<br>/KaliningradRandomRuf</div>
       <div style="font-weight:800;font-size:24px">👉 ссылка в профиле</div>
       <div style="font-size:14px;color:#aab2c5;max-width:320px">Береги себя: крыши опасны, а без разрешения — нарушение закона</div></div>
       <style>@keyframes fi{from{opacity:0;transform:scale(1.06)}to{opacity:1;transform:none}}</style>`; document.body.appendChild(d); }""")
    W(3300)
    mark("end")
    ctx.close(); b.close()
    import shutil
    shutil.rmtree("frames", ignore_errors=True); os.makedirs("frames")
    T0 = frames[0][0]
    lines=["ffconcat version 1.0"]
    for i,(ts,data) in enumerate(frames):
        fn=f"frames/{i:05d}.jpg"; open(fn,"wb").write(base64.b64decode(data))
        dur = (frames[i+1][0]-ts) if i+1<len(frames) else 0.5
        lines += [f"file '{fn}'", f"duration {max(0.001,dur):.4f}"]
    lines.append(f"file 'frames/{len(frames)-1:05d}.jpg'")
    open("frames.txt","w").write("\n".join(lines))
    marks["cast_t0_wall"] = T0
    vpath = f"{len(frames)} frames"

marks["F"]=F
json.dump(marks, open("marks.json", "w"))
print(marks, vpath)
