# Capas de texto en pantalla: etiqueta de lugar, subtítulos, chips, gráficas y tarjetas.
import functools, math
from PIL import Image, ImageDraw, ImageFilter
from gfx import font, OUT, W, H, clamp, ease_back, ease_out, smooth, mix

WHITE = (255, 255, 255)
YELLOW = (255, 214, 64)
TEAL = (16, 140, 138)
CORAL = (226, 88, 66)
GREEN = (44, 168, 104)
INK = (24, 34, 40)
CARD = (250, 248, 242)
GRAY = (226, 226, 220)

FONTS_EXTRA = {"bolditalic": "segoeuiz.ttf"}


def _font(name, size):
    if name in FONTS_EXTRA:
        from PIL import ImageFont
        return _fx(name, int(round(size)))
    return font(name, size)


@functools.lru_cache(maxsize=64)
def _fx(name, size):
    from PIL import ImageFont
    return ImageFont.truetype("C:/Windows/Fonts/" + FONTS_EXTRA[name], size)


_D = ImageDraw.Draw(Image.new("RGBA", (4, 4)))


def tsize(s, f, stroke=0):
    bb = _D.textbbox((0, 0), s, font=f, stroke_width=stroke)
    return bb, bb[2] - bb[0], bb[3] - bb[1]


