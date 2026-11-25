# Tomas del reel de Huellitas: fondo fijo (build), animación (animate) y textos de la escena (overlay).
import math, random, functools
from PIL import Image, ImageDraw
from gfx import *
import overlays as ov
from props import *


# ------------------------------------------------------------------ utilidades
def put(img, spr, x, y, anchor="bottom"):
    X, Y = x * K, y * K
    w, h = spr.size
    if anchor == "bottom":
        pos = (int(X - w / 2), int(Y - h))
    else:
        pos = (int(X - w / 2), int(Y - h / 2))
    img.paste(spr, pos, spr)


def lay_final(cv):
    im = cv.final()
    bb = im.getbbox() or (0, 0, 1, 1)
    return im.crop(bb), (bb[0], bb[1])


def put_layer(img, L, dx=0, dy=0):
    lim, (x, y) = L
    img.paste(lim, (int(x + dx), int(y + dy)), lim)


def bob(T, amp=3.0, f=2.2, ph=0.0):
    return math.sin(T * f + ph) * amp


@functools.lru_cache(maxsize=600)
def SANTI(expr="neutral", pose="stand", blink=False, look=(0.0, 0.0), scale=1.0, walk=0, glow=False, mouth=0):
    return santi(expr, pose, blink, look, scale * K, walk, glow, mouth)


@functools.lru_cache(maxsize=200)
def PERSON(scale=1.0, **kw):
    return person(scale=scale * K, **kw)


