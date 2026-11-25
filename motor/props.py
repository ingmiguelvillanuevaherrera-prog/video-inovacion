# Huellitas: personajes (perro, gato, equipo), utilería, fondos y tarjetas.
import math, random, functools
from PIL import Image, ImageDraw, ImageOps
from gfx import *
import overlays as ov

CREAM = (252, 242, 226)
SAGE = (128, 172, 134)
SAGE_D = (92, 136, 102)
WOOD = (176, 120, 78)
WOOD_D = (136, 88, 54)
COFFEE = (118, 78, 52)
ROSE = (238, 150, 150)
TEAL = ov.TEAL
CORAL = ov.CORAL
GREEN = ov.GREEN
INK = ov.INK
BLUSH = (240, 150, 140)
STEEL = (196, 204, 212)
STEEL_D = (150, 160, 170)

DOG_C = (214, 160, 98)
DOG_D = (162, 108, 60)
DOG_L = (248, 226, 194)


def paw(c, x, y, r, col, outline=None, w=0):
    """Huella: cojinete + 4 dedos."""
    c.ell((x - r, y - r * 0.55, x + r, y + r * 0.95), fill=col, outline=outline, w=w)
    for dx, dy in ((-0.95, -0.85), (-0.35, -1.35), (0.35, -1.35), (0.95, -0.85)):
        c.circ(x + dx * r, y + dy * r, r * 0.36, fill=col, outline=outline, w=w)


# ------------------------------------------------------------------ perro
@functools.lru_cache(maxsize=400)
def dog(expr="happy", tail=0, blink=False, scale=1.0, hat=None, look=(0.0, 0.0), col=DOG_C, mirror=False):
    """Perro sentado de frente, 320x440 unidades, patas en y≈434. tail en -2..2 (meneo)."""
    dark = mix(col, (60, 40, 25), 0.3)
    light = mix(col, (255, 248, 236), 0.65)
    c = Cv(320, 440, ss=2, k=scale * K, mode="RGBA")
    oy = 80
    # cola
    a = math.radians(-70 + 22 * tail)
    tx, ty = 228, 300 + oy
    c.limb([(tx, ty), (tx + 46 * math.cos(a + 0.5), ty + 46 * math.sin(a + 0.5)), (tx + 84 * math.cos(a), ty + 84 * math.sin(a))], 22, dark)
    # cuerpo
    c.ell((84, 166 + oy, 236, 350 + oy), fill=col)
    c.ell((122, 196 + oy, 198, 318 + oy), fill=light, outline=None)
    c.ell((62, 268 + oy, 132, 352 + oy), fill=col)
    c.ell((188, 268 + oy, 258, 352 + oy), fill=col)
    c.rect((114, 246 + oy, 150, 344 + oy), fill=col, r=16)
    c.rect((170, 246 + oy, 206, 344 + oy), fill=col, r=16)
    c.ell((102, 326 + oy, 156, 356 + oy), fill=light)
    c.ell((164, 326 + oy, 218, 356 + oy), fill=light)
    # collar
    c.rect((110, 170 + oy, 210, 194 + oy), fill=(222, 72, 84), r=10)
    c.circ(160, 202 + oy, 11, fill=(250, 204, 64))
    # cabeza
    hy = 108 + oy
    c.ell((70, hy - 82, 250, hy + 80), fill=col)
    down = expr == "sad"
    for sgn in (-1, 1):
        X = lambda x: 160 + sgn * (x - 160)
        if down:
            pts = [(X(96), hy - 60), (X(64), hy - 40), (X(54), hy + 50), (X(70), hy + 92), (X(98), hy + 70), (X(106), hy - 10)]
        else:
            pts = [(X(96), hy - 66), (X(58), hy - 56), (X(36), hy + 14), (X(48), hy + 62), (X(80), hy + 48), (X(104), hy - 20)]
        c.poly(pts, fill=dark)
    # hocico
    c.ell((116, hy + 6, 204, hy + 66), fill=light)
    # ojos
    lx, ly = look
    for ex in (126, 194):
        if blink:
            c.arc((ex - 16, hy - 24, ex + 16, hy + 4), 20, 160, w=5)
        else:
            c.ell((ex - 17, hy - 32, ex + 17, hy + 8), fill=(255, 255, 255))
            px, py = ex + lx * 6, hy - 10 + ly * 6
            c.circ(px, py, 10, fill=OUT, outline=None)
            c.circ(px - 3, py - 4, 3.5, fill=(255, 255, 255), outline=None)
    if down:
        c.line([(104, hy - 44), (136, hy - 34)], w=6)
        c.line([(184, hy - 34), (216, hy - 44)], w=6)
    # nariz
    c.poly([(144, hy + 14), (176, hy + 14), (160, hy + 34)], fill=OUT, w=6)
    c.circ(153, hy + 18, 3, fill=(120, 120, 130), outline=None)
    # boca
    if expr == "happy":
        c.chord((136, hy + 30, 184, hy + 70), 0, 180, fill=MOUTH, w=4)
        c.ell((148, hy + 46, 172, hy + 82), fill=(238, 110, 130), w=4)
    elif expr == "sad":
        c.arc((140, hy + 44, 180, hy + 70), 200, 340, w=5)
    else:
        c.arc((134, hy + 26, 162, hy + 50), 20, 160, w=5)
        c.arc((158, hy + 26, 186, hy + 50), 20, 160, w=5)
    # mejillas
    c.ell((90, hy + 22, 114, hy + 36), fill=BLUSH, outline=None)
    c.ell((206, hy + 22, 230, hy + 36), fill=BLUSH, outline=None)
    # gorros
    if hat == "chef":
        for (x, y, r) in ((122, hy - 112, 30), (198, hy - 112, 30), (160, hy - 128, 36)):
            c.circ(x, y, r, fill=(255, 255, 255))
        c.rect((114, hy - 104, 206, hy - 68), fill=(255, 255, 255), r=6)
        paw(c, 160, hy - 84, 7, OUT)
    elif hat == "party":
        c.poly([(128, hy - 72), (192, hy - 72), (166, hy - 160)], fill=(90, 170, 230))
        c.line([(140, hy - 98), (184, hy - 104)], fill=(255, 214, 64), w=7)
        c.line([(152, hy - 128), (176, hy - 132)], fill=(240, 90, 120), w=6)
        c.circ(166, hy - 162, 12, fill=(255, 214, 64))
    im = c.final()
    return ImageOps.mirror(im) if mirror else im


