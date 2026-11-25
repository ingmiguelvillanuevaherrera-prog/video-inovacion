# Renderiza cuadros: escena + cámara + textos + subtítulos. Modos: stills, video, mux.
import sys, os, json, math, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageFilter
from gfx import W, H, FPS, K, clamp, ease_out
import overlays as ov
import scenes as SC
from timeline import norm
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(HERE)


class Ctx:
    def __init__(self, tl):
        self.tl = tl
        self.idx = {}
        for w in tl["words"]:
            self.idx.setdefault((w["part"], norm(w["t"])), []).append(w["s"])
        self.scenes = {s["id"]: s for s in tl["scenes"]}
        self.cam = None

    def wt(self, part, word, n=1):
        L = self.idx.get((part, norm(word)))
        if not L:
            raise KeyError(f"{part}:{word}")
        return L[min(n, len(L)) - 1]

    def scene(self, sid):
        return self.scenes[sid]


def make_chunks(words):
    chunks, cur = [], []
    for w in words:
        if cur and (w["part"] != cur[-1]["part"] or len(cur) >= 3 or sum(len(x["d"]) for x in cur) + len(w["d"]) > 16):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if w["brk"]:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        nxt = chunks[i + 1] if i + 1 < len(chunks) else None
        if nxt and nxt[0]["part"] == ch[0]["part"]:
            t_off = min(nxt[0]["s"], ch[-1]["e"] + 0.7)
        else:
            t_off = ch[-1]["e"] + 0.4
        out.append((ch[0]["s"], t_off, ch))
    return out


class Renderer:
    def __init__(self):
        self.tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
        self.ctx = Ctx(self.tl)
        self.shots = [SC.SHOTS[s["key"]](self.ctx, s) for s in self.tl["shots"]]
        for sh in self.shots:
            sh.info["scene"] = next(s["scene"] for s in self.tl["shots"] if s["key"] == sh.info["key"])
        self.chunks = make_chunks(self.tl["words"])
        self.frozen = {}

    def shot_at(self, T):
        for sh in self.shots:
            if sh.t0 <= T < sh.t1:
                return sh
        return self.shots[-1]

    def camera(self, sh, T):
        tl = T - sh.t0
        dur = max(0.1, sh.t1 - sh.t0)
        z = 1 + sh.push * clamp(tl / dur) + 0.10 * (1 - ease_out(tl / 0.35))
        Wb, Hb = sh.get_base().size
        rw, rh = Wb / z, Hb / z
        cx, cy = sh.focus[0] * K, sh.focus[1] * K
        if sh.shake:
            cx += (math.sin(T * 31) + math.sin(T * 17)) * sh.shake * K * 0.5
            cy += math.sin(T * 23) * sh.shake * K * 0.5
        left = min(max(cx - rw / 2, 0), Wb - rw)
        top = min(max(cy - rh / 2, 0), Hb - rh)
        return left, top, rw, rh

    def scene_frame(self, sh, T):
        img = sh.get_base().copy()
        sh.animate(img, T - sh.t0, T)
        left, top, rw, rh = self.camera(sh, T)
        self.ctx.cam = lambda x, y: ((x * K - left) / rw * W, (y * K - top) / rh * H)
        return img.resize((W, H), Image.BILINEAR, box=(left, top, left + rw, top + rh))

    def frozen_bg(self, sh, sc):
        key = sc["id"]
        if key not in self.frozen:
            fr = self.scene_frame(sh, sc["pause0"])
            fr = fr.filter(ImageFilter.GaussianBlur(10))
            fr = Image.blend(fr, Image.new("RGB", (W, H), (8, 14, 18)), 0.45)
            self.frozen[key] = fr
        return self.frozen[key]

    def caption(self, fr, T, sh):
        for (t_on, t_off, ch) in self.chunks:
            if t_on <= T < t_off:
                active = max(j for j, w in enumerate(ch) if w["s"] <= T)
                im = ov.caption_img(tuple(w["d"] for w in ch), active)
                age = T - t_on
                if age < 0.1:
                    s = 0.9 + 0.1 * age / 0.1
                    im = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
                fr.paste(im, (int(540 - im.width / 2), int(sh.caption_y - im.height / 2)), im)
                return

    def frame(self, T):
        tl = self.tl
        if T >= tl["credits0"]:
            fr = ov.credits_frame().copy()
            a = clamp((T - tl["credits0"]) / 0.25)
            if a < 1:
                fr = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), fr, a)
            return fr
        sh = self.shot_at(T)
        sc = self.ctx.scene(sh.info["scene"])
        pause = "pause0" in sc and T >= sc["pause0"]
        if pause:
            fr = self.frozen_bg(sh, sc).copy()
            age = T - sc["pause0"]
            d = sc["dyn"]
            if T >= sc["reveal"]:
                mode, cnt = "reveal", 0
            elif age < 1.5:
                mode, cnt = "ask", 0
            else:
                mode, cnt = "count", max(1, min(3, 3 - int(age - 1.5)))
            card = ov.pause_card(d["q"], tuple(d["opts"]), d["ans"], mode, cnt)
            if mode == "reveal":
                ov.paste_pop(fr, card, 540, 990, 1.0 + (T - sc["reveal"]) * 0 if T - sc["reveal"] > 0.3 else T - sc["reveal"] + 0.12, start_scale=0.9)
            else:
                ov.paste_pop(fr, card, 540, 990, age, start_scale=0.8)
        else:
            fr = self.scene_frame(sh, T)
            sh.overlay(fr, T - sh.t0, T)
            ov.paste_pop(fr, ov.loc_label(sh.label), 540, 330, T - sh.t0, dur=0.3)
        self.caption(fr, T, sh)
        return fr


