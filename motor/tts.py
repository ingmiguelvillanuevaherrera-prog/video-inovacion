import sys, os, json, asyncio, subprocess, wave
sys.stdout.reconfigure(encoding="utf-8")
import edge_tts, imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from narracion import PARTS
try:
    from narracion import VOICES
except ImportError:
    VOICES = {}
VOICE = sys.argv[1] if len(sys.argv) > 1 else "es-MX-JorgeNeural"
RATE = sys.argv[2] if len(sys.argv) > 2 else "+8%"
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(HERE, "audio")
os.makedirs(OUT, exist_ok=True)

async def one(pid, text):
    words = []
    mp3 = os.path.join(OUT, pid + ".mp3")
    comm = edge_tts.Communicate(text, VOICES.get(pid, VOICE), rate=RATE, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                s = ch["offset"] / 1e7; d = ch["duration"] / 1e7
                words.append({"t": ch["text"], "s": round(s, 3), "e": round(s + d, 3)})
    wav = os.path.join(OUT, pid + ".wav")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", mp3, "-ar", "44100", "-ac", "1", wav], check=True)
    with wave.open(wav) as w:
        dur = w.getnframes() / w.getframerate()
    json.dump({"id": pid, "dur": dur, "words": words}, open(os.path.join(OUT, pid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return pid, dur, len(words)

async def main():
    tot = 0
    for pid, text in PARTS:
        pid, dur, nw = await one(pid, text)
        tot += dur
        print(f"{pid:4s} {dur:6.2f}s  words={nw}")
    print("TOTAL voz", round(tot, 1), "s")
asyncio.run(main())