# ------------------------------------------------------------------ gato
@functools.lru_cache(maxsize=64)
def cat(blink=False, scale=1.0, col=(150, 150, 160), tail=0):
    c = Cv(260, 360, ss=2, k=scale * K, mode="RGBA")
    dark = mix(col, (40, 40, 50), 0.35)
    a = math.radians(10 + 14 * tail)
    c.limb([(180, 320), (232, 300), (240 + 6 * math.cos(a), 230 + 10 * math.sin(a)), (214, 196)], 18, dark)
    c.ell((70, 170, 190, 350), fill=col)
    c.ell((100, 210, 160, 320), fill=mix(col, (255, 255, 255), 0.6), outline=None)
    c.ell((86, 326, 128, 354), fill=col)
    c.ell((132, 326, 174, 354), fill=col)
    for sgn in (-1, 1):
        X = lambda x: 130 + sgn * (x - 130)
        c.poly([(X(62), 120), (X(70), 30), (X(116), 80)], fill=col)
        c.poly([(X(74), 100), (X(78), 52), (X(104), 82)], fill=(240, 170, 180), outline=None)
    c.ell((50, 56, 210, 196), fill=col)
    for ex in (100, 160):
        if blink:
            c.arc((ex - 14, 106, ex + 14, 130), 20, 160, w=5)
        else:
            c.ell((ex - 15, 98, ex + 15, 134), fill=(200, 230, 120))
            c.ell((ex - 4, 102, ex + 4, 130), fill=OUT, outline=None)
    c.poly([(122, 142), (138, 142), (130, 152)], fill=(240, 140, 150), w=3)
    c.arc((112, 146, 132, 166), 20, 160, w=4)
    c.arc((128, 146, 148, 166), 20, 160, w=4)
    for dy in (-6, 6):
        c.line([(30, 150 + dy), (90, 152)], w=3)
        c.line([(170, 152), (230, 150 + dy)], w=3)
    return c.final()


# ------------------------------------------------------------------ equipo Huellitas
STAFF = {
    "jaqueline": dict(skin=(226, 176, 136), hair=(78, 46, 30), style="long", shirt=(238, 150, 150), glasses=False),
    "daniela": dict(skin=(201, 142, 99), hair=(34, 28, 26), style="bun", shirt=(120, 170, 220), glasses=True),
    "cocinera": dict(skin=(166, 110, 74), hair=(118, 62, 38), style="pony", shirt=(248, 200, 84), glasses=False),
}
APRON = (126, 84, 56)