def alpha_mul(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im


_WC = {}


def talk(ctx, pid, T):
    """Nivel de boca (0, 1, 2) según si la voz está diciendo una palabra."""
    L = _WC.get(pid)
    if L is None:
        L = _WC[pid] = [(w["s"], w["e"]) for w in ctx.tl["words"] if w["part"] == pid]
    for s, e in L:
        if s <= T < e:
            return (2, 1, 2, 0)[int((T - s) * 12) % 4]
        if s > T:
            break
    return 0


def sched(T, pairs, default):
    v = default
    for t, val in pairs:
        if T >= t:
            v = val
    return v


def santi_at(img, x, feet, scale, expr, pose, T, look=(0.0, 0.0), seed=0, ctx=None, pid=None):
    """Reyes (el protagonista). Si se pasa ctx y pid, mueve la boca con la voz de esa parte."""
    m = talk(ctx, pid, T) if ctx is not None else 0
    put(img, SANTI(expr, pose, blink_at(T, seed), look, scale, mouth=m), x, feet + 26 * scale + bob(T, 2, 2.0, seed))


def extra(img, who, T, x, feet, scale=1.25, arms="down", mirror=False, hat=False, look=(0.0, 0.0), seed=0):
    """Integrante del equipo que no habla (sin nombre)."""
    put(img, staff(who, 0, blink_at(T, seed + 5), arms, scale, look, hat, mirror), x, feet + 30 * scale + bob(T, 2, 1.8, seed))


REYES_TAG = (214, 150, 40)


def dog_at(img, x, feet, scale, T, expr="happy", wag=True, hat=None, look=(0.0, 0.0), col=DOG_C, mirror=False, hop=0.0, seed=0):
    tail = int(round(2 * math.sin(T * 13 + seed))) if wag else 0
    put(img, dog(expr, tail, blink_at(T, seed + 3), scale, hat, look, col, mirror), x, feet + 6 * scale - hop + bob(T, 1.5, 2.6, seed))


def speaker(img, ctx, who, pid, T, x, feet, scale=1.25, arms="down", mirror=False, hat=False, look=(0.0, 0.0), seed=0):
    m = talk(ctx, pid, T)
    spr = staff(who, m, blink_at(T, seed + 5), arms, scale, look, hat, mirror)
    put(img, spr, x, feet + 30 * scale + bob(T, 2, 1.8, seed))


def leash(img, p0, p1, sag=40):
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(21):
        t = i / 20
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t + sag * 4 * t * (1 - t)
        pts.append((x * K, y * K))
    d.line(pts, fill=OUT, width=int(12 * K), joint="curve")
    d.line(pts, fill=(222, 72, 84), width=int(6 * K), joint="curve")


@functools.lru_cache(maxsize=4)
def door_sign(kind):
    c = Cv(240, 270, 2, K, "RGBA")
    c.line([(70, 70), (120, 16), (170, 70)], w=4)
    c.circ(120, 16, 8, fill=(200, 200, 200))
    if kind == "open":
        c.rect((20, 66, 220, 166), fill=GREEN, r=18)
        c.text((120, 116), "ABIERTO", 38)
    else:
        c.circ(120, 160, 92, fill=(255, 255, 255), outline=OUT, w=6)
        c.circ(120, 160, 80, fill=None, outline=CORAL, w=18)
        paw(c, 120, 172, 30, OUT)
        c.line([(66, 106), (174, 214)], fill=CORAL, w=18)
    return c.final()


def swing(im, age, amp=14):
    a = amp * math.exp(-age * 2.5) * math.sin(age * 11)
    if abs(a) < 0.3:
        return im
    return im.rotate(a, resample=Image.BICUBIC, center=(im.width / 2, 16 * K))


@functools.lru_cache(maxsize=4)
def mini_store():
    c = Cv(220, 210, 2, 1, "RGBA")
    c.rect((20, 60, 200, 200), fill=CREAM)
    for i, x in enumerate(range(10, 210, 40)):
        c.rect((x, 40, x + 40, 84), fill=SAGE if i % 2 else (250, 246, 236), w=4)
    c.rect((84, 120, 136, 200), fill=(255, 214, 150))
    c.rect((32, 110, 72, 160), fill=(170, 210, 230))
    c.rect((148, 110, 188, 160), fill=(170, 210, 230))
    paw(c, 110, 22, 10, COFFEE)
    return c.final()


@functools.lru_cache(maxsize=8)
def cake(q):
    c = Cv(200, 220, 2, K, "RGBA")
    c.ell((10, 180, 190, 214), fill=(240, 240, 250))
    c.rect((36, 120, 164, 196), fill=(250, 200, 210), r=14)
    c.rect((60, 70, 140, 126), fill=(255, 246, 230), r=12)
    for x in (52, 84, 116, 148):
        c.circ(x, 122, 10, fill=(255, 246, 230), outline=None)
    paw(c, 100, 162, 13, (220, 110, 130))
    c.rect((94, 30, 106, 72), fill=(120, 180, 240), w=3)
    fl = (1.0, 0.85, 1.1, 0.95)[q]
    c.glow(100, 18, 30, (255, 220, 120), 0.6)
    c.ell((92, 26 - 20 * fl, 108, 30), fill=(255, 190, 60), w=3)
    return c.final()


@functools.lru_cache(maxsize=8)
def heart(scale, col=CORAL):
    c = Cv(100, 92, 2, scale * K, "RGBA")
    c.circ(30, 30, 26, fill=col, outline=None)
    c.circ(70, 30, 26, fill=col, outline=None)
    c.poly([(7, 40), (93, 40), (50, 88)], fill=col, outline=None)
    c.circ(28, 24, 7, fill=(255, 220, 220), outline=None)
    return c.final()


def hearts(img, T, t0, spots, scale=0.5):
    if T < t0:
        return
    for i, (x, y) in enumerate(spots):
        age = (T - t0 - i * 0.4) % 2.4
        if T - t0 < i * 0.4:
            continue
        a = clamp(age / 0.3) * (1 - clamp((age - 1.6) / 0.8))
        put(img, alpha_mul(heart(scale), a), x + 12 * math.sin(age * 3 + i), y - age * 120, "center")


def chips_seq(fr, T, items, t_off=None):
    """items: [(t_on, img, x, y)] → los muestra con pop hasta t_off."""
    for t_on, im, x, y in items:
        ov.show(fr, im, x, y, T, t_on, t_off)


def S_(lines, size=60, col=ov.WHITE):
    lines = tuple(lines)
    longest = max(lines, key=len)
    size = ov.fit_size(longest, size, 1000, "black", 10)
    return ov.stack_text(lines, size, col)


# ------------------------------------------------------------------ clase base
class Shot:
    label = ""
    focus = (540, 1100)
    push = 0.05
    shake = 0
    caption_y = 1470

    def __init__(self, ctx, info):
        self.ctx, self.info = ctx, info
        self.t0, self.t1 = info["t0"], info["t1"]
        self.base = None

    def get_base(self):
        if self.base is None:
            self.base = self.build()
        return self.base

    def build(self):
        raise NotImplementedError

    def animate(self, img, tl, T):
        pass

    def overlay(self, fr, tl, T):
        pass


# ------------------------------------------------------------------ 1 · Condesa (café que no deja pasar)
class S1(Shot):
    label = "Condesa, CDMX"
    focus = (540, 1200)
    push = 0.06

    def build(self):
        c = Cv(W, H, 2, K)
        draw_street(c)
        storefront_plain(c)
        tree(c, 20, 470, 170)
        tree(c, 1070, 500, 160)
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        tm, tp = w("s1", "mascotas"), w("s1", "perro")
        if T < tm:
            put(img, door_sign("open"), 755, 960, "center")
        else:
            put(img, swing(door_sign("no"), T - tm), 755, 980, "center")
        expr = sched(T, [(w("s1", "pero"), "curious"), (tm, "worried")], "happy")
        look = (0.7, 0.3) if tp <= T < tm else ((0.6, -0.4) if T >= tm else (0.0, 0.0))
        leash(img, (420, 1612), (690, 1606), 46)
        santi_at(img, 330, 1730, 0.78, expr, "stand", T, look, ctx=self.ctx, pid="s1")
        sad = T >= tm
        dog_at(img, 690, 1730, 0.8, T, "sad" if sad else "happy", not sad, look=(-0.5, -0.3) if sad else (0.0, 0.0))

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tm = w("s1", "mascotas")
        ov.show(fr, S_(("¿UN CAFÉ", "CON MI PERRO?"), 66), 540, 640, T, w("s1", "Quiero"), tm)
        ov.show(fr, name_tag("REYES", REYES_TAG), 330, 1110, T, self.t0 + 0.3)
        ov.show(fr, ov.chip("MASCOTAS NO", CORAL, size=72), 540, 640, T, tm, start_scale=1.6)


# ------------------------------------------------------------------ 2 · Zamora 165 (fachada Huellitas)
class S2(Shot):
    label = "Zamora 165"
    focus = (540, 1180)
    push = 0.06

    def build(self):
        c = Cv(W, H, 2, K)
        draw_street(c)
        storefront_huellitas(c)
        tree(c, 10, 470, 150)
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        butterflies(img, T, [(240, 980), (880, 940), (520, 1120), (980, 1260)], 0.55)
        tc = w("s2", "convives")
        hop = abs(math.sin((T - tc) * 7)) * 50 if tc <= T < tc + 1.4 else 0
        leash(img, (400, 1612), (690, 1606 - hop), 40)
        santi_at(img, 310, 1730, 0.78, sched(T, [(w("s2", "Huellitas"), "happy")], "surprised"), "stand", T, (0.4, -0.2), ctx=self.ctx, pid="s2")
        dog_at(img, 690, 1730, 0.8, T, "happy", True, hop=hop, look=(-0.4, -0.2))

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tp = w("s2", "pet")
        ov.show(fr, ov.logo_card(560), 540, 760, T, w("s2", "Huellitas"), tp)
        chips_seq(fr, T, [(tp, S_(("CAFÉ PET FRIENDLY",), 70, ov.YELLOW), 540, 590),
                          (w("s2", "entras"), ov.chip("ENTRAS CON TU MASCOTA", TEAL, size=46), 540, 700),
                          (w("s2", "convives"), ov.chip("Y CONVIVES CON ELLA", CORAL, size=46), 540, 800)])
        ov.show(fr, ov.chip("ZAMORA 165 · CONDESA", INK, size=44), 540, 1060, T, w("s2", "Zamora"))


# ------------------------------------------------------------------ 3 · Tu mesa (la app)
class S3(Shot):
    label = "Tu mesa"
    focus = (520, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c)
        chair_back(c, 300, 1631)
        round_table(c, 650, 1520, 260)
        c.rect((610, 1438, 680, 1500), fill=(255, 255, 255), r=10)
        c.ell((612, 1430, 678, 1450), fill=(200, 150, 100))
        c.arc((668, 1450, 704, 1486), 270, 90, w=5)
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        done = T >= w("s3", "listo")
        santi_at(img, 300, 1730, 0.8, "happy" if done else "curious", "sit_phone", T, (0.2, 0.6), ctx=self.ctx, pid="s3")
        dog_at(img, 890, 1745, 0.68, T, "happy", True, look=(-0.6, 0.0), seed=1)
        d = ImageDraw.Draw(img)
        d.ellipse([820 * K, 1736 * K, 960 * K, 1780 * K], fill=(90, 150, 210), outline=OUT, width=int(5 * K))
        d.ellipse([836 * K, 1740 * K, 944 * K, 1760 * K], fill=(170, 220, 250))

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ta = w("s3", "app")
        if T < ta:
            return
        n = sum(T >= w("s3", k) for k in ("aparto", "menú", "pido", "pago", "sigo"))
        listo = T >= w("s3", "listo")
        ov.paste_pop(fr, phone_card(n, listo), 540, 800, T - ta)


# ------------------------------------------------------------------ 4a · El mostrador (Jaqueline)
class S4a(Shot):
    label = "El mostrador"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c)
        self.counter = counter_layer(("espresso", "case", "cups"))
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        arms = sched(T, [(w("s4", "Para"), "open"), (w("s4", "arquitectura"), "point")], "wave")
        speaker(img, self.ctx, "jaqueline", "s4", T, 470, 1800, 1.45, arms)
        put_layer(img, self.counter, dy=130 * K)
        put(img, cat(blink_at(T, 4), 0.55, tail=int(2 * math.sin(T * 2))), 680, 1534)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ta = w("s4", "arquitectura")
        ov.show(fr, S_(("VIABILIDAD COMERCIAL", "Y OPERATIVA"), 60), 540, 620, T, w("s4", "viabilidad"), ta)
        ov.show(fr, blueprint_card(), 540, 770, T, ta)
        ov.show(fr, name_tag("JAQUELINE", ROSE), 470, 1380, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 4b · La fila (espera de 10 a 5 min)
QUEUE = [(90, dict(skin=SKINS[0], shirt=(120, 160, 200), hair=(60, 40, 30), style="long"), (200, 200, 205)),
         (225, dict(skin=SKINS[2], shirt=(90, 170, 120), hair=(30, 25, 22), style="cap"), DOG_C),
         (360, dict(skin=SKINS[4], shirt=(200, 120, 170), hair=(40, 30, 30), style="bun"), (90, 80, 76)),
         (495, dict(skin=SKINS[1], shirt=(230, 180, 60), hair=(25, 25, 25), style="short"), (240, 236, 228))]


class S4b(Shot):
    label = "La fila"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c, frames=False)
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        t5 = w("s4", "cinco")
        for i, (x, kw, pcol) in enumerate(QUEUE):
            gone = i < 2 and T >= t5
            age = T - t5 if gone else 0
            a = 1 - clamp(age / 0.7)
            if a <= 0:
                continue
            dx = -200 * clamp(age / 0.7) ** 2
            expr = "laugh" if T >= t5 else "flat"
            spr = PERSON(1.05, expr=expr, **kw)
            put(img, alpha_mul(spr, a), x + dx, 1700 + 18 * 1.05 + bob(T, 2, 2.0, i))
            if i == 0 or i == 3:
                im = cat(blink_at(T, i), 0.4, pcol)
            else:
                im = dog("happy" if T >= t5 else "neutral", 0, blink_at(T, i), 0.42, None, (0.6, 0.0), pcol)
            put(img, alpha_mul(im, a), x + 70 + dx, 1752)
        arms = sched(T, [(w("s4", "reducir"), "point"), (w("s4", "escalar"), "open"), (w("s4", "Cómo"), "down")], "open")
        speaker(img, self.ctx, "jaqueline", "s4", T, 830, 1760, 1.25, arms, mirror=True, look=(-0.5, -0.3))

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tr, t10, t5, te, tc, tq = (w("s4", k) for k in ("reducir", "diez", "cinco", "escalar", "cumplir", "Cómo"))
        st = ov.shown(T, tr, te)
        if st:
            if T < t10:
                q, lab = int(10 * clamp((T - tr) / max(0.1, t10 - tr))), "10"
            elif T < t5:
                q, lab = 10, "10"
            else:
                q, lab = 10 - int(round(5 * clamp((T - t5) / 0.6))), "5"
            ov.paste_pop(fr, clock_card(q, lab), 540, 720, st[0], fade_out_age=st[1])
        ov.show(fr, S_(("ESCALAR EL MODELO",), 64), 540, 600, T, te, tc)
        for i, x in enumerate((300, 540, 780)):
            ov.show(fr, mini_store(), x, 790, T, te + 0.35 + i * 0.25, tc)
        ov.show(fr, ov.chip("NORMATIVAS INTERNACIONALES", TEAL, size=44), 540, 620, T, tc, tq)
        ov.show(fr, ov.chip("PROTECCIÓN DE DATOS", GREEN, size=52), 540, 730, T, w("s4", "protección"), tq)
        ov.show(fr, S_(("¿CÓMO SE INTEGRA EN", "EL PUNTO DE VENTA?"), 62, ov.YELLOW), 540, 700, T, tq)
        ov.show(fr, name_tag("JAQUELINE", ROSE), 830, 1350, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 5a · El kiosco (Daniela)
class S5a(Shot):
    label = "El kiosco"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c, window=False)
        c.ell((690, 1700, 890, 1744), fill=(70, 74, 84))
        c.rect((760, 1300, 820, 1720), fill=(90, 96, 108))
        c.rect((640, 990, 940, 1330), fill=(60, 64, 76), r=24)
        c.rect((662, 1012, 918, 1250), fill=(232, 248, 244), r=12)
        c.rect((662, 1012, 918, 1066), fill=SAGE, r=12)
        c.text((790, 1040), "PIDE AQUÍ", 34)
        rng = random.Random(2)
        for i in range(9):
            for j in range(9):
                if rng.random() < 0.5 or (i < 3 and j < 3) or (i < 3 and j > 5) or (i > 5 and j < 3):
                    c.rect((736 + j * 12, 1090 + i * 12, 748 + j * 12, 1102 + i * 12), fill=OUT, outline=None)
        c.text((790, 1220), "menú · alérgenos", 22, fill=INK, fname="bold")
        c.rect((730, 1270, 850, 1300), fill=(40, 40, 46), r=6)
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        arms = sched(T, [(w("s5", "Implementamos"), "point")], "wave")
        speaker(img, self.ctx, "daniela", "s5", T, 320, 1740, 1.25, arms, look=(0.5, -0.2))
        dog_at(img, 975, 1760, 0.55, T, "happy", True, look=(-0.8, -0.6), seed=2)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ov.show(fr, S_(("ECOSISTEMA DIGITAL",), 66), 540, 580, T, w("s5", "ecosistema"))
        ov.show(fr, ov.chip("PLATAFORMA WEB", TEAL, size=44), 290, 670, T, w("s5", "plataforma"))
        ov.show(fr, ov.chip("KIOSCOS", CORAL, size=44), 800, 670, T, w("s5", "kioscos"))
        ov.show(fr, qr_card(), 540, 900, T, w("s5", "QR"))
        ov.show(fr, name_tag("DANIELA", (90, 140, 200)), 320, 1350, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 5r · Tu mesa (experiencia del cliente)
class S5r(Shot):
    label = "Tu mesa"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c)
        chair_back(c, 230, 1631)
        round_table(c, 500, 1530, 230)
        c.rect((470, 1450, 530, 1508), fill=(255, 255, 255), r=10)
        c.ell((472, 1442, 528, 1460), fill=(200, 150, 100))
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        santi_at(img, 230, 1730, 0.78, sched(T, [(w("s5", "consultar"), "curious"), (w("s5", "realizar"), "happy")], "happy"), "sit_phone", T, (0.3, 0.5))
        speaker(img, self.ctx, "daniela", "s5", T, 840, 1760, 1.2, "hold", mirror=True, look=(-0.6, 0.2), seed=1)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ov.show(fr, S_(("OPTIMIZA LA EXPERIENCIA",), 62), 540, 580, T, w("s5", "optimiza"))
        chips_seq(fr, T, [(w("s5", "reservar"), ov.chip("RESERVAR MESAS", TEAL, size=48), 540, 690),
                          (w("s5", "consultar"), ov.chip("CONSULTAR ALÉRGENOS", CORAL, size=48), 540, 790),
                          (w("s5", "realizar"), ov.chip("PEDIDOS SIN FRICCIONES", GREEN, size=48), 540, 890)])
        ov.show(fr, name_tag("DANIELA", (90, 140, 200)), 840, 1350, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 5b · Huellitas Club (CRM)
class S5b(Shot):
    label = "Huellitas Club"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c, window=False, wall=((250, 228, 232), (240, 206, 214)))
        rng = random.Random(3)
        for i in range(7):
            x, y = 600 + (i % 4) * 120 + rng.uniform(-10, 10), 1110 + (i // 4) * 150
            c.rect((x, y, x + 100, y + 116), fill=(255, 255, 255), w=4)
            c.rect((x + 10, y + 10, x + 90, y + 86), fill=rng.choice([(246, 210, 160), (200, 220, 246), (210, 240, 210)]), outline=None)
            paw(c, x + 50, y + 56, 13, rng.choice([COFFEE, (90, 90, 100), DOG_D]))
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        tb = w("s5", "cumpleaños")
        speaker(img, self.ctx, "daniela", "s5", T, 290, 1740, 1.25, "hold", look=(0.3, 0.3), seed=2)
        party = T >= tb
        dog_at(img, 830, 1750, 0.85, T, "happy", True, "party" if party else None, look=(-0.6, 0.2) if party else (0.0, 0.0), hop=abs(math.sin((T - tb) * 7)) * 40 if tb <= T < tb + 1.2 else 0)
        if party:
            put(img, cake(int(T * 10) % 4), 600, 1770)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ov.show(fr, ov.chip("SISTEMA CRM", CORAL, size=50), 540, 560, T, w("s5", "sistema"))
        ov.show(fr, club_card(), 540, 790, T, w("s5", "Huellitas"))
        ov.show(fr, coupon_card(), 720, 1070, T, w("s5", "cupones"))
        ov.show(fr, name_tag("DANIELA", (90, 140, 200)), 290, 1350, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 5c · Negocios internacionales
class S5c(Shot):
    label = "Negocios Internacionales"
    focus = (540, 1250)
    push = 0.06

    def build(self):
        c = Cv(W, H, 2, K)
        c.vgrad((0, 0, 1080, 1920), [(0, (18, 34, 70)), (1, (40, 84, 130))])
        rng = random.Random(8)
        for _ in range(70):
            x, y = rng.uniform(0, 1080), rng.uniform(0, 1500)
            c.circ(x, y, rng.uniform(1.5, 3.5), fill=(230, 236, 255), outline=None)
        gx, gy, r = 640, 1260, 400
        c.glow(gx, gy, r + 80, (120, 200, 255), 0.35)
        c.circ(gx, gy, r, fill=(70, 140, 210), w=7)
        for (x, y, a, b) in ((-150, -180, 150, 110), (100, -60, 120, 160), (-220, 90, 100, 140), (210, 170, 110, 90), (-30, 230, 90, 60)):
            c.ell((gx + x - a, gy + y - b, gx + x + a, gy + y + b), fill=(110, 190, 110), outline=None)
        for k in (-2, -1, 0, 1, 2):
            c.arc((gx - r * abs(math.cos(k * 0.6)) if k else gx - 4, gy - r, gx + r * abs(math.cos(k * 0.6)) if k else gx + 4, gy + r), 0, 360, fill=(140, 200, 240), w=3)
        for k in (-2, -1, 1, 2):
            yy = gy + k * r * 0.38
            hw = math.sqrt(max(0, r * r - (yy - gy) ** 2))
            c.line([(gx - hw, yy), (gx + hw, yy)], fill=(140, 200, 240), w=3)
        c.circ(gx, gy, r, fill=None, w=7)
        c.rect((-10, 1700, 1090, 1930), fill=(30, 56, 90))
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        gx, gy = 640, 1260
        pins = [(470, 1080), (760, 1210), (560, 1380), (850, 1420)]
        d = ImageDraw.Draw(img)
        prog = clamp((T - self.t0) / 2.5)
        for (a, b) in ((0, 1), (1, 3), (0, 2), (2, 3)):
            (x0, y0), (x1, y1) = pins[a], pins[b]
            pts = []
            for i in range(int(24 * prog) + 1):
                t = i / 24
                pts.append(((x0 + (x1 - x0) * t) * K, (y0 + (y1 - y0) * t - 120 * 4 * t * (1 - t)) * K))
            if len(pts) > 1:
                d.line(pts, fill=(255, 214, 64), width=int(5 * K))
        for (x, y) in pins:
            d.ellipse([(x - 16) * K, (y - 16) * K, (x + 16) * K, (y + 16) * K], fill=CORAL, outline=OUT, width=int(4 * K))
        tf = w("s5", "fidelizar")
        for i, (x, kw) in enumerate(((820, dict(skin=SKINS[3], shirt=(230, 120, 90), hair=(30, 25, 22), style="short")),
                                     (990, dict(skin=SKINS[0], shirt=(160, 120, 200), hair=(200, 150, 80), style="long")))):
            put(img, PERSON(1.1, expr="laugh" if T >= tf else "smile", **kw), x, 1780 + 18 * 1.1 + bob(T, 2, 2.0, i))
        dog_at(img, 900, 1800, 0.5, T, "happy", True, seed=4)
        hearts(img, T, tf, [(820, 1180), (990, 1200), (900, 1560)], 0.5)
        arms = sched(T, [(w("s5", "ventaja"), "open"), (w("s5", "personalización"), "wave")], "down")
        speaker(img, self.ctx, "daniela", "s5", T, 290, 1760, 1.25, arms, look=(0.5, -0.2), seed=3)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ov.show(fr, S_(("VENTAJA COMPETITIVA", "SOSTENIBLE"), 64, ov.YELLOW), 540, 610, T, w("s5", "ventaja"))
        ov.show(fr, ov.chip("FIDELIZAR", CORAL, size=46), 300, 760, T, w("s5", "fidelizar"))
        ov.show(fr, ov.chip("PET PARENTS", TEAL, size=46), 780, 760, T, w("s5", "pet"))
        ov.show(fr, ov.chip("PERSONALIZACIÓN MASIVA", GREEN, size=48), 540, 870, T, w("s5", "personalización"))
        ov.show(fr, name_tag("DANIELA", (90, 140, 200)), 290, 1370, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 6a · La cocina (Reyes, comandas)
class S6a(Shot):
    label = "La cocina"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_kitchen(c)
        self.counter = counter_layer(("printer",), steel=True)
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        ti = w("s6", "impresoras")
        arms = sched(T, [(w("s6", "Contamos"), "open"), (ti, "point")], "down")
        extra(img, "cocinera", T, 640, 1800, 1.3, "hold", hat=True, look=(-0.4, 0.3))
        put_layer(img, self.counter, dy=130 * K)
        santi_at(img, 300, 1790, 0.85, "happy" if T >= ti else "neutral", "stand", T, (0.6, -0.2), ctx=self.ctx, pid="s6")
        if T >= ti:
            age = (T - ti) % 3.0
            hh = min(200, age * 170)
            if hh > 4:
                d = ImageDraw.Draw(img)
                x0, x1, yb = 808, 932, 1426
                d.rectangle([x0 * K, (yb - hh) * K, x1 * K, yb * K], fill=(255, 255, 255), outline=OUT, width=int(4 * K))
                for k in range(int(hh // 26)):
                    y = yb - hh + 18 + k * 26
                    d.line([(x0 + 14) * K, y * K, (x1 - 14 - (k % 3) * 18) * K, y * K], fill=(140, 140, 150), width=int(5 * K))

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tc = w("s6", "Contamos")
        ov.show(fr, S_(("TRASTIENDA OPERATIVA", "E INDUSTRIAL"), 62), 540, 610, T, w("s6", "trastienda"), tc)
        ov.show(fr, S_(("HARDWARE ESPECIALIZADO",), 62), 540, 590, T, w("s6", "hardware"))
        ov.show(fr, ov.chip("IMPRESORAS DE COMANDAS", TEAL, size=46), 540, 700, T, w("s6", "impresoras"))
        ov.show(fr, ov.chip("EN TIEMPO REAL CON COCINA", CORAL, size=46), 540, 800, T, w("s6", "tiempo"))
        ov.show(fr, name_tag("REYES", REYES_TAG), 300, 1130, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 6b · La caja (pago sin contacto, ley)
class S6b(Shot):
    label = "La caja"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_interior(c, frames=False)
        self.counter = counter_layer(("pos", "espresso"))
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        tc = w("s6", "contacto")
        extra(img, "cocinera", T, 330, 1800, 1.45, "down", look=(0.6, 0.0), seed=1)
        put_layer(img, self.counter, dy=130 * K)
        if tc <= T < tc + 3.0:
            d = ImageDraw.Draw(img)
            for k in range(3):
                age = (T - tc - k * 0.25) % 0.9
                r = 30 + age * 110
                a = int(255 * (1 - age / 0.9))
                if a > 10:
                    d.arc([(690 - r) * K, (1360 - r) * K, (690 + r) * K, (1360 + r) * K], 280, 350, fill=(70, 200, 170), width=int(9 * K))
        santi_at(img, 860, 1770, 0.8, sched(T, [(w("s6", "transacciones"), "happy")], "curious"), "phone_stand", T, (-0.5, 0.0), seed=2, ctx=self.ctx, pid="s6")
        dog_at(img, 1010, 1790, 0.5, T, "happy", True, look=(-0.6, -0.3), seed=5)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tl_ = w("s6", "Ley")
        chips_seq(fr, T, [(w("s6", "terminales"), ov.chip("TERMINALES DE PAGO", TEAL, size=46), 540, 580),
                          (w("s6", "contacto"), ov.chip("SIN CONTACTO", CORAL, size=46), 540, 670),
                          (w("s6", "pasarelas"), ov.chip("PASARELAS DIGITALES", (120, 90, 190), size=46), 540, 760),
                          (w("s6", "transacciones"), ov.chip("TRANSACCIONES SEGURAS", GREEN, size=46), 540, 850)], tl_)
        ov.show(fr, shield_card(), 540, 720, T, tl_)
        ov.show(fr, name_tag("REYES", REYES_TAG), 860, 1150, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 6c · La bodega (inventario y merma)
class S6c(Shot):
    label = "La bodega"
    focus = (540, 1250)
    push = 0.05

    def build(self):
        c = Cv(W, H, 2, K)
        draw_bodega(c)
        return c.final()

    def animate(self, img, tl, T):
        santi_at(img, 300, 1770, 0.85, "neutral", "phone_stand", T, (0.3, 0.4), seed=2, ctx=self.ctx, pid="s6")
        put(img, cat(blink_at(T, 6), 0.45, (230, 150, 80), int(2 * math.sin(T * 2))), 640, 1790)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        ov.show(fr, ov.chip("SOFTWARE ERP", TEAL, size=50), 540, 570, T, w("s6", "software"))
        ov.show(fr, ov.chip("CONTROL DE INVENTARIOS", CORAL, size=46), 540, 665, T, w("s6", "inventarios"))
        tm = w("s6", "merma")
        st = ov.shown(T, tm)
        if st:
            q = int(26 * smooth(clamp((T - tm) / 1.2)))
            ov.paste_pop(fr, merma_card(q), 540, 860, st[0])
        ov.show(fr, name_tag("REYES", REYES_TAG), 300, 1130, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 6d · La azotea (en resumen)
class S6d(Shot):
    label = "La azotea"
    focus = (540, 1250)
    push = 0.06

    def build(self):
        c = Cv(W, H, 2, K)
        draw_rooftop(c)
        for x in (620, 1000):
            c.poly([(x - 40, 1560), (x + 40, 1560), (x + 30, 1660), (x - 30, 1660)], fill=(214, 110, 80))
            for k in range(5):
                a = math.radians(200 + k * 35)
                c.ell((x + 46 * math.cos(a) - 24, 1540 + 56 * math.sin(a) - 32, x + 46 * math.cos(a) + 24, 1540 + 56 * math.sin(a) + 32), fill=(96, 160, 96))
        return c.final()

    def animate(self, img, tl, T):
        w = self.ctx.wt
        ts = w("s6", "sinergia")
        p = clamp((T - ts) / 4.0)
        pts = [(470, 1480), (600, 1360), (690, 1410), (850, 1220), (1000, 1060)]
        if p > 0:
            seg = p * (len(pts) - 1)
            n = int(seg)
            path = pts[:n + 1]
            if n < len(pts) - 1:
                f = seg - n
                path = path + [(pts[n][0] + (pts[n + 1][0] - pts[n][0]) * f, pts[n][1] + (pts[n + 1][1] - pts[n][1]) * f)]
            d = ImageDraw.Draw(img)
            P = [(x * K, y * K) for x, y in path]
            if len(P) > 1:
                d.line(P, fill=OUT, width=int(34 * K), joint="curve")
                d.line(P, fill=(255, 214, 64), width=int(22 * K), joint="curve")
                (x0, y0), (x1, y1) = path[-2], path[-1]
                ang = math.atan2(y1 - y0, x1 - x0)
                hd = 46
                tri = [(x1 + hd * math.cos(ang), y1 + hd * math.sin(ang)),
                       (x1 + hd * 0.8 * math.cos(ang + 2.3), y1 + hd * 0.8 * math.sin(ang + 2.3)),
                       (x1 + hd * 0.8 * math.cos(ang - 2.3), y1 + hd * 0.8 * math.sin(ang - 2.3))]
                d.polygon([(x * K, y * K) for x, y in tri], fill=(255, 214, 64), outline=OUT, width=int(6 * K))
        expr = sched(T, [(w("s6", "vanguardista"), "happy")], "determined")
        santi_at(img, 290, 1770, 0.85, expr, "stand", T, (0.5, -0.4), seed=3, ctx=self.ctx, pid="s6")

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tv = w("s6", "vanguardista")
        chips_seq(fr, T, [(w("s6", "herramientas"), ov.chip("HERRAMIENTAS DIGITALES", TEAL, size=46), 540, 580),
                          (w("s6", "automatización"), ov.chip("AUTOMATIZACIÓN", CORAL, size=46), 540, 670),
                          (w("s6", "cumplimiento"), ov.chip("CUMPLIMIENTO NORMATIVO", GREEN, size=46), 540, 760)], tv)
        chips_seq(fr, T, [(tv, ov.chip("VANGUARDISTA", TEAL, size=64), 540, 600),
                          (w("s6", "escalable"), ov.chip("ESCALABLE", CORAL, size=64), 540, 720),
                          (w("s6", "rentable"), ov.chip("RENTABLE", GREEN, size=64), 540, 840)])
        ov.show(fr, name_tag("REYES", REYES_TAG), 290, 1130, T, self.t0 + 0.2)


# ------------------------------------------------------------------ 7 · Huellitas al atardecer (cierre)
class S7(Shot):
    label = "Huellitas"
    focus = (540, 1250)
    push = 0.07

    def build(self):
        c = Cv(W, H, 2, K)
        draw_terrace(c)
        chair_back(c, 290, 1631)
        chair_back(c, 820, 1631)
        round_table(c, 560, 1560, 240)
        for x in (520, 600):
            c.rect((x - 26, 1478, x + 26, 1540), fill=(255, 255, 255), r=8)
            c.ell((x - 24, 1470, x + 24, 1486), fill=(200, 150, 100))
        return c.final()

    def animate(self, img, tl, T):
        butterflies(img, T, [(200, 1060), (880, 1000), (560, 1160), (980, 1300)], 0.55)
        santi_at(img, 290, 1730, 0.8, "happy", "sit", T, (0.5, 0.0), ctx=self.ctx, pid="s7")
        dog_at(img, 820, 1640, 0.8, T, "happy", True, "chef", look=(-0.5, 0.0), seed=1)

    def overlay(self, fr, tl, T):
        w = self.ctx.wt
        tq = w("s7", "quién")
        chips_seq(fr, T, [(w("s7", "Café"), ov.chip("CAFÉ", COFFEE, size=54), 540, 570),
                          (w("s7", "mascota"), ov.chip("TU MASCOTA", CORAL, size=54), 540, 665),
                          (w("s7", "cero"), ov.chip("CERO ESPERAS", GREEN, size=54), 540, 760)], tq)
        ov.show(fr, S_(("¿A QUIÉN LLEVARÍAS", "TÚ A HUELLITAS?"), 68, ov.YELLOW), 540, 610, T, tq)
        ov.show(fr, ov.logo_card(400), 540, 880, T, tq + 0.4)


SHOTS = {"s1": S1, "s2": S2, "s3": S3, "s4a": S4a, "s4b": S4b, "s5a": S5a, "s5r": S5r, "s5b": S5b, "s5c": S5c,
         "s6a": S6a, "s6b": S6b, "s6c": S6c, "s6d": S6d, "s7": S7}