@functools.lru_cache(maxsize=1024)
def text_img(s, size, fill=WHITE, fname="black", stroke=0, stroke_fill=OUT):
    f = _font(fname, size)
    bb, w, h = tsize(s, f, stroke)
    p = stroke + 4
    im = Image.new("RGBA", (w + 2 * p, h + 2 * p), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((p - bb[0], p - bb[1]), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def fit_size(s, size, max_w, fname="black", stroke=0):
    while size > 20:
        _, w, _ = tsize(s, _font(fname, size), stroke)
        if w + 2 * stroke <= max_w:
            return size
        size -= 2
    return size


@functools.lru_cache(maxsize=256)
def stack_text(lines, size, fill=WHITE, fname="black", stroke=10, gap=0.08):
    """Varias líneas centradas con contorno (para títulos)."""
    ims = [text_img(l, size, fill, fname, stroke) for l in lines]
    w = max(i.width for i in ims)
    lh = [i.height for i in ims]
    g = int(size * gap)
    out = Image.new("RGBA", (w, sum(lh) + g * (len(ims) - 1)), (0, 0, 0, 0))
    y = 0
    for im in ims:
        out.paste(im, ((w - im.width) // 2, y), im)
        y += im.height + g
    return out


def ss_canvas(w, h, ss=2):
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def ss_done(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


# ------------------------------------------------------------- piezas fijas
@functools.lru_cache(maxsize=32)
def loc_label(s):
    size = fit_size(s.upper(), 92, 980, "black", 11)
    return text_img(s.upper(), size, WHITE, "black", 11)


@functools.lru_cache(maxsize=256)
def chip(s, bg=TEAL, fg=WHITE, size=44, fname="black"):
    f = font(fname, size * 2)
    bb, tw, th = tsize(s, f)
    h = int(size * 1.55)
    w = tw // 2 + 56
    im, d = ss_canvas(w + 12, h + 12)
    d.rounded_rectangle([6 * 2, 6 * 2, (w + 6) * 2, (h + 6) * 2], radius=h, fill=bg, outline=OUT, width=10)
    d.text(((w + 12), (h + 12)), s, font=f, fill=fg, anchor="mm")
    return ss_done(im, w + 12, h + 12)


def paste_pop(fr, img, cx, cy, age, dur=0.28, fade_out_age=None, start_scale=0.55, alpha=1.0):
    """Pega img centrada en (cx,cy) con entrada tipo 'pop'. age = segundos desde que aparece."""
    if age < 0:
        return
    s = start_scale + (1 - start_scale) * ease_back(age / dur)
    a = clamp(age / (dur * 0.6)) * alpha
    if fade_out_age is not None and fade_out_age > 0:
        a *= 1 - clamp(fade_out_age / 0.22)
        s *= 1 - 0.1 * clamp(fade_out_age / 0.22)
    if a <= 0.01:
        return
    im = img
    if abs(s - 1) > 0.01:
        im = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
    if a < 0.99:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    fr.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def shown(T, t_on, t_off=None):
    """Devuelve (age, fade_age) o None si no se muestra."""
    if t_on is None or T < t_on:
        return None
    fade = None
    if t_off is not None and T >= t_off:
        fade = T - t_off
        if fade > 0.25:
            return None
    return (T - t_on, fade)


def show(fr, img, cx, cy, T, t_on, t_off=None, **kw):
    st = shown(T, t_on, t_off)
    if st:
        paste_pop(fr, img, cx, cy, st[0], fade_out_age=st[1], **kw)


def arrow(fr, p0, p1, color=WHITE, w=7, head=26, alpha=1.0):
    """Flecha con contorno de p0 a p1 (coordenadas de pantalla)."""
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", fr.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0 = p0
    x1, y1 = p1
    ang = math.atan2(y1 - y0, x1 - x0)
    bx, by = x1 - head * 0.8 * math.cos(ang), y1 - head * 0.8 * math.sin(ang)
    tri = [(x1, y1), (bx + head * 0.6 * math.cos(ang + math.pi / 2), by + head * 0.6 * math.sin(ang + math.pi / 2)),
           (bx - head * 0.6 * math.cos(ang + math.pi / 2), by - head * 0.6 * math.sin(ang + math.pi / 2))]
    d.line([p0, (bx, by)], fill=OUT + (255,), width=w + 8)
    d.polygon(tri, fill=OUT + (255,), outline=OUT + (255,), width=8)
    d.line([p0, (bx, by)], fill=color + (255,), width=w)
    d.polygon(tri, fill=color + (255,))
    if alpha < 0.99:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    fr.paste(lay, (0, 0), lay)


# ------------------------------------------------------------- subtítulos
@functools.lru_cache(maxsize=2048)
def caption_img(words, active, size=70):
    words = [w.upper() for w in words]
    stroke = 10
    s = " ".join(words)
    size = fit_size(s, size, 1000, "black", stroke)
    f = font("black", size)
    space = f.getlength(" ")
    widths = [f.getlength(w) for w in words]
    tw = int(sum(widths) + space * (len(words) - 1))
    bb, _, th = tsize("ÁGjy", f, stroke)
    p = stroke + 6
    im = Image.new("RGBA", (tw + 2 * p, th + 2 * p), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = p
    for i, w in enumerate(words):
        col = YELLOW if i == active else WHITE
        d.text((x, p - bb[1]), w, font=f, fill=col, stroke_width=stroke, stroke_fill=OUT)
        x += widths[i] + space
    return im


# ------------------------------------------------------------- tarjetas
def card_base(w, h, ss=2, fill=CARD, radius=34):
    im, d = ss_canvas(w, h, ss)
    d.rounded_rectangle([5 * ss, 5 * ss, (w - 5) * ss, (h - 5) * ss], radius=radius * ss, fill=fill, outline=OUT, width=7 * ss)
    return im, d


@functools.lru_cache(maxsize=8)
def quote_card():
    w, h = 940, 300
    im, d = card_base(w, h)
    d.text((80 * 2, 70 * 2), "“", font=font("black", 170 * 2), fill=TEAL, anchor="mm")
    f = _font("bolditalic", 54 * 2)
    d.text((w, 128 * 2), "Ni estamos solos,", font=f, fill=INK, anchor="mm")
    d.text((w, 196 * 2), "ni somos autárquicos.", font=f, fill=INK, anchor="mm")
    d.text((w, 258 * 2), "El impacto de la globalización en el futuro de México · CISC, 2006", font=font("semi", 22 * 2), fill=(110, 120, 124), anchor="mm")
    return ss_done(im, w, h)


@functools.lru_cache(maxsize=8)
def stat_card():
    w, h = 940, 470
    im, d = card_base(w, h)
    d.rounded_rectangle([60 * 2, 40 * 2, 230 * 2, 100 * 2], radius=60, fill=INK)
    d.text((145 * 2, 70 * 2), "2002", font=font("black", 40 * 2), fill=WHITE, anchor="mm")
    d.text((w, 200 * 2), "80%", font=font("black", 170 * 2), fill=CORAL, anchor="mm")
    d.text((w, 320 * 2), "de 20 millones de crímenes ocurrió en", font=font("bold", 42 * 2), fill=INK, anchor="mm")
    d.text((w, 380 * 2), "solo 20 de 157 países", font=font("black", 52 * 2), fill=INK, anchor="mm")
    d.text((w, 432 * 2), "Naciones supervisadas por la ONU · diapositiva 13", font=font("semi", 24 * 2), fill=(110, 120, 124), anchor="mm")
    return ss_done(im, w, h)


@functools.lru_cache(maxsize=16)
def num_card(n, s):
    w, h = 900, 104
    im, d = card_base(w, h, radius=52)
    d.ellipse([22 * 2, 14 * 2, 98 * 2, 90 * 2], fill=TEAL, outline=OUT, width=10)
    d.text((60 * 2, 53 * 2), str(n), font=font("black", 48 * 2), fill=WHITE, anchor="mm")
    d.text((128 * 2, 53 * 2), s, font=font("black", 46 * 2), fill=INK, anchor="lm")
    return ss_done(im, w, h)


def bar_chart_pib(progress_fn):
    """Panel con barras horizontales del PIB 2004. progress_fn(i) -> 0..1"""
    data = [("EE.UU.", 12.2), ("Japón", 4.8), ("Alemania", 2.8), ("China", 1.9), ("México", 0.8), ("India", 0.7)]
    w, h = 960, 640
    im, d = card_base(w, h)
    S = 2
    d.text((w, 62 * S), "PIB 2004 · billones de dólares", font=font("black", 44 * S), fill=INK, anchor="mm")
    x0, x1 = 250, 830
    for i, (name, v) in enumerate(data):
        y = 128 + i * 78
        mex = name == "México"
        d.text(((x0 - 22) * S, (y + 27) * S), name, font=font("black" if mex else "bold", 38 * S), fill=CORAL if mex else INK, anchor="rm")
        p = clamp(progress_fn(i))
        bw = (x1 - x0) * v / 13.0 * ease_out(p)
        if bw > 2:
            d.rounded_rectangle([x0 * S, y * S, (x0 + bw) * S, (y + 54) * S], radius=12 * S, fill=CORAL if mex else TEAL, outline=OUT, width=6)
        if p > 0.6:
            d.text(((x0 + bw + 14) * S, (y + 27) * S), f"{v:.1f}", font=font("black", 36 * S), fill=INK, anchor="lm")
    d.text((w, 606 * S), "Fuente: FMI, 2004 · diapositiva 5", font=font("semi", 24 * S), fill=(110, 120, 124), anchor="mm")
    return ss_done(im, w, h)


def bar_chart_pob(progress_fn):
    """Barras agrupadas de población 1997 vs 2050 (América y Europa ocultas para la dinámica)."""
    data = [("Asia", 3600, 5300), ("África", 800, 1800), ("América", None, None), ("Europa", None, None)]
    w, h = 960, 660
    im, d = card_base(w, h)
    S = 2
    d.text((w, 60 * S), "Población · millones (aprox.)", font=font("black", 44 * S), fill=INK, anchor="mm")
    # leyenda
    d.rounded_rectangle([300 * S, 100 * S, 330 * S, 128 * S], radius=8, fill=CORAL, outline=OUT, width=4)
    d.text((340 * S, 114 * S), "1997", font=font("bold", 30 * S), fill=INK, anchor="lm")
    d.rounded_rectangle([500 * S, 100 * S, 530 * S, 128 * S], radius=8, fill=TEAL, outline=OUT, width=4)
    d.text((540 * S, 114 * S), "2050", font=font("bold", 30 * S), fill=INK, anchor="lm")
    base_y, top_y = 560, 170
    d.line([(60 * S, base_y * S), (900 * S, base_y * S)], fill=OUT, width=6)
    for i, (name, a, b) in enumerate(data):
        cx = 150 + i * 215
        d.text((cx * S, (base_y + 36) * S), name, font=font("black", 34 * S), fill=INK, anchor="mm")
        if a is None:
            d.rounded_rectangle([(cx - 60) * S, (base_y - 150) * S, (cx + 60) * S, base_y * S], radius=12 * S, fill=GRAY, outline=OUT, width=6)
            d.text((cx * S, (base_y - 75) * S), "?", font=font("black", 80 * S), fill=(120, 120, 120), anchor="mm")
            continue
        p = clamp(progress_fn(i))
        for j, (v, col) in enumerate(((a, CORAL), (b, TEAL))):
            hh = (base_y - top_y) * v / 6000 * ease_out(p)
            x = cx - 64 + j * 66
            if hh > 2:
                d.rounded_rectangle([x * S, (base_y - hh) * S, (x + 60) * S, base_y * S], radius=10 * S, fill=col, outline=OUT, width=6)
            if p > 0.6:
                d.text(((x + 30) * S, (base_y - hh - 22) * S), f"{v:,}", font=font("black", 26 * S), fill=INK, anchor="mm")
    d.text((w, 630 * S), "Diapositiva 6 · África más que duplica su población", font=font("semi", 24 * S), fill=(110, 120, 124), anchor="mm")
    return ss_done(im, w, h)


# ------------------------------------------------------------- tarjeta de pausa
def wrap(s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if _D.textlength(t, font=f) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


@functools.lru_cache(maxsize=64)
def pause_card(q, opts, ans_idx, mode, count):
    """mode: 'ask' (sin conteo), 'count' (con número), 'reveal'."""
    w, h = 960, 900
    S = 2
    im, d = card_base(w, h, S)
    # píldora PAUSA
    d.rounded_rectangle([300 * S, 34 * S, 660 * S, 112 * S], radius=40 * S, fill=CORAL, outline=OUT, width=7 * S)
    d.rectangle([342 * S, 54 * S, 356 * S, 92 * S], fill=WHITE)
    d.rectangle([366 * S, 54 * S, 380 * S, 92 * S], fill=WHITE)
    d.text((510 * S, 74 * S), "¡PAUSA!", font=font("black", 50 * S), fill=WHITE, anchor="mm")
    d.text((w, 160 * S), "¿Tú qué crees?", font=font("black", 50 * S), fill=TEAL, anchor="mm")
    fq = font("bold", 42 * S)
    lines = wrap(q, fq, 860 * S)
    y = 222
    for l in lines:
        d.text((w, y * S), l, font=fq, fill=INK, anchor="mm")
        y += 54
    oy = max(y + 20, 360)
    for i, o in enumerate(opts):
        top = oy + i * 118
        correct = mode == "reveal" and i == ans_idx
        faded = mode == "reveal" and i != ans_idx
        fill = GREEN if correct else ((236, 236, 232) if faded else (240, 240, 236))
        d.rounded_rectangle([70 * S, top * S, 890 * S, (top + 100) * S], radius=26 * S, fill=fill, outline=OUT if not faded else (150, 150, 150), width=6 * S)
        letter = "ABC"[i]
        d.ellipse([92 * S, (top + 14) * S, 164 * S, (top + 86) * S], fill=WHITE if correct else (TEAL if not faded else (180, 180, 180)), outline=OUT if not faded else (150, 150, 150), width=5 * S)
        d.text((128 * S, (top + 51) * S), letter, font=font("black", 42 * S), fill=GREEN if correct else WHITE, anchor="mm")
        d.text((190 * S, (top + 50) * S), o, font=font("black", 44 * S), fill=WHITE if correct else ((160, 160, 160) if faded else INK), anchor="lm")
        if correct:
            d.line([(800 * S, (top + 52) * S), (826 * S, (top + 76) * S), (866 * S, (top + 28) * S)], fill=WHITE, width=12 * S, joint="curve")
    by = oy + 3 * 118 + 50
    if mode == "ask":
        d.text((w, by * S), "Pausen el video y voten: A, B o C", font=font("bold", 36 * S), fill=(90, 100, 104), anchor="mm")
    elif mode == "count":
        d.ellipse([(480 - 52) * S, (by - 52) * S, (480 + 52) * S, (by + 52) * S], fill=CORAL, outline=OUT, width=6 * S)
        d.text((w, (by + 2) * S), str(count), font=font("black", 66 * S), fill=WHITE, anchor="mm")
    else:
        d.text((w, by * S), "¡RESPUESTA!", font=font("black", 50 * S), fill=GREEN, anchor="mm")
    return ss_done(im, w, h)


# ------------------------------------------------------------- logo y créditos
import os as _os
_LOGO = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "logo.png")


@functools.lru_cache(maxsize=16)
def logo_img(width, ink=(34, 30, 30), thick=5):
    """Logo de Huellitas como RGBA (líneas en color ink, fondo transparente)."""
    g = Image.open(_LOGO).convert("L")
    g = g.point(lambda v: 255 if v > 200 else v)
    bb = Image.eval(g, lambda v: 255 - v).getbbox()
    g = g.crop((bb[0] - 10, bb[1] - 10, bb[2] + 10, bb[3] + 10))
    if thick > 1:
        g = g.filter(ImageFilter.MinFilter(thick))
    a = g.point(lambda v: max(0, min(255, int((255 - v) * 1.5))))
    h = int(g.height * width / g.width)
    a = a.resize((width, h), Image.LANCZOS)
    im = Image.new("RGBA", (width, h), ink + (255,))
    im.putalpha(a)
    return im


@functools.lru_cache(maxsize=4)
def logo_card(width):
    lg = logo_img(width - 70)
    w, h = width, lg.height + 70
    im, d = card_base(w, h, fill=(255, 253, 248))
    im = ss_done(im, w, h)
    im.paste(lg, (35, 35), lg)
    return im


@functools.lru_cache(maxsize=1)
def credits_frame():
    im = Image.new("RGB", (W * 2, H * 2), (252, 246, 236))
    d = ImageDraw.Draw(im)
    S = 2
    lg = logo_img(820 * S, thick=9)
    im.paste(lg, (W - lg.width // 2, 330 * S), lg)
    y = 330 + lg.height // S + 70
    for s, fn, sz, col in [("Café pet friendly", "black", 58, (16, 140, 138)),
                           ("Zamora 165, Condesa, CDMX", "bold", 46, INK),
                           ("Jaqueline · Daniela · Reyes", "bold", 44, (120, 80, 52))]:
        d.text((W, y * S), s, font=font(fn, sz * S), fill=col, anchor="mm")
        y += sz + 40
    d.text((W, 1500 * S), "Animación hecha con código · voces sintéticas", font=font("semi", 30 * S), fill=(150, 140, 130), anchor="mm")
    return im.resize((W, H), Image.LANCZOS)
