# Recorta silencios largos entre oraciones y al final de cada parte; ajusta los tiempos de palabra.
import sys, os, json, wave, glob
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); A = os.path.join(HERE, "audio")
MAXGAP = 0.40; KEEP = MAXGAP / 2; TAIL = 0.15; HEAD = 0.05
tot = 0
for jf in sorted(glob.glob(os.path.join(A, "s*.json"))):
    if jf.endswith("_t.json"): continue
    d = json.load(open(jf, encoding="utf-8")); pid = d["id"]
    with wave.open(os.path.join(A, pid + ".wav")) as w:
        sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    words = d["words"]
    # segmentos a conservar en segundos
    cuts = []  # (start, end) a eliminar
    first = words[0]["s"]
    if first > HEAD: cuts.append((0.0, first - HEAD))
    for i in range(len(words) - 1):
        g0, g1 = words[i]["e"], words[i + 1]["s"]
        if g1 - g0 > MAXGAP: cuts.append((g0 + KEEP, g1 - KEEP))
    end = words[-1]["e"] + TAIL
    cuts.append((end, len(x) / sr))
    keep = []; pos = 0.0
    for c0, c1 in cuts:
        if c0 > pos: keep.append((pos, c0))
        pos = max(pos, c1)
    out = []; fade = int(0.004 * sr)
    for k0, k1 in keep:
        seg = x[int(k0 * sr):int(k1 * sr)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        out.append(seg)
    y = np.concatenate(out)
    def remap(t):
        removed = 0.0
        for c0, c1 in cuts:
            if t >= c1: removed += c1 - c0
            elif t > c0: removed += t - c0
        return round(t - removed, 3)
    nw = [{"t": w_["t"], "s": remap(w_["s"]), "e": remap(w_["e"])} for w_ in words]
    with wave.open(os.path.join(A, pid + "_t.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes())
    dur = len(y) / sr; tot += dur
    json.dump({"id": pid, "dur": dur, "words": nw}, open(os.path.join(A, pid + "_t.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{pid:4s} {d['dur']:6.2f} -> {dur:6.2f}")
print("TOTAL voz recortada", round(tot, 1))
