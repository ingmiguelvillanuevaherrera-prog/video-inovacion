# Música y efectos sintetizados con numpy + mezcla con la voz (ducking). Salida: mezcla.wav
import sys, os, json, wave, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
from render import Ctx

SR = 44100
rng = np.random.default_rng(7)


def T(sec):
    return int(round(sec * SR))


def tt(dur):
    return np.arange(T(dur)) / SR


def fft_filter(x, lo=None, hi=None, soft=0.15):
    """Filtro por FFT: deja pasar entre lo y hi Hz con bordes suaves."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1 / (1 + (f / hi) ** 4)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X * g, n)


def add(buf, sig, at, gain=1.0):
    i = T(at)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j0 = max(0, -i)
    sig = sig[j0:]
    i = max(0, i)
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain


def env_ad(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, T(a))
    e[:na] *= np.linspace(0, 1, na)
    return e


def noise(n):
    return rng.standard_normal(n)


# ------------------------------------------------------------------ instrumentos
def kick(gain=1.0):
    t = tt(0.35)
    f = 50 + 90 * np.exp(-t / 0.04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.12) * gain


def snare(gain=1.0):
    t = tt(0.25)
    n = fft_filter(noise(len(t)), 900, 7000) * np.exp(-t / 0.06)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05)
    return (0.7 * n / (np.abs(n).max() + 1e-9) + 0.5 * tone) * gain


def hat(gain=1.0):
    t = tt(0.06)
    n = fft_filter(noise(len(t)), 6000, None) * np.exp(-t / 0.014)
    return n / (np.abs(n).max() + 1e-9) * gain


def ep_note(f, dur, gain=1.0):
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    s *= (1 + 0.15 * np.sin(2 * np.pi * 4.5 * t))
    return s * env_ad(len(t), 0.01, 0.9) * gain


def pad_note(f, dur, gain=1.0):
    t = tt(dur)
    s = np.zeros_like(t)
    for h in range(1, 7):
        for det in (-0.6, 0.6):
            s += np.sin(2 * np.pi * (f + det) * h * t) / h
    e = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4)
    return s * e * gain / 6


def pluck(f, gain=1.0):
    t = tt(0.4)
    s = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))
    return s * np.exp(-t / 0.12) * gain


def bass(f, dur, gain=1.0):
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return s * env_ad(len(t), 0.01, dur * 0.7) * gain


# ------------------------------------------------------------------ secciones de música
def lofi(dur):
    buf = np.zeros(T(dur) + SR)
    beat = 60 / 84
    bar = 4 * beat
    chords = [([220.0, 261.63, 329.63, 392.0], 110.0), ([146.83, 174.61, 220.0, 261.63], 73.42),
              ([196.0, 246.94, 293.66, 349.23], 98.0), ([130.81, 164.81, 196.0, 246.94], 65.41)]
    nb = int(dur / bar) + 1
    for b in range(nb):
        t0 = b * bar
        notes, root = chords[b % 4]
        for k, f in enumerate(notes):
            add(buf, ep_note(f, bar * 0.95, 0.16), t0 + k * 0.012)
            add(buf, ep_note(f, beat * 1.5, 0.08), t0 + 2.5 * beat + k * 0.01)
        add(buf, bass(root, beat * 1.8, 0.5), t0)
        add(buf, bass(root, beat * 1.2, 0.4), t0 + 2.5 * beat)
        for q in range(4):
            if q in (0, 2):
                add(buf, kick(0.85), t0 + q * beat)
            else:
                add(buf, snare(0.35), t0 + q * beat)
            for e in range(2):
                sw = 0.11 * beat if e == 1 else 0
                add(buf, hat(0.10 if e == 0 else 0.07), t0 + q * beat + e * beat / 2 + sw)
        add(buf, kick(0.5), t0 + 2.5 * beat + 0.12 * beat)
    buf = fft_filter(buf, 35, 4200)
    cr = np.zeros_like(buf)
    idx = rng.integers(0, len(buf), int(dur * 6))
    cr[idx] = rng.uniform(-1, 1, len(idx))
    buf += fft_filter(cr, 1500, 6000) * 0.25
    return buf[:T(dur)]


def suspense(dur):
    t = tt(dur)
    s = np.zeros_like(t)
    for h in range(1, 9):
        s += np.sin(2 * np.pi * 55 * h * t) / h + 0.6 * np.sin(2 * np.pi * 82.41 * h * t + 1.3) / h
    s = fft_filter(s, 30, 500) * 0.10 * (0.75 + 0.25 * np.sin(2 * np.pi * 0.12 * t))
    s += 0.025 * np.sin(2 * np.pi * (880 + 6 * np.sin(2 * np.pi * 0.3 * t)) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t))
    beat = 0.92
    k = 0.0
    while k < dur:
        add(s, kick(0.55), k)
        add(s, kick(0.35), k + 0.2)
        k += beat
    return s


def inspiring(dur):
    buf = np.zeros(T(dur) + SR)
    beat = 60 / 100
    bar = 4 * beat
    prog = [([261.63, 329.63, 392.0], 65.41), ([196.0, 246.94, 293.66], 98.0), ([220.0, 261.63, 329.63], 110.0), ([174.61, 220.0, 261.63], 87.31)]
    nb = int(dur / bar) + 1
    for b in range(nb):
        t0 = b * bar
        notes, root = prog[b % 4]
        for f in notes:
            add(buf, pad_note(f, bar, 0.09), t0)
        add(buf, bass(root, bar * 0.9, 0.45), t0)
        arp = notes + [notes[1] * 2]
        for e in range(8):
            add(buf, pluck(arp[e % 4] * 2, 0.10), t0 + e * beat / 2)
        for q in range(4):
            add(buf, kick(0.6), t0 + q * beat)
            if q in (1, 3):
                add(buf, snare(0.25), t0 + q * beat)
            add(buf, hat(0.06), t0 + q * beat + beat / 2)
    buf = fft_filter(buf, 35, 6000)
    return buf[:T(dur)]


# ------------------------------------------------------------------ efectos
def whoosh(dur=0.5, gain=1.0):
    t = tt(dur)
    n = noise(len(t))
    lo = fft_filter(n, 300, 1500)
    hi = fft_filter(n, 1500, 7000)
    u = t / dur
    s = lo * (1 - u) + hi * u
    e = np.sin(np.pi * u) ** 2
    return s / (np.abs(s).max() + 1e-9) * e * gain


def beep(f, dur, gain=1.0):
    t = tt(dur)
    return np.sign(np.sin(2 * np.pi * f * t)) * 0.4 * env_ad(len(t), 0.003, dur) * gain


def pop(gain=1.0):
    t = tt(0.09)
    f = 520 + 600 * t / 0.09
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.035) * gain


def thunder(dur=1.6, gain=1.0):
    t = tt(dur)
    n = fft_filter(noise(len(t)), 30, 260)
    e = np.exp(-t / 0.5) * (1 + 0.6 * np.sin(2 * np.pi * 3 * t))
    return n / (np.abs(n).max() + 1e-9) * e * gain


def bell(gain=1.0):
    t = tt(1.6)
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((520, 1, 0.9), (1435, 0.5, 0.5), (2810, 0.3, 0.3)))
    return s * gain / 1.8


def coin_snd(gain=1.0):
    t = tt(0.5)
    return (np.sin(2 * np.pi * 2093 * t) + 0.6 * np.sin(2 * np.pi * 2637 * t)) * np.exp(-t / 0.12) * gain / 1.6


def chime(gain=1.0):
    out = np.zeros(T(1.6))
    for i, f in enumerate((659.25, 523.25)):
        t = tt(1.0)
        add(out, np.sin(2 * np.pi * f * t) * np.exp(-t / 0.4), i * 0.35)
    return out * gain


def ding(gain=1.0):
    t = tt(1.2)
    return (np.sin(2 * np.pi * 1046.5 * t) + 0.7 * np.sin(2 * np.pi * 1318.5 * t) + 0.4 * np.sin(2 * np.pi * 1568 * t)) * np.exp(-t / 0.35) * gain / 2


def tick(hi=True, gain=1.0):
    t = tt(0.05)
    return np.sin(2 * np.pi * (2200 if hi else 1600) * t) * np.exp(-t / 0.008) * gain


def pause_snd(gain=1.0):
    t = tt(0.35)
    f = 900 * np.exp(-t / 0.12) + 120
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.2) * gain


def notif(gain=1.0):
    out = np.zeros(T(0.4))
    for i, f in enumerate((1318.5, 1760)):
        t = tt(0.15)
        add(out, np.sin(2 * np.pi * f * t) * np.exp(-t / 0.05), i * 0.11)
    return out * gain


def chirp(gain=1.0):
    t = tt(0.12)
    f = 3200 + 1400 * np.sin(np.pi * t / 0.12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.12) * gain


def woof(gain=1.0):
    """Ladrido caricatura: dos golpes graves con caída de tono."""
    out = np.zeros(T(0.5))
    for i, (f0, d) in enumerate(((420, 0.13), (380, 0.16))):
        t = tt(d)
        f = f0 * np.exp(-t / 0.12) + 160
        ph = 2 * np.pi * np.cumsum(f) / SR
        sig = np.sign(np.sin(ph)) * 0.5 + np.sin(2 * ph) * 0.3 + noise(len(t)) * 0.15
        sig = fft_filter(sig, 150, 2400) * env_ad(len(t), 0.006, d * 0.6)
        add(out, sig / (np.abs(sig).max() + 1e-9), i * 0.2)
    return out * gain


def womp(gain=1.0):
    """'Womp womp' triste: dos notas que bajan."""
    out = np.zeros(T(1.3))
    for i, (f0, f1) in enumerate(((330, 290), (290, 220))):
        d = 0.45 if i else 0.3
        t = tt(d)
        f = f0 + (f1 - f0) * t / d
        ph = 2 * np.pi * np.cumsum(f) / SR
        sig = sum(np.sin(h * ph) / h for h in range(1, 7))
        sig = fft_filter(sig, 80, 2000) * env_ad(len(t), 0.02, d * 0.8)
        add(out, sig / (np.abs(sig).max() + 1e-9), i * 0.36)
    return out * gain


def riser(dur=1.2, gain=1.0):
    t = tt(dur)
    n = fft_filter(noise(len(t)), 800, 9000)
    return n / (np.abs(n).max() + 1e-9) * (t / dur) ** 2 * gain


def bed_noise(dur, lo, hi, gain):
    n = fft_filter(noise(T(dur)), lo, hi)
    n = n / (np.abs(n).max() + 1e-9)
    e = np.minimum(1, np.minimum(np.arange(len(n)) / SR / 0.5, (dur - np.arange(len(n)) / SR) / 0.5))
    return n * e * gain


def read_wav(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def main():
    tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
    ctx = Ctx(tl)
    wt = ctx.wt
    sc = {s["id"]: s for s in tl["scenes"]}
    shots = {s["key"]: s for s in tl["shots"]}
    total = tl["total"]
    N = T(total) + SR

    voice = np.zeros(N)
    for pl in tl["placements"]:
        add(voice, read_wav(os.path.join(HERE, "audio", pl["id"] + "_t.wav")), pl["t0"])
    voice *= 0.72 / (np.abs(voice).max() + 1e-9)

    # música por secciones con cruces de 1 s
    music = np.zeros(N)
    b = shots["s6d"]["t0"]
    xf = 1.0
    for fn, s0, s1 in ((lofi, 0.0, b), (inspiring, b, total)):
        seg = fn(s1 - s0 + xf)
        seg = seg / (np.abs(seg).max() + 1e-9)
        n = len(seg)
        e = np.ones(n)
        k = T(xf)
        if s0 > 0:
            e[:k] = np.linspace(0, 1, k)
        if s1 < total:
            e[-k:] = np.linspace(1, 0, k)
        else:
            fo = T(2.5)
            e[-fo:] *= np.linspace(1, 0, fo)
        add(music, seg * e, max(0, s0 - (xf / 2 if s0 > 0 else 0)))

    # ducking bajo la voz y bajo las tarjetas de pausa
    win = T(0.25)
    cs = np.concatenate([[0.0], np.cumsum(np.abs(voice))])
    lo_i = np.clip(np.arange(len(voice)) - win // 2, 0, len(voice))
    hi_i = np.clip(np.arange(len(voice)) + win // 2, 0, len(voice))
    env = (cs[hi_i] - cs[lo_i]) / win
    env = np.clip(env / 0.06, 0, 1)
    gain = 0.26 - 0.15 * env
    for s in sc.values():
        if "pause0" in s:
            i0, i1 = T(s["pause0"]), T(s["reveal"])
            gain[i0:i1] *= 0.45
    music *= gain

    fx = np.zeros(N)
    for key, s in shots.items():
        if s["t0"] > 0.1:
            add(fx, whoosh(0.5, 0.30), s["t0"] - 0.2)
    P = lambda part, word, g=0.28, n=1: add(fx, pop(g), wt(part, word, n))
    # 1 · Condesa
    k = 0.5
    while k < shots["s1"]["t1"]:
        add(fx, chirp(0.05), k); add(fx, chirp(0.04), k + 0.16); k += 2.1
    P("s1", "Quiero")
    add(fx, woof(0.35), wt("s1", "perro") + 0.35)
    add(fx, womp(0.30), wt("s1", "mascotas"))
    # 2 · Zamora 165
    add(fx, bell(0.35), wt("s2", "Huellitas"))
    for word in ("Zamora", "pet", "entras", "convives"):
        P("s2", word)
    add(fx, woof(0.3), wt("s2", "convives") + 0.2)
    # 3 · la app
    for word in ("aparto", "menú", "pido", "pago", "sigo"):
        add(fx, notif(0.22), wt("s3", word))
    add(fx, ding(0.35), wt("s3", "listo"))
    # 4 · Jaqueline
    for word in ("viabilidad", "arquitectura", "escalar", "cumplir", "protección"):
        P("s4", word)
    k = wt("s4", "reducir")
    while k < wt("s4", "cinco"):
        add(fx, tick(True, 0.12), k); k += 0.5
    add(fx, ding(0.35), wt("s4", "cinco") + 0.3)
    add(fx, riser(1.0, 0.15), wt("s4", "Cómo") - 0.9)
    # 5 · Daniela
    for word in ("ecosistema", "plataforma", "kioscos", "optimiza", "reservar", "consultar", "realizar", "sistema", "Huellitas", "ventaja", "fidelizar", "pet", "personalización"):
        P("s5", word)
    add(fx, beep(1800, 0.12, 0.10), wt("s5", "QR")); add(fx, pop(0.28), wt("s5", "QR"))
    add(fx, coin_snd(0.25), wt("s5", "cupones"))
    add(fx, chime(0.30), wt("s5", "cumpleaños"))
    add(fx, woof(0.25), wt("s5", "cumpleaños") + 0.5)
    # 6 · Reyes
    for word in ("trastienda", "hardware", "impresoras", "tiempo", "terminales", "pasarelas", "transacciones", "software", "inventarios", "herramientas", "automatización", "cumplimiento"):
        P("s6", word)
    ti = wt("s6", "impresoras"); k = ti
    while k < shots["s6a"]["t1"] - 0.3:
        add(fx, bed_noise(0.9, 1500, 5000, 0.05), k); k += 3.0
    add(fx, notif(0.3), wt("s6", "contacto"))
    add(fx, ding(0.3), wt("s6", "Ley"))
    add(fx, pop(0.3), wt("s6", "merma"))
    add(fx, riser(1.2, 0.15), wt("s6", "vanguardista") - 1.1)
    for word in ("vanguardista", "escalable", "rentable"):
        add(fx, pop(0.38), wt("s6", word)); add(fx, coin_snd(0.18), wt("s6", word) + 0.05)
    # 7 · cierre
    for word in ("Café", "mascota", "cero"):
        P("s7", word, 0.3)
    add(fx, riser(1.0, 0.18), wt("s7", "quién") - 1.0)
    add(fx, ding(0.35), wt("s7", "quién"))
    add(fx, woof(0.3), wt("s7", "Huellitas") + 0.6)
    add(fx, whoosh(0.6, 0.3), tl["credits0"] - 0.25)
    # dinámicas
    for s in sc.values():
        if "pause0" in s:
            p0 = s["pause0"]
            add(fx, pause_snd(0.45), p0)
            k = p0 + 1.5
            i = 0
            while k < s["reveal"] - 0.05:
                add(fx, tick(i % 2 == 0, 0.35), k)
                k += 0.5
                i += 1
            add(fx, ding(0.5), s["reveal"])

    mixd = voice + music + fx
    mixd *= 0.89 / (np.abs(mixd).max() + 1e-9)
    mixd = mixd[:T(total)]
    st = np.stack([mixd, mixd], 1)
    out = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else "mezcla.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
    print("mezcla.wav", round(len(mixd) / SR, 2), "s  voz pico", round(float(np.abs(voice).max()), 2),
          "música rms", round(float(np.sqrt(np.mean(music ** 2))), 3), "fx pico", round(float(np.abs(fx).max()), 2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
