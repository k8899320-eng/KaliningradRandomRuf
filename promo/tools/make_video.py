"""Записывает HTML-анимацию 432x768 в плавное MP4 1080x1920 30fps с музыкой.

python3 make_video.py <url> <длительность_сек> <выход.mp4>

Время на странице замедляется в F раз, кадры снимаются в полном разрешении,
затем ролик собирается с реальными таймингами. Музыка генерируется music.py.
"""
import sys, time, base64, os, shutil, subprocess
from playwright.sync_api import sync_playwright

url, dur, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
here = os.path.dirname(os.path.abspath(__file__))
F = 0.3
SLOWJS = """(()=>{const F=%s;const pn=performance.now.bind(performance);const t0=pn();const d0=Date.now();
performance.now=()=>t0+(pn()-t0)*F; const DN=Date.now; Date.now=()=>d0+(DN()-d0)*F;
const raf=window.requestAnimationFrame.bind(window); window.requestAnimationFrame=cb=>raf(()=>cb(performance.now()));
const st=window.setTimeout.bind(window), si=window.setInterval.bind(window);
window.setTimeout=(f,d,...a)=>st(f,(d||0)/F,...a); window.setInterval=(f,d,...a)=>si(f,(d||0)/F,...a);
const fix=()=>{ try{ document.getAnimations().forEach(a=>{ if(a.playbackRate!==F) a.playbackRate=F; }); }catch(e){} raf(fix); }; raf(fix);
})();""" % F

fdir = os.path.join(here, "frames_mv"); shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
frames = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 432, "height": 768}, device_scale_factor=2.5)
    ctx.add_init_script(SLOWJS)
    pg = ctx.new_page()
    for pat in ["https://fonts.googleapis.com/**", "https://unpkg.com/**"]:
        pg.route(pat, lambda r: r.abort())
    pg.goto(url); pg.wait_for_timeout(300)
    cdp = ctx.new_cdp_session(pg)
    t0 = time.time(); end = t0 + dur / F
    while time.time() < end:
        r = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 90, "optimizeForSpeed": True,
                                                "clip": {"x": 0, "y": 0, "width": 432, "height": 768, "scale": 2.5}})
        frames.append((time.time(), r["data"]))
    b.close()

lines = ["ffconcat version 1.0"]
for i, (ts, data) in enumerate(frames):
    fn = os.path.join(fdir, f"{i:05d}.jpg"); open(fn, "wb").write(base64.b64decode(data))
    d = ((frames[i + 1][0] - ts) * F) if i + 1 < len(frames) else 0.1
    lines += [f"file '{fn}'", f"duration {d:.4f}"]
lines.append(f"file '{os.path.join(fdir, f'{len(frames)-1:05d}.jpg')}'")
lst = os.path.join(here, "frames_mv.txt"); open(lst, "w").write("\n".join(lines))
print("кадров:", len(frames), "≈fps:", round(len(frames) / dur, 1))

subprocess.run([sys.executable, os.path.join(here, "music.py"), str(dur)], cwd=here, check=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(here, "music.wav"),
                "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
print("готово:", out)