@functools.lru_cache(maxsize=600)
def staff(who, mouth=0, blink=False, arms="down", scale=1.0, look=(0.0, 0.0), hat=False, mirror=False, brows="up"):
    """Integrante del equipo con mandil. 300x560 unidades, pies en y≈530."""
    cf = STAFF[who]
    skin, hair, shirt = cf["skin"], cf["hair"], cf["shirt"]
    c = Cv(300, 560, ss=2, k=scale * K, mode="RGBA")
    cx, hy = 150, 128
    if cf["style"] == "long":
        c.rect((cx - 92, 62, cx + 92, 318), fill=hair, r=56)
    if cf["style"] == "pony":
        c.ell((cx + 50, 70, cx + 120, 270), fill=hair)
    # piernas
    c.rect((cx - 64, 380, cx - 22, 508), fill=(52, 56, 72), r=14)
    c.rect((cx + 22, 380, cx + 64, 508), fill=(52, 56, 72), r=14)
    c.ell((cx - 80, 492, cx - 18, 530), fill=(60, 50, 46))
    c.ell((cx + 18, 492, cx + 80, 530), fill=(60, 50, 46))
    # brazo de atrás en "hold" no aplica; brazos detrás del torso no se dibujan
    c.rect((cx - 72, 200, cx + 72, 394), fill=shirt, r=46)
    # mandil
    c.rect((cx - 52, 254, cx + 52, 404), fill=APRON, r=16)
    c.rect((cx - 34, 212, cx + 34, 266), fill=APRON, r=8)
    c.line([(cx - 34, 214), (cx - 46, 202)], fill=APRON, w=8)
    c.line([(cx + 34, 214), (cx + 46, 202)], fill=APRON, w=8)
    paw(c, cx, 240, 11, CREAM)
    c.rect((cx - 28, 330, cx + 28, 366), fill=None, outline=mix(APRON, (0, 0, 0), 0.35), w=4, r=6)
    # brazos
    hand = lambda x, y: c.circ(x, y, 17, fill=skin)
    if arms == "down":
        c.limb([(cx - 62, 222), (cx - 80, 300), (cx - 82, 352)], 34, shirt); hand(cx - 82, 362)
        c.limb([(cx + 62, 222), (cx + 80, 300), (cx + 82, 352)], 34, shirt); hand(cx + 82, 362)
    elif arms == "wave":
        c.limb([(cx - 62, 222), (cx - 80, 300), (cx - 82, 352)], 34, shirt); hand(cx - 82, 362)
        c.limb([(cx + 62, 222), (cx + 102, 166), (cx + 110, 104)], 34, shirt); hand(cx + 110, 92)
    elif arms == "point":
        c.limb([(cx - 62, 222), (cx - 80, 300), (cx - 82, 352)], 34, shirt); hand(cx - 82, 362)
        c.limb([(cx + 62, 222), (cx + 104, 196), (cx + 132, 146)], 34, shirt); hand(cx + 136, 136)
    elif arms == "open":
        c.limb([(cx - 62, 222), (cx - 96, 292), (cx - 124, 262)], 34, shirt); hand(cx - 128, 254)
        c.limb([(cx + 62, 222), (cx + 96, 292), (cx + 124, 262)], 34, shirt); hand(cx + 128, 254)
    elif arms == "hold":
        c.limb([(cx - 62, 222), (cx - 74, 300), (cx - 40, 318)], 34, shirt)
        c.limb([(cx + 62, 222), (cx + 74, 300), (cx + 40, 318)], 34, shirt)
        c.rect((cx - 62, 262, cx + 62, 344), fill=(44, 48, 58), r=10)
        c.rect((cx - 52, 270, cx + 52, 336), fill=(120, 200, 196), outline=None, r=6)
        for i in range(3):
            c.rect((cx - 42, 280 + i * 18, cx + 10 + i * 10, 290 + i * 18), fill=(255, 255, 255), outline=None, r=4)
        hand(cx - 42, 318); hand(cx + 42, 318)
    # cabeza
    c.circ(cx - 80, hy + 8, 16, fill=skin)
    c.circ(cx + 80, hy + 8, 16, fill=skin)
    c.circ(cx, hy, 82, fill=skin)
    # pelo
    pts = []
    for ang in range(192, 350, 8):
        a = math.radians(ang)
        pts.append((cx + 90 * math.cos(a), hy + 2 + 90 * math.sin(a)))
    xs = list(range(cx + 82, cx - 90, -16))
    for i, x in enumerate(xs):
        pts.append((x, hy - 44 + 26 * ((x - cx) / 80) ** 2 + (12 if i % 2 else 0)))
    c.poly(pts, fill=hair)
    if cf["style"] == "bun":
        c.circ(cx, hy - 96, 32, fill=hair)
    if cf["style"] == "pony":
        c.circ(cx + 74, hy - 40, 12, fill=(240, 90, 110))
    if hat:
        for (x, y, r) in ((cx - 52, hy - 104, 36), (cx + 52, hy - 104, 36), (cx, hy - 124, 44)):
            c.circ(x, y, r, fill=(255, 255, 255))
        c.rect((cx - 72, hy - 96, cx + 72, hy - 50), fill=(255, 255, 255), r=8)
        paw(c, cx, hy - 72, 9, OUT)
    # cara
    lx, ly = look
    for ex in (cx - 32, cx + 32):
        if blink:
            c.arc((ex - 15, hy - 6, ex + 15, hy + 14), 20, 160, w=5)
        else:
            c.ell((ex - 15, hy - 18, ex + 15, hy + 18), fill=(255, 255, 255))
            px, py = ex + lx * 5, hy + 2 + ly * 5
            c.circ(px, py, 8.5, fill=OUT, outline=None)
            c.circ(px - 3, py - 3, 3, fill=(255, 255, 255), outline=None)
        sg = -1 if ex < cx else 1
        c.line([(ex + sg * 13, hy - 14), (ex + sg * 21, hy - 20)], w=4)
    by = hy - 34
    if brows == "up":
        c.line([(cx - 46, by), (cx - 18, by - 4)], fill=hair, w=6)
        c.line([(cx + 18, by - 4), (cx + 46, by)], fill=hair, w=6)
    else:
        c.line([(cx - 46, by - 4), (cx - 18, by + 2)], fill=hair, w=6)
        c.line([(cx + 18, by + 2), (cx + 46, by - 4)], fill=hair, w=6)
    if cf["glasses"]:
        c.circ(cx - 32, hy, 23, fill=None, w=4)
        c.circ(cx + 32, hy, 23, fill=None, w=4)
        c.line([(cx - 9, hy), (cx + 9, hy)], w=4)
    c.ell((cx - 66, hy + 22, cx - 40, hy + 36), fill=BLUSH, outline=None)
    c.ell((cx + 40, hy + 22, cx + 66, hy + 36), fill=BLUSH, outline=None)
    c.arc((cx - 8, hy + 8, cx + 8, hy + 24), 300, 60, w=3)
    if mouth == 0:
        c.arc((cx - 20, hy + 22, cx + 20, hy + 52), 20, 160, w=5)
    elif mouth == 1:
        c.chord((cx - 16, hy + 32, cx + 16, hy + 54), 0, 180, fill=MOUTH, w=4)
    else:
        c.chord((cx - 20, hy + 28, cx + 20, hy + 64), 0, 180, fill=MOUTH, w=4)
        c.chord((cx - 11, hy + 50, cx + 11, hy + 62), 180, 360, fill=(236, 110, 130), outline=None)
    im = c.final()
    return ImageOps.mirror(im) if mirror else im


# ------------------------------------------------------------------ mariposa
@functools.lru_cache(maxsize=80)
def butterfly(q, col, scale):
    f = (1.0, 0.72, 0.4, 0.18, 0.45, 0.8)[q]
    c = Cv(130, 110, ss=2, k=scale * K, mode="RGBA")
    m = 65
    dk = mix(col, (0, 0, 0), 0.25)
    c.ell((m - 56 * f, 8, m + 2, 60), fill=col, w=4)
    c.ell((m - 2, 8, m + 56 * f, 60), fill=col, w=4)
    c.ell((m - 40 * f, 50, m + 2, 92), fill=dk, w=4)
    c.ell((m - 2, 50, m + 40 * f, 92), fill=dk, w=4)
    c.ell((m - 6, 26, m + 6, 90), fill=OUT, outline=None)
    c.line([(m - 2, 30), (m - 14, 6)], w=3)
    c.line([(m + 2, 30), (m + 14, 6)], w=3)
    return c.final()


BFLY_COLS = [(255, 214, 120), (250, 170, 200), (190, 170, 240), (255, 255, 255), (150, 220, 200)]


def _put(img, spr, x, y):
    img.paste(spr, (int(x * K - spr.width / 2), int(y * K - spr.height / 2)), spr)


def butterflies(img, T, spots, scale=0.6):
    for i, (x, y) in enumerate(spots):
        xx = x + 60 * math.sin(T * 0.7 + i * 1.9) + 20 * math.sin(T * 2.1 + i)
        yy = y + 40 * math.sin(T * 0.9 + i * 2.7)
        q = int(T * 14 + i * 2) % 6
        _put(img, butterfly(q, BFLY_COLS[i % len(BFLY_COLS)], scale), xx, yy)


# ------------------------------------------------------------------ fondos
def tree(c, x, y, r, col=(98, 160, 92)):
    c.rect((x - 22, y, x + 22, y + 700), fill=(120, 84, 58))
    dk = mix(col, (0, 0, 0), 0.18)
    for dx, dy, rr in ((-0.55, 0.15, 0.7), (0.55, 0.15, 0.7), (0, -0.35, 0.8), (0, 0.25, 0.75)):
        c.circ(x + dx * r, y + dy * r, rr * r, fill=dk if dy > 0 else col)