_R = None


def get_R():
    global _R
    if _R is None:
        _R = Renderer()
    return _R


def render_range(args):
    f0, f1, out = args
    R = get_R()
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(R.frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


def main():
    mode = sys.argv[1]
    if mode == "stills":
        R = get_R()
        os.makedirs(os.path.join(ROOT, "preview"), exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]]
        thumbs = []
        for T in ts:
            t0 = time.time()
            fr = R.frame(T)
            print(f"T={T:7.2f}  {time.time() - t0:5.2f}s  shot={R.shot_at(T).info['key']}")
            thumbs.append(fr.resize((W // 3, H // 3), Image.LANCZOS))
        cols = min(4, len(thumbs))
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (W // 3 + 8), rows * (H // 3 + 8)), (40, 40, 40))
        for i, th in enumerate(thumbs):
            sheet.paste(th, ((i % cols) * (W // 3 + 8), (i // cols) * (H // 3 + 8)))
        name = os.environ.get("SHEET", "sheet")
        sheet.save(os.path.join(ROOT, "preview", name + ".png"))
    elif mode == "frame":
        R = get_R()
        T = float(sys.argv[2])
        R.frame(T).save(os.path.join(ROOT, "preview", "frame_%06.2f.png" % T))
    elif mode == "video":
        from multiprocessing import Pool
        tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
        n = int(math.ceil(tl["total"] * FPS))
        if len(sys.argv) > 3:
            n = min(n, int(float(sys.argv[3]) * FPS))
        start = int(float(sys.argv[2]) * FPS) if len(sys.argv) > 2 else 0
        segdir = os.path.join(ROOT, "segs")
        os.makedirs(segdir, exist_ok=True)
        step = 120
        tasks = [(f, min(f + step, n), os.path.join(segdir, "seg_%05d.mp4" % f)) for f in range(start, n, step)]
        t0 = time.time()
        with Pool(int(os.environ.get("JOBS", "12"))) as pool:
            for i, out in enumerate(pool.imap(render_range, tasks)):
                print(f"{i + 1}/{len(tasks)} {os.path.basename(out)}  {time.time() - t0:6.1f}s", flush=True)
        with open(os.path.join(segdir, "list.txt"), "w") as f:
            for _, _, out in tasks:
                f.write("file '%s'\n" % out.replace("\\", "/"))
        subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(segdir, "list.txt"),
                        "-c", "copy", os.path.join(ROOT, "video_sin_audio.mp4")], check=True)
        print("listo video_sin_audio.mp4", round(time.time() - t0, 1), "s")
    elif mode == "mux":
        out = sys.argv[2]
        subprocess.run([FF, "-y", "-loglevel", "error", "-i", os.path.join(ROOT, "video_sin_audio.mp4"), "-i", os.path.join(ROOT, sys.argv[3] if len(sys.argv) > 3 else "mezcla.wav"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest",
                        "-movflags", "+faststart", out], check=True)
        print("listo", out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
