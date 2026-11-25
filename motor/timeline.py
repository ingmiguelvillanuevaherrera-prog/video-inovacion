# Arma la línea de tiempo del video a partir de los audios recortados.
import os, re, json, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "audio")
import sys
sys.path.insert(0, HERE)
from narracion import PARTS

TEXT = dict(PARTS)
LEAD, TAIL, GAP_AB, PAUSE, CREDITS = 0.45, 0.35, 0.15, 4.5, 3.4

SCENES = [
    dict(id="s1", parts=["s1"], shots=[("s1", None)]),
    dict(id="s2", parts=["s2"], shots=[("s2", None)]),
    dict(id="s3", parts=["s3"], shots=[("s3", None)]),
    dict(id="s4", parts=["s4"], shots=[("s4a", None), ("s4b", ("s4", "tecnología", 1))]),
    dict(id="s5", parts=["s5"], shots=[("s5a", None), ("s5r", ("s5", "Esto", 1)), ("s5b", ("s5", "Además", 1)), ("s5c", ("s5", "Desde", 1))]),
    dict(id="s6", parts=["s6"], shots=[("s6a", None), ("s6b", ("s6", "terminales", 1)), ("s6c", ("s6", "Asimismo", 1)), ("s6d", ("s6", "resumen", 1))]),
    dict(id="s7", parts=["s7"], shots=[("s7", None)]),
]


def norm(s):
    s = s.lower()
    return "".join(ch for ch in s if ch.isalnum() or ch in "áéíóúüñ")


def decorate(text, words):
    """Agrega ¿¡ y ?! a cada palabra y marca dónde termina una frase."""
    toks = list(re.finditer(r"([¿¡]*)([\wáéíóúüñÁÉÍÓÚÜÑ]+)([^\w\s]*)", text))
    out, j = [], 0
    for w in words:
        disp, brk = w["t"], False
        for k in range(j, min(j + 4, len(toks))):
            if norm(toks[k].group(2)) == norm(w["t"]):
                pre, suf = toks[k].group(1), toks[k].group(3)
                disp = pre + w["t"] + "".join(ch for ch in suf if ch in "?!")
                brk = any(ch in suf for ch in ".,:;?!…")
                j = k + 1
                break
        out.append(dict(w, d=disp, brk=brk))
    return out


def build():
    parts = {}
    for pid, _ in PARTS:
        d = json.load(open(os.path.join(A, pid + "_t.json"), encoding="utf-8"))
        parts[pid] = d
    t = 0.0
    scenes, shots, placements, words = [], [], [], []
    for sc in SCENES:
        s0 = t
        cur = s0 + LEAD
        info = dict(id=sc["id"], t0=s0, parts={})
        for i, pid in enumerate(sc["parts"]):
            if i == 1:
                if sc.get("dyn"):
                    info["pause0"] = cur + GAP_AB
                    cur = info["pause0"] + PAUSE
                    info["reveal"] = cur
                else:
                    cur += GAP_AB
            dur = parts[pid]["dur"]
            info["parts"][pid] = dict(t0=cur, dur=dur)
            placements.append(dict(id=pid, t0=round(cur, 3)))
            for w in decorate(TEXT[pid], parts[pid]["words"]):
                words.append(dict(part=pid, t=w["t"], d=w["d"], brk=w["brk"], s=round(cur + w["s"], 3), e=round(cur + w["e"], 3)))
            cur += dur
        info["t1"] = cur + TAIL
        if sc.get("dyn"):
            info["dyn"] = sc["dyn"]
        scenes.append(info)
        # tomas
        shot_starts = []
        for key, sw in sc["shots"]:
            if sw is None:
                shot_starts.append((key, s0))
            else:
                pid, word, nth = sw
                cnt = 0
                for w in words:
                    if w["part"] == pid and norm(w["t"]) == norm(word):
                        cnt += 1
                        if cnt == nth:
                            shot_starts.append((key, w["s"] - 0.12))
                            break
        for i, (key, st) in enumerate(shot_starts):
            en = shot_starts[i + 1][1] if i + 1 < len(shot_starts) else info["t1"]
            shots.append(dict(key=key, scene=sc["id"], t0=round(st, 3), t1=round(en, 3)))
        t = info["t1"]
    total = t + CREDITS
    tl = dict(total=round(total, 3), credits0=round(t, 3), scenes=scenes, shots=shots, placements=placements, words=words)
    json.dump(tl, open(os.path.join(HERE, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return tl


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    tl = build()
    for sh in tl["shots"]:
        print(f"{sh['key']:4s} {sh['t0']:7.2f} -> {sh['t1']:7.2f}  ({sh['t1'] - sh['t0']:5.2f}s)")
    for sc in tl["scenes"]:
        if "pause0" in sc:
            print(sc["id"], "pausa", round(sc["pause0"], 2), "revela", round(sc["reveal"], 2))
    print("créditos desde", tl["credits0"], "TOTAL", tl["total"])
    