def draw_street(c, sunset=False):
    if sunset:
        c.vgrad((0, 0, 1080, 1500), [(0, (126, 92, 160)), (0.5, (240, 130, 120)), (1, (255, 196, 128))])
    else:
        c.vgrad((0, 0, 1080, 1500), [(0, (140, 200, 236)), (1, (214, 238, 246))])
    # edificio art déco de fondo
    c.rect((-10, 330, 1090, 1520), fill=(238, 206, 176))
    c.rect((-10, 330, 1090, 372), fill=(214, 176, 140))
    for x in range(60, 1080, 200):
        c.rect((x, 420, x + 110, 560), fill=(170, 200, 214), r=4)
        c.line([(x + 55, 420), (x + 55, 560)], w=4)
        c.rect((x - 8, 556, x + 118, 572), fill=(214, 176, 140), r=4)
    # banqueta
    c.rect((-10, 1500, 1090, 1930), fill=(206, 200, 190))
    for x in range(-40, 1100, 180):
        c.line([(x, 1500), (x - 60, 1930)], fill=(184, 178, 168), w=4)
    c.line([(0, 1640), (1080, 1640)], fill=(184, 178, 168), w=4)
    c.line([(0, 1500), (1080, 1500)], w=5)


def storefront_plain(c):
    c.rect((110, 640, 970, 1504), fill=(88, 104, 122))
    c.rect((130, 820, 520, 1420), fill=(176, 206, 222))
    c.line([(170, 1100), (320, 900)], fill=(220, 236, 244), w=14)
    c.line([(220, 1150), (370, 950)], fill=(220, 236, 244), w=8)
    c.rect((580, 820, 930, 1504), fill=(70, 84, 100))
    c.rect((610, 850, 900, 1474), fill=(160, 190, 206))
    c.circ(626, 1170, 10, fill=(210, 200, 120))
    # toldo gris
    for i, x in enumerate(range(90, 990, 90)):
        c.rect((x, 690, x + 90, 790), fill=(110, 116, 126) if i % 2 else (210, 212, 216), w=4)
    c.line([(90, 790), (990, 790)], w=5)
    c.rect((300, 600, 780, 680), fill=(60, 66, 76), r=10)
    c.text((540, 640), "CAFÉ", 50, fill=(230, 230, 230))


def storefront_huellitas(c):
    c.rect((90, 620, 990, 1504), fill=CREAM)
    for y in range(660, 1500, 44):
        c.line([(92, y), (988, y)], fill=(236, 222, 200), w=3)
    # ventana con interior cálido
    c.rect((130, 900, 500, 1400), fill=(255, 214, 150), r=12)
    c.glow(315, 1150, 230, (255, 240, 200), 0.5)
    for (x, y) in ((220, 1080), (400, 1240)):
        paw(c, x, y, 26, (236, 150, 100))
    c.line([(315, 900), (315, 1400)], w=6)
    c.rect((120, 1394, 510, 1420), fill=SAGE_D, r=6)
    # puerta abierta
    c.rect((600, 880, 920, 1504), fill=(255, 220, 160))
    c.glow(760, 1200, 260, (255, 246, 210), 0.55)
    c.poly([(600, 880), (680, 910), (680, 1474), (600, 1504)], fill=SAGE)
    c.rect((590, 870, 930, 896), fill=SAGE_D, r=6)
    c.ell((640, 1470, 880, 1530), fill=(226, 120, 110))
    paw(c, 760, 1498, 12, (255, 220, 200))
    # número
    c.rect((940, 1060, 1040, 1120), fill=(40, 60, 70), r=8)
    c.text((990, 1090), "165", 34, fill=(255, 255, 255))
    # toldo festoneado
    for i, x in enumerate(range(70, 1010, 94)):
        c.rect((x, 740, x + 94, 820), fill=SAGE if i % 2 else (250, 246, 236), w=4)
        c.chord((x, 790, x + 94, 850), 0, 180, fill=SAGE if i % 2 else (250, 246, 236), w=4)
    c.rect((60, 712, 1020, 744), fill=SAGE_D, r=8)
    # macetas
    for x in (70, 560):
        c.poly([(x - 34, 1420), (x + 34, 1420), (x + 24, 1504), (x - 24, 1504)], fill=(214, 110, 80))
        for k in range(5):
            a = math.radians(200 + k * 35)
            c.ell((x + 40 * math.cos(a) - 22, 1400 + 50 * math.sin(a) - 30, x + 40 * math.cos(a) + 22, 1400 + 50 * math.sin(a) + 30), fill=(96, 160, 96))
    # pizarrón
    c.poly([(150, 1500), (210, 1250), (230, 1250), (290, 1500)], fill=None, w=6)
    c.rect((180, 1240, 400, 1420), fill=(44, 54, 50), w=6, r=8)
    c.text((290, 1300), "PET", 40, fill=(255, 255, 255))
    c.text((290, 1350), "FRIENDLY", 34, fill=(255, 214, 64))
    paw(c, 290, 1395, 12, (255, 255, 255))
    # plato de agua
    c.ell((440, 1486, 540, 1520), fill=(90, 150, 210))
    c.ell((452, 1488, 528, 1504), fill=(170, 220, 250), outline=None)


