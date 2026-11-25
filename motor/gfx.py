# Utilidades de dibujo: lienzo con supersampling, a Santi y personas genéricas.
import math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
K = 1.08            # el fondo se dibuja 8% más grande para mover la cámara sin perder nitidez
OUT = (22, 22, 28)  # color de contorno
OW = 5              # grosor de contorno en unidades de cuadro

FONT_DIR = "C:/Windows/Fonts/"
FONTS = {"black": "seguibl.ttf", "bold": "segoeuib.ttf", "semi": "seguisb.ttf", "reg": "segoeui.ttf"}


@functools.lru_cache(maxsize=512)
def font(name, size):
    return ImageFont.truetype(FONT_DIR + FONTS[name], max(4, int(round(size))))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


@functools.lru_cache(maxsize=64)
def radial_mask(px, alpha, power=2.0):
    """Máscara radial (L) de px x px, opaca al centro."""
    y, x = np.mgrid[0:px, 0:px].astype(np.float32)
    c = (px - 1) / 2.0
    d = np.sqrt((x - c) ** 2 + (y - c) ** 2) / max(c, 1)
    m = np.clip(1 - d, 0, 1) ** power * alpha * 255
    return Image.fromarray(m.astype(np.uint8), "L")


class Cv:
    """Lienzo en unidades de cuadro (1080x1920) con supersampling ss y escala k."""

    def __init__(self, w, h, ss=2, k=1.0, mode="RGB", bg=None):
        self.w, self.h, self.ss, self.k, self.mode = w, h, ss, k, mode
        self.f = ss * k
        if bg is None:
            bg = (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0)
        self.img = Image.new(mode, (int(round(w * self.f)), int(round(h * self.f))), bg)
        self.d = ImageDraw.Draw(self.img)

    # --- conversiones
    def P(self, pts):
        return [(x * self.f, y * self.f) for x, y in pts]

    def B(self, b):
        return [b[0] * self.f, b[1] * self.f, b[2] * self.f, b[3] * self.f]

    def px(self, v):
        return max(1, int(round(v * self.f)))

    # --- figuras con contorno
    def rect(self, b, fill=None, outline=OUT, w=OW, r=0):
        kw = dict(fill=fill)
        if outline is not None and w > 0:
            kw.update(outline=outline, width=self.px(w))
        if r:
            self.d.rounded_rectangle(self.B(b), radius=r * self.f, **kw)
        else:
            self.d.rectangle(self.B(b), **kw)

    def ell(self, b, fill=None, outline=OUT, w=OW):
        kw = dict(fill=fill)
        if outline is not None and w > 0:
            kw.update(outline=outline, width=self.px(w))
        self.d.ellipse(self.B(b), **kw)

    def circ(self, cx, cy, r, fill=None, outline=OUT, w=OW):
        self.ell((cx - r, cy - r, cx + r, cy + r), fill, outline, w)

    def poly(self, pts, fill=None, outline=OUT, w=OW):
        kw = dict(fill=fill)
        if outline is not None and w > 0:
            kw.update(outline=outline, width=self.px(w))
        self.d.polygon(self.P(pts), **kw)

    def line(self, pts, fill=OUT, w=OW):
        self.d.line(self.P(pts), fill=fill, width=self.px(w), joint="curve")

    def limb(self, pts, w, fill, outline=OUT, ow=OW):
        """Polilínea gruesa con puntas redondas y contorno (brazos, piernas, cejas)."""
        P = self.P(pts)
        layers = []
        if outline is not None:
            layers.append((outline, w + 2 * ow))
        layers.append((fill, w))
        for col, ww in layers:
            self.d.line(P, fill=col, width=self.px(ww), joint="curve")
            r = ww / 2 * self.f
            for (x, y) in (P[0], P[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def arc(self, b, a0, a1, fill=OUT, w=OW):
        self.d.arc(self.B(b), a0, a1, fill=fill, width=self.px(w))

    def chord(self, b, a0, a1, fill=None, outline=OUT, w=OW):
        kw = dict(fill=fill)
        if outline is not None:
            kw.update(outline=outline, width=self.px(w))
        self.d.chord(self.B(b), a0, a1, **kw)

    def pie(self, b, a0, a1, fill=None, outline=OUT, w=OW):
        kw = dict(fill=fill)
        if outline is not None:
            kw.update(outline=outline, width=self.px(w))
        self.d.pieslice(self.B(b), a0, a1, **kw)

    def text(self, xy, s, size, fill=(255, 255, 255), fname="black", anchor="mm", stroke=0, stroke_fill=OUT):
        self.d.text((xy[0] * self.f, xy[1] * self.f), s, font=font(fname, size * self.f), fill=fill,
                    anchor=anchor, stroke_width=int(round(stroke * self.f)), stroke_fill=stroke_fill)

    # --- rellenos
    def vgrad(self, b, stops):
        """Degradado vertical. stops = [(pos 0..1, color), ...]"""
        x0, y0, x1, y1 = [int(round(v)) for v in self.B(b)]
        h, w = max(1, y1 - y0), max(1, x1 - x0)
        t = np.linspace(0, 1, h)
        cols = []
        for ch in range(3):
            cols.append(np.interp(t, [s[0] for s in stops], [s[1][ch] for s in stops]))
        col = np.stack(cols, 1).astype(np.uint8)
        arr = np.repeat(col[:, None, :], w, axis=1)
        strip = Image.fromarray(arr, "RGB")
        if self.mode == "RGBA":
            strip = strip.convert("RGBA")
        self.img.paste(strip, (x0, y0))

    def glow(self, cx, cy, r, color, alpha=0.6, power=2.0):
        px = max(2, int(round(2 * r * self.f)))
        m = radial_mask(px, round(alpha, 3), power)
        x, y = int(round((cx - r) * self.f)), int(round((cy - r) * self.f))
        if self.mode == "RGBA":
            lay = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            lay.paste(Image.new("RGBA", (px, px), color + (255,)), (x, y), m)
            self.img = Image.alpha_composite(self.img, lay)
            self.d = ImageDraw.Draw(self.img)
        else:
            self.img.paste(Image.new("RGB", (px, px), color), (x, y), m)

    def layer(self):
        return Cv(self.w, self.h, self.ss, self.k, "RGBA")

    def comp(self, lay, opacity=1.0):
        im = lay.img
        if opacity < 1:
            a = im.getchannel("A").point(lambda v: int(v * opacity))
            im = im.copy()
            im.putalpha(a)
        if self.mode == "RGBA":
            self.img = Image.alpha_composite(self.img, im)
            self.d = ImageDraw.Draw(self.img)
        else:
            self.img.paste(im, (0, 0), im)

    def final(self):
        return self.img.resize((int(round(self.w * self.k)), int(round(self.h * self.k))), Image.LANCZOS)


# ---------------------------------------------------------------- Santi
SKIN = (201, 142, 99)
SKIN_D = (168, 110, 72)
HAIR = (30, 27, 27)
HOOD = (226, 168, 46)
HOOD_D = (186, 132, 28)
JEANS = (46, 64, 100)
PACK = (58, 138, 70)
PACK_D = (40, 104, 52)
SHOE = (243, 243, 238)
EYE_W = (255, 255, 255)
MOUTH = (110, 30, 40)

BROWS = {
    "neutral":    ([(118, 152), (150, 144), (182, 150)], [(218, 150), (250, 144), (282, 152)]),
    "curious":    ([(118, 136), (150, 126), (182, 134)], [(218, 150), (250, 145), (282, 152)]),
    "surprised":  ([(118, 132), (150, 120), (182, 130)], [(218, 130), (250, 120), (282, 132)]),
    "worried":    ([(116, 152), (150, 144), (182, 132)], [(218, 132), (250, 144), (284, 152)]),
    "determined": ([(118, 136), (150, 144), (184, 156)], [(216, 156), (250, 144), (282, 136)]),
    "suspicious": ([(118, 160), (150, 156), (182, 160)], [(218, 156), (250, 152), (282, 158)]),
    "happy":      ([(118, 142), (150, 132), (182, 140)], [(218, 140), (250, 132), (282, 142)]),
    "squish":     ([(120, 146), (182, 158)], [(218, 158), (280, 146)]),
}


def _hair_poly():
    cx, cy, r = 200, 190, 152
    pts = []
    n = 0
    for ang in range(190, 352, 9):
        rr = r + (18 if n % 2 == 0 else 3)
        a = math.radians(ang)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        n += 1
    # flequillo de derecha a izquierda, en picos
    xs = list(range(342, 56, -24))
    for i, x in enumerate(xs):
        base = 108 + 66 * ((x - 200) / 142) ** 2
        y = base + (20 if i % 2 else 0)
        pts.append((x, y))
    return pts


HAIR_POLY = _hair_poly()


def santi(expr="neutral", pose="stand", blink=False, look=(0.0, 0.0), scale=1.0, walk=0, glow=False, mouth=0):
    """Devuelve a Santi como RGBA de (400*scale) x (720*scale)."""
    c = Cv(400, 720, ss=2, k=scale, mode="RGBA")
    # mochila (detrás)
    c.rect((70, 345, 330, 548), fill=PACK_D, r=44)

    # piernas
    if pose in ("sit", "sit_phone"):
        c.ell((118, 520, 204, 600), fill=JEANS)
        c.ell((196, 520, 282, 600), fill=JEANS)
        c.rect((130, 566, 192, 660), fill=JEANS, r=18)
        c.rect((208, 566, 270, 660), fill=JEANS, r=18)
        c.ell((112, 640, 204, 694), fill=SHOE)
        c.ell((196, 640, 288, 694), fill=SHOE)
    else:
        dx = 0
        lift = 16 * abs(walk)
        c.rect((128 + dx, 535, 196 + dx, 660 - (lift if walk > 0 else 0)), fill=JEANS, r=18)
        c.rect((204 - dx, 535, 272 - dx, 660 - (lift if walk < 0 else 0)), fill=JEANS, r=18)
        c.ell((112 + dx, 640 - (lift if walk > 0 else 0), 204 + dx, 692 - (lift if walk > 0 else 0)), fill=SHOE)
        c.ell((196 - dx, 640 - (lift if walk < 0 else 0), 288 - dx, 692 - (lift if walk < 0 else 0)), fill=SHOE)
        c.line([(120 + dx, 678 - (lift if walk > 0 else 0)), (196 + dx, 678 - (lift if walk > 0 else 0))], fill=(180, 180, 176), w=4)
        c.line([(204 - dx, 678 - (lift if walk < 0 else 0)), (280 - dx, 678 - (lift if walk < 0 else 0))], fill=(180, 180, 176), w=4)

    # torso (sudadera)
    c.rect((80, 322, 320, 566), fill=HOOD, r=64)
    c.ell((118, 292, 282, 374), fill=HOOD_D)
    c.rect((134, 470, 266, 548), fill=None, outline=HOOD_D, w=4, r=24)
    c.line([(94, 548), (306, 548)], fill=HOOD_D, w=4)
    # cordones
    for x0, x1 in ((184, 180), (216, 220)):
        c.line([(x0, 358), (x1, 420)], fill=(245, 240, 228), w=5)
        c.circ(x1, 424, 6, fill=(245, 240, 228), w=2)
    # tirantes de la mochila
    c.rect((98, 330, 128, 474), fill=PACK, r=12)
    c.rect((272, 330, 302, 474), fill=PACK, r=12)
    # parche de globo
    c.circ(244, 440, 19, fill=(58, 143, 183), w=3)
    c.line([(225, 440), (263, 440)], fill=OUT, w=2)
    c.ell((236, 421, 252, 459), fill=None, w=2)

    # brazos
    if pose in ("stand", "walk", "sit"):
        sw = 6 * walk
        c.limb([(100, 362), (80 - sw, 448), (74 - sw, 518)], 52, HOOD)
        c.circ(74 - sw, 530, 25, fill=SKIN)
        c.limb([(300, 362), (320 + sw, 448), (326 + sw, 518)], 52, HOOD)
        c.circ(326 + sw, 530, 25, fill=SKIN)
    elif pose in ("phone_stand", "sit_phone"):
        c.limb([(100, 362), (80, 448), (74, 518)], 52, HOOD)
        c.circ(74, 530, 25, fill=SKIN)
        c.limb([(300, 362), (330, 446), (272, 474)], 52, HOOD)
        scr = (150, 215, 255) if glow else (90, 150, 200)
        c.rect((222, 380, 284, 478), fill=(28, 28, 36), r=10)
        c.rect((230, 390, 276, 466), fill=scr, outline=None, r=5)
        c.circ(256, 470, 25, fill=SKIN)
    elif pose == "gloves":
        GL = (214, 44, 44)
        c.limb([(100, 362), (64, 450), (128, 420)], 52, HOOD)
        c.limb([(300, 362), (336, 450), (272, 420)], 52, HOOD)
        c.circ(132, 404, 44, fill=GL)
        c.circ(268, 404, 44, fill=GL)
        c.arc((104, 380, 150, 420), 150, 300, fill=(160, 25, 25), w=4)
        c.arc((250, 380, 296, 420), 240, 30, fill=(160, 25, 25), w=4)
    elif pose == "shake":
        c.limb([(100, 362), (110, 450), (160, 440)], 52, HOOD)
        c.limb([(300, 362), (290, 450), (240, 440)], 52, HOOD)
        c.circ(162, 440, 25, fill=SKIN)
        c.circ(238, 440, 25, fill=SKIN)

    # cabeza
    c.circ(52, 208, 28, fill=SKIN)
    c.circ(348, 208, 28, fill=SKIN)
    c.arc((40, 194, 64, 222), 100, 260, fill=SKIN_D, w=4)
    c.arc((336, 194, 360, 222), 280, 80, fill=SKIN_D, w=4)
    c.circ(200, 190, 152, fill=SKIN, w=6)
    c.poly(HAIR_POLY, fill=HAIR, w=5)

    # mejillas
    c.ell((104, 244, 140, 266), fill=(214, 130, 100), outline=None)
    c.ell((260, 244, 296, 266), fill=(214, 130, 100), outline=None)

    # cejas
    lb, rb = BROWS.get(expr, BROWS["neutral"])
    c.limb(lb, 11, HAIR, outline=None)
    c.limb(rb, 11, HAIR, outline=None)

    # ojos
    lx, ly = look
    for ex in (150, 250):
        box = (ex - 34, 166, ex + 34, 250)
        if blink:
            c.line([(ex - 30, 210), (ex, 220), (ex + 30, 210)], fill=OUT, w=6)
        elif expr == "squish":
            if ex == 150:
                c.line([(ex - 24, 194), (ex + 18, 210), (ex - 24, 226)], fill=OUT, w=7)
            else:
                c.line([(ex + 24, 194), (ex - 18, 210), (ex + 24, 226)], fill=OUT, w=7)
        elif expr == "suspicious":
            c.chord(box, 0, 180, fill=EYE_W, w=5)
            px, py = ex + lx * 12, 214 + max(0, ly) * 10
            c.chord((px - 15, py - 15, px + 15, py + 15), 0, 180, fill=OUT, outline=None)
            c.line([(ex - 34, 208), (ex + 34, 208)], fill=OUT, w=6)
        else:
            c.ell(box, fill=EYE_W, w=5)
            pr = 13 if expr == "surprised" else 16
            px, py = ex + lx * 12, 212 + ly * 16
            c.circ(px, py, pr, fill=OUT, outline=None)
            c.circ(px - 5, py - 6, 5, fill=(255, 255, 255), outline=None)

    # nariz
    c.line([(198, 236), (192, 256), (206, 260)], fill=SKIN_D, w=5)

    # boca
    if mouth:  # hablando: boca abierta (1 chica, 2 grande)
        if mouth == 1:
            c.chord((178, 270, 222, 306), 0, 180, fill=MOUTH, w=5)
        else:
            c.chord((170, 264, 230, 322), 0, 180, fill=MOUTH, w=5)
            c.chord((184, 300, 216, 320), 200, 340, fill=(230, 110, 120), outline=None)
    elif expr in ("neutral", "curious"):
        c.arc((174, 262, 226, 300), 25, 155, fill=OUT, w=6)
    elif expr == "happy":
        c.chord((160, 262, 240, 326), 0, 180, fill=MOUTH, w=5)
        c.chord((178, 304, 222, 336), 200, 340, fill=(230, 110, 120), outline=None)
        c.rect((176, 296, 224, 304), fill=(255, 255, 255), outline=None)
    elif expr == "surprised":
        c.ell((184, 274, 216, 318), fill=MOUTH, w=5)
    elif expr == "worried":
        c.line([(170, 298), (185, 290), (200, 298), (215, 290), (230, 298)], fill=OUT, w=6)
    elif expr == "determined":
        c.line([(168, 292), (200, 290), (232, 278)], fill=OUT, w=6)
    elif expr == "suspicious":
        c.line([(178, 294), (222, 292)], fill=OUT, w=6)
    elif expr == "squish":
        c.line([(180, 296), (190, 288), (200, 298), (210, 288), (220, 296)], fill=OUT, w=6)
    return c.final()


# ---------------------------------------------------------------- personas genéricas
SKINS = [(232, 190, 160), (201, 142, 99), (160, 105, 70), (120, 78, 52), (222, 170, 130), (98, 64, 45)]


def person(skin=(222, 170, 130), shirt=(80, 120, 170), pants=(50, 52, 64), hair=(35, 28, 26), style="short",
           scale=1.0, old=False, glasses=False, expr="smile", look=(0, 0), arms="down", sil=None, kid=False):
    """Persona sencilla (240x480 unidades). sil=color -> silueta plana sin cara."""
    c = Cv(240, 480, ss=2, k=scale, mode="RGBA")
    o = OUT if sil is None else sil
    S = (lambda col: col if sil is None else sil)
    w = OW
    if style == "long":
        c.rect((52, 60, 188, 250), fill=S(hair), outline=o, w=w, r=50)
    # piernas y zapatos
    c.rect((72, 312, 116, 440), fill=S(pants), outline=o, w=w, r=14)
    c.rect((124, 312, 168, 440), fill=S(pants), outline=o, w=w, r=14)
    c.ell((60, 426, 120, 462), fill=S((40, 40, 44)), outline=o, w=w)
    c.ell((120, 426, 180, 462), fill=S((40, 40, 44)), outline=o, w=w)
    # torso
    c.rect((58, 158, 182, 330), fill=S(shirt), outline=o, w=w, r=42)
    # brazos
    if arms == "down":
        c.limb([(68, 180), (52, 250), (50, 300)], 34, S(shirt), outline=o)
        c.circ(50, 308, 16, fill=S(skin), outline=o)
        c.limb([(172, 180), (188, 250), (190, 300)], 34, S(shirt), outline=o)
        c.circ(190, 308, 16, fill=S(skin), outline=o)
    elif arms == "wave":
        c.limb([(68, 180), (52, 250), (50, 300)], 34, S(shirt), outline=o)
        c.circ(50, 308, 16, fill=S(skin), outline=o)
        c.limb([(172, 180), (206, 130), (214, 70)], 34, S(shirt), outline=o)
        c.circ(214, 60, 17, fill=S(skin), outline=o)
    elif arms == "hold":  # brazos al frente (sostener algo)
        c.limb([(68, 180), (60, 250), (100, 262)], 34, S(shirt), outline=o)
        c.limb([(172, 180), (180, 250), (140, 262)], 34, S(shirt), outline=o)
        c.circ(104, 262, 16, fill=S(skin), outline=o)
        c.circ(136, 262, 16, fill=S(skin), outline=o)
    # cuello y cabeza
    c.circ(120, 96, 72, fill=S(skin), outline=o, w=w)
    if sil is not None:
        if style == "hat":
            c.rect((40, 40, 200, 58), fill=sil, outline=sil, r=8)
            c.rect((66, 0, 174, 48), fill=sil, outline=sil, r=14)
        if style == "hood":
            c.ell((40, 14, 200, 186), fill=sil, outline=sil)
        return c.final()
    # cabello
    if style in ("short", "long", "bun"):
        pts = []
        for ang in range(196, 346, 10):
            a = math.radians(ang)
            pts.append((120 + 78 * math.cos(a), 96 + 78 * math.sin(a)))
        for i, x in enumerate(range(186, 50, -17)):
            pts.append((x, 58 + 30 * ((x - 120) / 70) ** 2 + (12 if i % 2 else 0)))
        c.poly(pts, fill=hair, w=w)
    if style == "bun":
        c.circ(120, 26, 28, fill=hair, w=w)
    if style == "bald":
        c.ell((48, 70, 72, 120), fill=hair, outline=None)
        c.ell((168, 70, 192, 120), fill=hair, outline=None)
    if style == "cap":
        c.chord((46, 18, 194, 140), 180, 360, fill=(200, 60, 60), w=w)
        c.rect((110, 64, 214, 80), fill=(200, 60, 60), r=8)
    # cara
    lx, ly = look
    for ex in (96, 144):
        c.ell((ex - 8 + lx * 5, 88 + ly * 5, ex + 8 + lx * 5, 108 + ly * 5), fill=OUT, outline=None)
    if glasses:
        c.circ(96, 98, 19, fill=None, w=4)
        c.circ(144, 98, 19, fill=None, w=4)
        c.line([(115, 98), (125, 98)], w=4)
    if old:
        c.line([(70, 92), (78, 96)], fill=(150, 100, 80), w=3)
        c.line([(162, 96), (170, 92)], fill=(150, 100, 80), w=3)
        c.line([(100, 72), (140, 72)], fill=(150, 100, 80), w=3)
    if expr == "smile":
        c.arc((98, 106, 142, 140), 20, 160, w=5)
    elif expr == "laugh":
        c.chord((96, 112, 144, 146), 0, 180, fill=MOUTH, w=4)
    elif expr == "flat":
        c.line([(104, 128), (136, 128)], w=5)
    elif expr == "angry":
        c.line([(104, 132), (120, 126), (136, 132)], w=5)
        c.line([(80, 78), (106, 86)], w=6)
        c.line([(134, 86), (160, 78)], w=6)
    return c.final()


def blink_at(t, seed=0, period=3.3):
    """True durante ~0.12 s cada 'period' segundos, desfasado por seed."""
    ph = (t + seed * 1.37) % period
    return ph < 0.12


def tint(img, color, amount):
    """Mezcla un RGBA hacia un color (para luz nocturna o atardecer), respetando alfa."""
    if amount <= 0:
        return img
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    over = Image.new("RGB", img.size, color)
    rgb = Image.blend(rgb, over, amount)
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def darken(img, f):
    """Oscurece un RGBA multiplicando RGB por f."""
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b)).point(lambda v: int(v * f))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out
