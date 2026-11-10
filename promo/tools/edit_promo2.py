"""Монтаж ролика «новый сайт + 3D-игра» под фонк-бит (склейки ровно по тактам).

python3 edit_promo2.py <папка_клипов> <музыка.wav> <выход.mp4>
Подписи — как пишут в ТикТоке: белый жирный текст с обводкой, строчными, без «нейро-градиентов».
"""
import sys, os, json, bisect, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

CL, MUS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
here = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
BAR = 60 / 140 * 4
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT2 = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
PH = os.path.join(here, "..", "data", "photos")
ASSETS = os.path.join(here, "..", "..", "assets")

class Clip:
    def __init__(s, name):
        s.dir = os.path.join(CL, name); s.t = json.load(open(os.path.join(s.dir, "times.json"))); s.cache = {}
    def at(s, t):
        i = max(0, min(len(s.t) - 1, bisect.bisect_left(s.t, t)))
        if i not in s.cache:
            if len(s.cache) > 40: s.cache.clear()
            s.cache[i] = Image.open(os.path.join(s.dir, f"{i:05d}.jpg")).convert("RGB").resize((W, H))
        return s.cache[i]

def cover(img, w=W, h=H):
    k = max(w / img.width, h / img.height); im = img.resize((int(img.width * k) + 1, int(img.height * k) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))

def still(path):
    im = Image.open(path).convert("RGB")
    k = max(W * 1.25 / im.width, H * 1.25 / im.height)
    return im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)

def kenburns(big, p, z0=1.0, z1=1.12, dx=0, seed=0):
    # «с рук»: медленный зум + лёгкое покачивание
    z = z0 + (z1 - z0) * p
    w, h = big.width / (1.25 * z), big.height / (1.25 * z)
    cx = big.width / 2 + dx * p * big.width + math.sin(p * 9 + seed) * 6
    cy = big.height / 2 + math.cos(p * 7 + seed) * 6
    return big.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((W, H), Image.BILINEAR)

def punch(img, dt, amt=.07, dur=.22):
    if dt >= dur: return img
    z = 1 + amt * (1 - dt / dur) ** 2; w, h = int(W / z), int(H / z)
    return img.crop(((W - w) // 2, (H - h) // 2, (W - w) // 2 + w, (H - h) // 2 + h)).resize((W, H), Image.BILINEAR)

_fonts = {}
def F(path, size):
    k = (path, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) > maxw and cur: lines.append(cur); cur = w_
        else: cur = t
    if cur: lines.append(cur)
    return lines

def caption(img, text, dt, y=0.25, size=74, dur=None):
    """Подпись в «родном» стиле ТикТока: белые плашки со скруглением, чёрный текст; выскакивает за 0.12 с."""
    if dt < 0 or (dur and dt > dur): return
    sc = .85 + .15 * min(1, dt / .12)
    f = F(FONT, max(10, int(size * sc)))
    d = ImageDraw.Draw(img)
    lines = wrap(d, text, f, W - 190)
    pad_x, pad_y = int(f.size * .42), int(f.size * .2)
    lh = int(f.size * 1.32); y0 = int(H * y) - lh * len(lines) // 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    for k, ln in enumerate(lines):
        tw = ld.textlength(ln, font=f); x = (W - tw) / 2; yy = y0 + k * lh
        ld.rounded_rectangle((x - pad_x, yy - pad_y, x + tw + pad_x, yy + f.size + pad_y * 1.4), radius=int(f.size * .3), fill=(255, 255, 255, 246))
    for k, ln in enumerate(lines):
        tw = ld.textlength(ln, font=f); x = (W - tw) / 2; yy = y0 + k * lh
        ld.text((x, yy - f.size * .06), ln, font=f, fill=(12, 12, 14, 255))
    img.paste(layer, (0, 0), layer)

def small(img, text, x, y, size=34, anchor="la"):
    d = ImageDraw.Draw(img)
    d.text((x, y), text, font=F(FONT2, size), fill="white", stroke_width=3, stroke_fill=(0, 0, 0), anchor=anchor)

# ---------- материалы ----------
C = {n: Clip(n) for n in ["hero", "spin", "korona", "filters", "game"]}
P1 = still(os.path.join(PH, "mwaqawkk-f8sxo2.jpg"))   # закат с «Короны»
P2 = still(os.path.join(PH, "mwaqc0og-aizw9i.jpg"))   # вид на дома
T = [0, 2 * BAR, 4 * BAR, 6 * BAR, 8 * BAR, 9 * BAR, 11 * BAR, 12 * BAR + 1.5]
DUR = T[-1]

def frame(t):
    if t < T[1]:
        p = t / T[1]; img = kenburns(P1, p, 1.0, 1.14, .02)
        caption(img, "калининград с крыши", t - .15, .2)
        caption(img, "но как найти, куда залезть?", t - BAR, .32, 62)
        small(img, "фото: @zhev_urbex · с моего сайта", 50, H - 120, 32)
    elif t < T[2]:
        dt = t - T[1]; img = punch(C["hero"].at(.25 + dt * 1.05).copy(), dt)
        caption(img, "я сделал сайт для руферов", dt, .62, 70)
    elif t < T[3]:
        dt = t - T[2]; img = punch(C["spin"].at(.15 + dt * 1.15).copy(), dt)
        caption(img, "жмёшь — и выпадает рандомная высотка", dt, .7, 64)
    elif t < T[4]:
        dt = t - T[3]; img = punch(C["korona"].at(.2 + dt * 1.95).copy(), dt)
        caption(img, "поиск по адресу + виды с крыш от своих", dt, .72, 62)
    elif t < T[5]:
        dt = t - T[4]; img = punch(C["filters"].at(.2 + dt * 2.5).copy(), dt, .05)
        caption(img, "отели, тц, светлогорск, балтийск", dt, .72, 62)
    elif t < T[6]:
        dt = t - T[5]; img = punch(C["game"].at(1.6 + dt * 1.35).copy(), dt, .09)
        caption(img, "а ещё 3D-игра: убегай от полиции по крышам", dt, .64, 62)
    else:
        dt = t - T[6]; p = dt / (T[7] - T[6]); img = kenburns(P2, p, 1.08, 1.0, -.015, 2)
        img = ImageEnhance.Brightness(img).enhance(.82)
        caption(img, "ссылка в профиле", dt, .42, 92)
        caption(img, "руф-рандомайзер калининград", dt - .45, .52, 54)
        small(img, "лезь только туда, куда можно. береги себя", W // 2, H - 170, 34, "ma")
        small(img, "фото: @zhev_urbex", 50, H - 110, 30)
        if T[7] - t < .5: img = ImageEnhance.Brightness(img).enhance(max(0, (T[7] - t) / .5))
    # короткая белая вспышка на дропах
    for tc in (T[1], T[5]):
        if 0 <= t - tc < .08: img = Image.blend(img, Image.new("RGB", (W, H), "white"), .55 * (1 - (t - tc) / .08))
    return img

n = int(DUR * FPS)
ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-i", MUS, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
                       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for i in range(n):
    ff.stdin.write(frame(i / FPS).tobytes())
    if i % 90 == 0: print(f"{i}/{n}", flush=True)
ff.stdin.close(); ff.wait(); print("готово:", OUT, round(DUR, 2), "с")