def draw_interior(c, frames=True, window=True, wall=((252, 236, 212), (244, 218, 186))):
    c.vgrad((0, 0, 1080, 1480), [(0, wall[0]), (1, wall[1])])
    pc = mix(wall[1], (210, 170, 130), 0.35)
    rng = random.Random(4)
    for y in range(560, 1080, 170):
        for x in range(60 + (y // 170 % 2) * 90, 1080, 180):
            paw(c, x + rng.uniform(-10, 10), y, 11, pc)
    c.rect((-10, 1100, 1090, 1484), fill=SAGE)
    for x in range(30, 1080, 150):
        c.rect((x, 1146, x + 112, 1440), fill=None, outline=SAGE_D, w=4, r=10)
    c.rect((-10, 1090, 1090, 1110), fill=SAGE_D)
    c.vgrad((0, 1480, 1080, 1920), [(0, (192, 138, 94)), (1, (150, 102, 66))])
    for i, y in enumerate(range(1550, 1920, 72)):
        c.line([(0, y), (1080, y)], fill=(150, 102, 66), w=3)
        for x in range(-60 + (i % 2) * 120, 1080, 240):
            c.line([(x, y - 72 if i else 1480), (x, y)], fill=(150, 102, 66), w=3)
    c.line([(0, 1480), (1080, 1480)], w=6)
    if window:
        c.rect((640, 620, 980, 1020), fill=(160, 214, 236), w=8, r=10)
        c.circ(730, 820, 70, fill=(110, 176, 104), outline=None)
        c.circ(880, 770, 84, fill=(96, 164, 92), outline=None)
        c.line([(810, 620), (810, 1020)], w=6)
        c.line([(640, 820), (980, 820)], w=6)
        c.rect((626, 1010, 994, 1036), fill=WOOD, r=6)
    if frames:
        for (x0, y0, w, h, bg, kind) in ((90, 640, 200, 230, (246, 200, 190), "dog"), (330, 700, 170, 170, (200, 220, 246), "cat")):
            c.rect((x0, y0, x0 + w, y0 + h), fill=WOOD, r=8)
            c.rect((x0 + 16, y0 + 16, x0 + w - 16, y0 + h - 16), fill=bg, w=4)
            mx, my = x0 + w / 2, y0 + h / 2 + 10
            if kind == "dog":
                c.ell((mx - 70, my - 40, mx - 30, my + 40), fill=DOG_D, w=4)
                c.ell((mx + 30, my - 40, mx + 70, my + 40), fill=DOG_D, w=4)
                c.circ(mx, my, 48, fill=DOG_C, w=4)
                c.circ(mx, my + 20, 10, fill=OUT, outline=None)
            else:
                c.poly([(mx - 44, my - 10), (mx - 36, my - 62), (mx - 6, my - 34)], fill=(150, 150, 160), w=4)
                c.poly([(mx + 44, my - 10), (mx + 36, my - 62), (mx + 6, my - 34)], fill=(150, 150, 160), w=4)
                c.circ(mx, my, 44, fill=(150, 150, 160), w=4)
            for ex in (-16, 16):
                c.circ(mx + ex, my - 4, 6, fill=OUT, outline=None)
    # foquitos
    pts = [(x, 520 + 40 * math.sin(x / 1080 * math.pi)) for x in range(-20, 1110, 20)]
    c.line(pts, fill=(60, 50, 40), w=3)
    for i, x in enumerate(range(30, 1080, 90)):
        y = 528 + 40 * math.sin(x / 1080 * math.pi)
        col = ((255, 214, 120), (255, 170, 150), (180, 230, 200))[i % 3]
        c.glow(x, y + 10, 34, col, 0.45)
        c.ell((x - 10, y, x + 10, y + 26), fill=col, w=3)


def counter_layer(items=("espresso", "case"), steel=False):
    """Barra en primer plano (RGBA), tapa en y=1400."""
    c = Cv(W, H, 2, K, mode="RGBA")
    if steel:
        c.rect((-10, 1420, 1090, 1930), fill=STEEL)
        for x in range(60, 1080, 260):
            c.rect((x, 1470, x + 200, 1700), fill=None, outline=STEEL_D, w=4, r=8)
            c.line([(x + 70, 1500), (x + 130, 1500)], fill=STEEL_D, w=8)
        c.rect((-10, 1396, 1090, 1428), fill=(226, 232, 238))
    else:
        c.rect((-10, 1420, 1090, 1930), fill=WOOD)
        for x in range(0, 1080, 60):
            c.line([(x, 1428), (x, 1930)], fill=WOOD_D, w=3)
        c.rect((-10, 1396, 1090, 1430), fill=(236, 226, 210))
        paw(c, 540, 1540, 34, CREAM)
    if "espresso" in items:
        c.rect((760, 1180, 1000, 1400), fill=(200, 60, 60), r=18)
        c.rect((780, 1200, 980, 1260), fill=(240, 240, 240), r=8)
        c.circ(880, 1230, 18, fill=(60, 60, 60))
        c.rect((820, 1260, 940, 1300), fill=(70, 70, 70), r=6)
        c.rect((840, 1330, 900, 1398), fill=(255, 255, 255), r=6)
        c.arc((890, 1344, 920, 1376), 270, 90, w=5)
    if "case" in items:
        c.rect((20, 1230, 300, 1398), fill=(210, 236, 246), r=10)
        for i, (x, col) in enumerate(((70, (220, 150, 90)), (150, (240, 200, 130)), (230, (170, 110, 80)))):
            c.ell((x - 36, 1330, x + 36, 1380), fill=col)
            c.ell((x - 26, 1300, x + 26, 1346), fill=mix(col, (255, 255, 255), 0.3))
        c.line([(30, 1290), (290, 1290)], fill=(255, 255, 255), w=4)
    if "pos" in items:
        c.rect((610, 1250, 760, 1400), fill=(48, 52, 62), r=16)
        c.rect((626, 1266, 744, 1330), fill=(140, 220, 200), r=8)
        for i in range(3):
            for j in range(3):
                c.rect((634 + j * 38, 1342 + i * 18, 664 + j * 38, 1354 + i * 18), fill=(200, 204, 210), outline=None, r=3)
        c.text((685, 1298), "$", 40, fill=(255, 255, 255))
    if "printer" in items:
        c.rect((760, 1290, 980, 1400), fill=(70, 76, 88), r=14)
        c.rect((790, 1290, 950, 1306), fill=(30, 30, 36), r=4)
        c.circ(950, 1350, 10, fill=(90, 220, 120))
    if "cups" in items:
        for x in (380, 470):
            c.rect((x, 1330, x + 60, 1398), fill=(255, 255, 255), r=8)
            paw(c, x + 30, 1368, 9, COFFEE)
    return lay_final_rgba(c)


def lay_final_rgba(cv):
    im = cv.final()
    bb = im.getbbox() or (0, 0, 1, 1)
    return im.crop(bb), (bb[0], bb[1])


def draw_kitchen(c):
    c.vgrad((0, 0, 1080, 1420), [(0, (236, 242, 244)), (1, (222, 230, 234))])
    for y in range(500, 1420, 60):
        c.line([(0, y), (1080, y)], fill=(204, 214, 220), w=3)
    for x in range(0, 1080, 60):
        c.line([(x, 500), (x, 1420)], fill=(204, 214, 220), w=3)
    # campana
    c.poly([(80, 330), (560, 330), (640, 600), (0, 600)], fill=STEEL)
    c.rect((-10, 596, 650, 630), fill=STEEL_D)
    # repisa con ollas
    c.rect((640, 900, 1080, 922), fill=WOOD)
    for x, w_, h_ in ((700, 110, 80), (840, 90, 110), (970, 100, 70)):
        c.rect((x - w_ / 2, 900 - h_, x + w_ / 2, 900), fill=STEEL_D, r=10)
        c.line([(x - w_ / 2 - 16, 900 - h_ + 14), (x - w_ / 2, 900 - h_ + 14)], w=8)
    # riel de comandas
    c.rect((560, 1060, 1060, 1076), fill=STEEL_D)
    for x in (600, 720, 840):
        c.rect((x, 1068, x + 90, 1210), fill=(255, 255, 255), w=4)
        for k in range(4):
            c.line([(x + 14, 1100 + k * 24), (x + 76 - (k % 2) * 20, 1100 + k * 24)], fill=(150, 150, 160), w=4)
    c.rect((-10, 1420, 1090, 1930), fill=(150, 156, 166))


def draw_bodega(c):
    c.vgrad((0, 0, 1080, 1500), [(0, (214, 208, 198)), (1, (196, 188, 176))])
    for y in range(520, 1500, 80):
        for x in range(0 + (y // 80 % 2) * 60, 1080, 120):
            c.rect((x, y, x + 120, y + 80), fill=None, outline=(186, 178, 166), w=3)
    for y in (800, 1080, 1360):
        c.rect((480, y, 1080, y + 24), fill=WOOD)
    c.rect((490, 640, 510, 1500), fill=WOOD_D)
    rng = random.Random(9)
    for y in (800, 1080, 1360):
        x = 540
        while x < 1050:
            kind = rng.choice(["sack", "box", "milk", "food"])
            if kind == "sack":
                c.ell((x, y - 130, x + 120, y + 6), fill=(196, 160, 110))
                c.text((x + 60, y - 60), "CAFÉ", 26, fill=COFFEE)
                x += 130
            elif kind == "box":
                c.rect((x, y - 110, x + 110, y), fill=(210, 170, 120))
                c.line([(x + 55, y - 110), (x + 55, y - 70)], fill=(160, 120, 80), w=5)
                x += 120
            elif kind == "milk":
                for k in range(2):
                    c.rect((x + k * 46, y - 100, x + k * 46 + 40, y), fill=(250, 250, 250))
                    c.rect((x + k * 46, y - 70, x + k * 46 + 40, y - 46), fill=(90, 150, 220), outline=None)
                x += 100
            else:
                c.rect((x, y - 140, x + 100, y), fill=(230, 120, 80), r=10)
                paw(c, x + 50, y - 64, 18, (255, 240, 220))
                x += 112
    c.rect((-10, 1500, 1090, 1930), fill=(160, 156, 150))
    c.line([(0, 1500), (1080, 1500)], w=5)


def draw_rooftop(c):
    c.vgrad((0, 0, 1080, 1500), [(0, (120, 190, 240)), (1, (220, 240, 250))])
    c.glow(860, 640, 160, (255, 250, 200), 0.7)
    c.circ(860, 640, 70, fill=(255, 226, 110), w=5)
    for (x, y, s) in ((200, 760, 1.0), (620, 900, 0.8)):
        for dx, dy, r in ((-60, 10, 50), (0, -10, 64), (60, 10, 50)):
            c.circ(x + dx * s, y + dy * s, r * s, fill=(255, 255, 255), outline=None)
    rng = random.Random(5)
    x = -20
    while x < 1100:
        w_ = rng.uniform(110, 190)
        h_ = rng.uniform(220, 420)
        col = rng.choice([(232, 150, 140), (244, 200, 120), (140, 190, 200), (200, 170, 220), (238, 220, 190)])
        c.rect((x, 1420 - h_, x + w_, 1430), fill=col)
        for yy in range(int(1420 - h_ + 30), 1400, 60):
            for xx in range(int(x + 20), int(x + w_ - 30), 46):
                c.rect((xx, yy, xx + 24, yy + 32), fill=(250, 246, 220), outline=None)
        x += w_ + rng.uniform(4, 20)
    c.rect((-10, 1430, 1090, 1500), fill=(190, 120, 100))
    c.rect((-10, 1500, 1090, 1930), fill=(206, 190, 176))
    c.line([(0, 1500), (1080, 1500)], w=5)


def draw_terrace(c):
    c.vgrad((0, 0, 1080, 1500), [(0, (120, 90, 164)), (0.45, (238, 128, 120)), (0.8, (255, 196, 128)), (1, (255, 214, 150))])
    c.glow(540, 1260, 300, (255, 240, 190), 0.6)
    c.circ(540, 1300, 110, fill=(255, 226, 140), outline=None)
    for x, r in ((60, 200), (1020, 220), (300, 120), (800, 140)):
        c.circ(x, 1260, r, fill=(90, 70, 110), outline=None)
    c.rect((-10, 1300, 1090, 1500), fill=(110, 84, 120))
    # barandal
    c.rect((-10, 1290, 1090, 1312), fill=(70, 56, 70))
    for x in range(20, 1080, 70):
        c.rect((x, 1310, x + 14, 1500), fill=(70, 56, 70), outline=None)
    c.vgrad((0, 1500, 1080, 1920), [(0, (196, 130, 92)), (1, (150, 96, 70))])
    c.line([(0, 1500), (1080, 1500)], w=5)
    pts = [(x, 560 + 50 * math.sin(x / 1080 * math.pi)) for x in range(-20, 1110, 20)]
    c.line(pts, fill=(60, 40, 50), w=3)
    for i, x in enumerate(range(30, 1080, 80)):
        y = 568 + 50 * math.sin(x / 1080 * math.pi)
        c.glow(x, y + 10, 40, (255, 230, 150), 0.6)
        c.ell((x - 10, y, x + 10, y + 26), fill=(255, 230, 150), w=3)


def chair_back(c, x, seat_y, col=WOOD):
    c.rect((x - 100, seat_y - 280, x + 100, seat_y - 250), fill=col, r=10)
    c.rect((x - 96, seat_y - 280, x - 70, seat_y + 10), fill=col)
    c.rect((x + 70, seat_y - 280, x + 96, seat_y + 10), fill=col)
    c.rect((x - 110, seat_y - 6, x + 110, seat_y + 22), fill=col, r=6)
    c.rect((x - 100, seat_y + 22, x - 80, seat_y + 150), fill=col)
    c.rect((x + 80, seat_y + 22, x + 100, seat_y + 150), fill=col)


def round_table(c, x, top_y, w=280, col=WOOD):
    c.rect((x - 16, top_y, x + 16, top_y + 220), fill=WOOD_D)
    c.ell((x - 80, top_y + 200, x + 80, top_y + 236), fill=WOOD_D)
    c.ell((x - w / 2, top_y - 30, x + w / 2, top_y + 30), fill=col)


# ------------------------------------------------------------------ tarjetas (pantalla)
S = 2


def _f(n, sz):
    return font(n, sz * S)


@functools.lru_cache(maxsize=16)
def phone_card(n, listo):
    w, h = 440, 600
    im, d = ov.card_base(w, h, fill=(34, 34, 40), radius=56)
    d.rounded_rectangle([22 * S, 22 * S, (w - 22) * S, (h - 22) * S], radius=40 * S, fill=(252, 246, 236))
    d.rounded_rectangle([22 * S, 22 * S, (w - 22) * S, 104 * S], radius=40 * S, fill=SAGE)
    d.rectangle([22 * S, 70 * S, (w - 22) * S, 104 * S], fill=SAGE)
    d.text((w // 2 * S, 64 * S), "Huellitas", font=_f("black", 40), fill=(255, 255, 255), anchor="mm")
    rows = ["Apartar mesa", "Ver menú", "Pedir", "Pagar", "Seguir pedido"]
    for i, s in enumerate(rows):
        y = 122 + i * 72
        d.rounded_rectangle([42 * S, y * S, (w - 42) * S, (y + 58) * S], radius=16 * S, fill=(255, 255, 255), outline=(210, 204, 196), width=3 * S)
        done = i < n
        cxy = (78, y + 29)
        d.ellipse([(cxy[0] - 17) * S, (cxy[1] - 17) * S, (cxy[0] + 17) * S, (cxy[1] + 17) * S], fill=GREEN if done else (236, 232, 226), outline=OUT, width=3 * S)
        if done:
            d.line([((cxy[0] - 8) * S, (cxy[1]) * S), ((cxy[0] - 2) * S, (cxy[1] + 7) * S), ((cxy[0] + 9) * S, (cxy[1] - 7) * S)], fill=(255, 255, 255), width=5 * S, joint="curve")
        d.text((110 * S, (y + 29) * S), s, font=_f("bold", 32), fill=INK if done or i == n else (150, 146, 140), anchor="lm")
    if listo:
        d.rounded_rectangle([60 * S, 494 * S, (w - 60) * S, 560 * S], radius=33 * S, fill=GREEN, outline=OUT, width=5 * S)
        d.text((w // 2 * S, 527 * S), "¡LISTO!", font=_f("black", 40), fill=(255, 255, 255), anchor="mm")
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=4)
def blueprint_card():
    w, h = 900, 400
    im, d = ov.card_base(w, h, fill=(36, 92, 150))
    for x in range(40, w, 40):
        d.line([(x * S, 12 * S), (x * S, (h - 12) * S)], fill=(60, 116, 172), width=2 * S)
    for y in range(40, h, 40):
        d.line([(12 * S, y * S), ((w - 12) * S, y * S)], fill=(60, 116, 172), width=2 * S)
    d.text((w // 2 * S, 52 * S), "ARQUITECTURA TECNOLÓGICA", font=_f("black", 42), fill=(255, 255, 255), anchor="mm")
    boxes = [("CLIENTE", "web · kiosco · QR", 170), ("OPERACIÓN", "comandas · pagos", 450), ("DATOS", "Club · inventario", 730)]
    for t, sub, x in boxes:
        d.rounded_rectangle([(x - 120) * S, 120 * S, (x + 120) * S, 330 * S], radius=20 * S, fill=None, outline=(255, 255, 255), width=5 * S)
        d.text((x * S, 200 * S), t, font=_f("black", 38), fill=(255, 255, 255), anchor="mm")
        d.text((x * S, 262 * S), sub, font=_f("semi", 25), fill=(200, 226, 250), anchor="mm")
    for x in (290, 570):
        d.line([(x * S, 225 * S), ((x + 40) * S, 225 * S)], fill=(255, 214, 64), width=7 * S)
        d.polygon([((x + 40) * S, 212 * S), ((x + 40) * S, 238 * S), ((x + 52) * S, 225 * S)], fill=(255, 214, 64))
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=64)
def clock_card(minutes_q, label):
    """Reloj con la manecilla en minutes_q (0..60, cuantizado) y etiqueta grande."""
    w, h = 560, 430
    im, d = ov.card_base(w, h)
    cx, cy, r = 150, 215, 120
    d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=(255, 255, 255), outline=OUT, width=8 * S)
    a1 = -math.pi / 2
    a2 = -math.pi / 2 + 2 * math.pi * minutes_q / 60
    d.pieslice([(cx - r + 12) * S, (cy - r + 12) * S, (cx + r - 12) * S, (cy + r - 12) * S], math.degrees(a1), math.degrees(a2) if minutes_q > 0 else math.degrees(a1) + 0.1, fill=(255, 200, 190))
    for k in range(12):
        a = k * math.pi / 6
        d.line([((cx + (r - 22) * math.cos(a)) * S, (cy + (r - 22) * math.sin(a)) * S), ((cx + (r - 8) * math.cos(a)) * S, (cy + (r - 8) * math.sin(a)) * S)], fill=OUT, width=5 * S)
    d.line([(cx * S, cy * S), ((cx + (r - 30) * math.cos(a2)) * S, (cy + (r - 30) * math.sin(a2)) * S)], fill=CORAL, width=9 * S)
    d.line([(cx * S, cy * S), (cx * S, (cy - 60) * S)], fill=OUT, width=9 * S)
    d.ellipse([(cx - 12) * S, (cy - 12) * S, (cx + 12) * S, (cy + 12) * S], fill=OUT)
    d.text((410 * S, 120 * S), "ESPERA", font=_f("black", 40), fill=INK, anchor="mm")
    col = GREEN if label == "5" else CORAL
    d.text((410 * S, 230 * S), label, font=_f("black", 160), fill=col, anchor="mm")
    d.text((410 * S, 340 * S), "minutos", font=_f("bold", 40), fill=INK, anchor="mm")
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=4)
def qr_card():
    w, h = 330, 380
    im, d = ov.card_base(w, h)
    n, cell, x0, y0 = 21, 12, 39, 34
    rng = random.Random(7)
    grid = [[rng.random() < 0.5 for _ in range(n)] for _ in range(n)]
    for (fx, fy) in ((0, 0), (n - 7, 0), (0, n - 7)):
        for i in range(7):
            for j in range(7):
                ring = i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4)
                grid[fy + i][fx + j] = ring
            if fx + 7 < n:
                grid[fy + i][fx + 7] = False
    for i in range(n):
        for j in range(n):
            if grid[i][j]:
                d.rectangle([(x0 + j * cell) * S, (y0 + i * cell) * S, (x0 + (j + 1) * cell) * S - 1, (y0 + (i + 1) * cell) * S - 1], fill=OUT)
    d.text((w // 2 * S, 330 * S), "MENÚ DIGITAL", font=_f("black", 34), fill=TEAL, anchor="mm")
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=4)
def club_card():
    w, h = 820, 400
    im, d = ov.card_base(w, h)
    d.rounded_rectangle([5 * S, 5 * S, (w - 5) * S, 100 * S], radius=34 * S, fill=TEAL)
    d.rectangle([5 * S, 60 * S, (w - 5) * S, 100 * S], fill=TEAL)
    d.line([(5 * S, 100 * S), ((w - 5) * S, 100 * S)], fill=OUT, width=6 * S)
    d.text((w // 2 * S, 54 * S), "HUELLITAS CLUB", font=_f("black", 48), fill=(255, 255, 255), anchor="mm")
    im = ov.ss_done(im, w, h)
    face = dog("happy", 0, False, 0.62 / K)
    face = face.crop((0, 0, face.width, int(face.height * 0.62)))
    im.paste(face, (40, 112), face)
    d = ImageDraw.Draw(im)
    for i, (k, v) in enumerate((("Mascota:", "Canela"), ("Raza:", "mestiza"), ("Cumple:", "12 de marzo"), ("Visitas:", "18"))):
        y = 150 + i * 60
        d.text((290, y), k, font=font("semi", 32), fill=(110, 116, 120), anchor="lm")
        d.text((440, y), v, font=font("black", 34), fill=INK, anchor="lm")
    return im


@functools.lru_cache(maxsize=4)
def coupon_card():
    w, h = 560, 170
    im, d = ov.card_base(w, h, fill=(255, 236, 150), radius=24)
    for x in range(40, w - 30, 30):
        d.line([(x * S, 24 * S), ((x + 14) * S, 24 * S)], fill=CORAL, width=4 * S)
        d.line([(x * S, (h - 24) * S), ((x + 14) * S, (h - 24) * S)], fill=CORAL, width=4 * S)
    d.text((w // 2 * S, 66 * S), "CUPÓN DE CUMPLEAÑOS", font=_f("black", 40), fill=INK, anchor="mm")
    d.text((w // 2 * S, 116 * S), "automático, cada año", font=_f("bold", 30), fill=CORAL, anchor="mm")
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=4)
def shield_card():
    w, h = 900, 330
    im, d = ov.card_base(w, h)
    pts = [(150, 50), (250, 86), (240, 200), (150, 280), (60, 200), (50, 86)]
    d.polygon([(x * S, y * S) for x, y in pts], fill=TEAL, outline=OUT, width=7 * S)
    d.rounded_rectangle([118 * S, 150 * S, 182 * S, 210 * S], radius=8 * S, fill=(255, 214, 64), outline=OUT, width=5 * S)
    d.arc([126 * S, 116 * S, 174 * S, 170 * S], 180, 360, fill=OUT, width=8 * S)
    d.text((300 * S, 110 * S), "LFPDPPP", font=_f("black", 72), fill=INK, anchor="lm")
    d.text((300 * S, 186 * S), "Ley Federal de Protección", font=_f("bold", 36), fill=INK, anchor="lm")
    d.text((300 * S, 232 * S), "de Datos Personales", font=_f("bold", 36), fill=INK, anchor="lm")
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=40)
def merma_card(level_q):
    """Medidor de merma: level_q 0..30 (décimas de %), marca en 3%."""
    w, h = 900, 300
    im, d = ov.card_base(w, h)
    d.text((60 * S, 70 * S), "MERMA", font=_f("black", 50), fill=INK, anchor="lm")
    d.text(((w - 60) * S, 70 * S), "< 3%", font=_f("black", 64), fill=GREEN, anchor="rm")
    x0, x1, y0, y1 = 60, w - 60, 140, 200
    d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=30 * S, fill=(236, 232, 226), outline=OUT, width=5 * S)
    # escala 0..10 %
    lim = x0 + (x1 - x0) * 0.3
    fill_x = x0 + (x1 - x0) * (level_q / 100)
    if level_q > 0:
        d.rounded_rectangle([(x0 + 6) * S, (y0 + 6) * S, max(x0 + 40, fill_x) * S, (y1 - 6) * S], radius=24 * S, fill=GREEN)
    d.line([(lim * S, (y0 - 16) * S), (lim * S, (y1 + 16) * S)], fill=CORAL, width=7 * S)
    d.text((lim * S, (y1 + 46) * S), "3%", font=_f("black", 34), fill=CORAL, anchor="mm")
    d.text((x0 * S, (y1 + 46) * S), "0%", font=_f("bold", 30), fill=(120, 120, 120), anchor="lm")
    d.text((x1 * S, (y1 + 46) * S), "10%", font=_f("bold", 30), fill=(120, 120, 120), anchor="rm")
    return ov.ss_done(im, w, h)


@functools.lru_cache(maxsize=8)
def name_tag(s, col):
    return ov.chip(s, col, size=44)
