#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_bgm_guitar.py v1.0.0 — 木吉他 BGM：程序作曲 → MIDI → fluidsynth + SoundFont 采样渲染
personal-vlog-cut 专用。与 gen_bgm.py（合成器 v3）完全独立，不影响其输出。

依赖：numpy（仅渲染时）；fluidsynth 2.x；GM SoundFont（默认 FluidR3_GM.sf2，MIT）
SoundFont：给了 --sf2 就只用它（不存在即报错退出 2）；否则按 PVC_SF2 > SF2_CANDIDATES 查找

用法：
  python gen_bgm_guitar.py --seed 1 --dur 60 --out a.wav                  # 默认：指弹/轻扫交替
  python gen_bgm_guitar.py --seed 1 --dur 60 --out a.wav --pattern finger # 全程指弹
  python gen_bgm_guitar.py --seed 1 --dur 60 --out a.wav --guitar nylon   # 尼龙弦
  python gen_bgm_guitar.py --seed 1 --dur 60 --print-chords               # 只作曲+自检（无需 numpy/fluidsynth）
  python gen_bgm_guitar.py --seed 1 --dur 60 --print-chords --midi-out a.mid

退出码：0 成功；2 参数/依赖错误；3 自检失败；4 渲染失败
"""
import argparse
import json
import math
import os
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

VERSION = "1.0.0"
SR = 48000
PEAK = 0.70          # ≈ -3.1 dBFS
PPQ = 480
LEAD = 0.15          # 开头留白（秒）
TAIL = 3.0           # 结尾余音（秒）

# 标准调弦，索引 0=6弦(E2) … 5=1弦(E4)
OPEN = [40, 45, 50, 55, 59, 64]

# D 调开放和弦（品格，6→1 弦，None=不弹）。--key 相当于变调夹整体移调。
SHAPES = {
    "D":     [None, None, 0, 2, 3, 2],
    "D/F#":  [2, None, 0, 2, 3, 2],
    "Dmaj7": [None, None, 0, 2, 2, 2],
    "D6":    [None, None, 0, 2, 0, 2],
    "G":     [3, 2, 0, 0, 0, 3],
    "G/B":   [None, 2, 0, 0, 3, 3],
    "Gadd9": [3, 2, 0, 2, 0, 3],
    "A":     [None, 0, 2, 2, 2, 0],
    "A/C#":  [None, 4, 2, 2, 2, 0],
    "Asus4": [None, 0, 2, 2, 3, 0],
}
ROOT_PC = {"D": 2, "D/F#": 2, "Dmaj7": 2, "D6": 2,
           "G": 7, "G/B": 7, "Gadd9": 7,
           "A": 9, "A/C#": 9, "Asus4": 9}
KEY_OFFSET = {"C": -2, "C#": -1, "D": 0, "Eb": 1, "E": 2, "F": 3, "F#": 4, "G": 5}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
GUITAR_PROGRAM = {"steel": 25, "nylon": 24}   # GM：24 尼龙，25 钢弦

# 4 小节一句；每小节为 [(和弦, 拍数), ...]
PROGS = [
    [[("D", 4)], [("Gadd9", 4)], [("D", 4)], [("Asus4", 2), ("A", 2)]],
    [[("D", 4)], [("D/F#", 4)], [("G", 4)], [("A", 4)]],
    [[("G", 4)], [("D/F#", 4)], [("Gadd9", 4)], [("Asus4", 2), ("A", 2)]],
    [[("Dmaj7", 4)], [("G/B", 4)], [("A/C#", 2), ("A", 2)], [("D", 4)]],
    [[("D6", 4)], [("Gadd9", 4)], [("D", 2), ("A/C#", 2)], [("G", 2), ("A", 2)]],
]
PENULT = [("Asus4", 2), ("A", 2)]
ENDING = "D"

SF2_CANDIDATES = [
    "/usr/share/sounds/sf2/FluidR3_GM.sf2",
    "/usr/share/soundfonts/FluidR3_GM.sf2",
    "/opt/homebrew/share/soundfonts/FluidR3_GM.sf2",
    "/usr/local/share/soundfonts/FluidR3_GM.sf2",
    "~/.local/share/soundfonts/FluidR3_GM.sf2",
    "~/Library/Audio/Sounds/Banks/FluidR3_GM.sf2",
]


def die(msg, code=2):
    print(f"[gen_bgm_guitar] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg):
    print(f"[gen_bgm_guitar] WARN: {msg}", file=sys.stderr)


def voicing(name, shift):
    """[(string_idx, midi)]，低音弦在前"""
    return [(i, OPEN[i] + f + shift) for i, f in enumerate(SHAPES[name]) if f is not None]


# ---------------------------------------------------------------- 作曲
def plan_bars(dur, bpm, seed, pattern):
    rng = random.Random(seed)
    bar = 240.0 / bpm
    n = int((dur - LEAD - TAIL) // bar)
    if n < 3:
        die(f"--dur 太短：当前 BPM 下至少需要 {LEAD + TAIL + 3 * bar:.1f}s")
    body = n - 1
    chords = []
    while len(chords) < body:
        chords.extend(rng.choice(PROGS))
    chords = chords[:body]
    chords[-1] = list(PENULT)
    bars = []
    for i, segs in enumerate(chords):
        if i == 0 or i % 8 == 7:
            kind = "breath"
        elif pattern == "finger":
            kind = "finger"
        elif pattern == "strum":
            kind = "strum"
        else:
            kind = "finger" if (i // 8) % 2 == 0 else "strum"
        bars.append({"bar": i, "kind": kind, "segs": [list(s) for s in segs]})
    bars.append({"bar": body, "kind": "ending", "segs": [[ENDING, 4]]})
    return bars


def self_check(bars, shift):
    scale = {(2 + shift + d) % 12 for d in MAJOR}
    errs = []
    for b in bars:
        for name, _ in b["segs"]:
            notes = [n for _, n in voicing(name, shift)]
            root = (ROOT_PC[name] + shift) % 12
            rel = {(n - root) % 12 for n in notes}
            if 3 in rel:
                errs.append(f"bar {b['bar']} {name}: 含小三度")
            if 4 not in rel and 5 not in rel:
                errs.append(f"bar {b['bar']} {name}: 无大三度也非 sus4")
            for n in notes:
                if n % 12 not in scale:
                    errs.append(f"bar {b['bar']} {name}: MIDI {n} 不在大调音阶内")
    return errs


# ---------------------------------------------------------------- 演奏
class Perf:
    def __init__(self, seed, bpm):
        self.rng = random.Random(seed * 7919 + 17)
        self.beat = 60.0 / bpm
        self.notes = []          # [on, off, ch(=弦), pitch, vel]

    def hum(self, t, sd=0.006, lim=0.015):
        return t + max(-lim, min(lim, self.rng.gauss(0.0, sd)))

    def play(self, t, string, pitch, vel):
        vel = int(max(20, min(110, vel + self.rng.randint(-6, 6))))
        self.notes.append([max(0.0, t), math.inf, string, pitch, vel])

    def damp_all(self, t):
        for n in self.notes:
            if n[1] == math.inf:
                n[1] = t


def pick_alt(thumb, root):
    for s, n in thumb[1:]:
        if (n - root) % 12 in (0, 7):
            return (s, n)
    return thumb[1] if len(thumb) > 1 else thumb[0]


def travis(p, t0, beats, v, root, dens, accent):
    thumb = [x for x in v if x[0] <= 3]
    bass = thumb[0]
    alt = pick_alt(thumb, root)
    tre = [x for x in v if x[0] >= 3 and x != alt]
    if len(tre) < 2:
        tre = v[-2:]
    fill = {1: tre[-2], 3: tre[-1], 5: (tre[0] if len(tre) >= 3 else tre[-2]), 7: tre[-1]}
    e = p.beat / 2
    for k in range(int(beats * 2)):
        t = t0 + k * e
        slot = k % 8
        if slot in (0, 4):
            p.play(p.hum(t), *bass, 70 + (8 if (slot == 0 and accent) else 0))
            if slot == 0:
                p.play(p.hum(t), *tre[-1], 62)
        elif slot in (2, 6):
            p.play(p.hum(t), *alt, 62)
        elif p.rng.random() < dens:
            p.play(p.hum(t), *fill[slot], 56)


def strum(p, t0, beats, v, dens, accent):
    pat = "D.DU.UDU"
    e = p.beat / 2
    for k in range(int(beats * 2)):
        c = pat[k % 8]
        if c == ".":
            continue
        t = p.hum(t0 + k * e, 0.005, 0.012)
        if c == "D":
            spread = p.rng.uniform(0.009, 0.015)
            base = 60 + (6 if (k % 8 == 0 and accent) else 0)
            for i, (s, n) in enumerate(v):
                p.play(t + i * spread, s, n, base - i)
        else:
            if p.rng.random() > dens:
                continue
            spread = p.rng.uniform(0.007, 0.011)
            for i, (s, n) in enumerate(v[-3:][::-1]):
                p.play(t + i * spread, s, n, 46 - 2 * i)


def breath(p, t0, beats, v, slow=0.075, vel=56, extra=True):
    t = p.hum(t0)
    for i, (s, n) in enumerate(v):
        p.play(t + i * slow, s, n, vel - i)
    if extra and beats >= 4 and p.rng.random() < 0.6:
        s, n = v[-1]
        p.play(p.hum(t0 + 2.5 * p.beat), s, n, vel - 8)


def perform(bars, bpm, shift, dens, seed, dur):
    p = Perf(seed, bpm)
    bar_sec = 4 * p.beat
    for b in bars:
        pos = 0.0
        for name, beats in b["segs"]:
            t0 = LEAD + b["bar"] * bar_sec + pos * p.beat
            if t0 > LEAD:
                p.damp_all(t0 + 0.03)        # 换和弦：旧余音轻微重叠后闷掉
            v = voicing(name, shift)
            root = (ROOT_PC[name] + shift) % 12
            accent = pos == 0
            kind = b["kind"]
            if kind == "finger":
                travis(p, t0, beats, v, root, dens, accent)
            elif kind == "strum":
                strum(p, t0, beats, v, dens, accent)
            elif kind == "breath":
                breath(p, t0, beats, v)
            else:
                breath(p, t0, beats, v, slow=0.11, vel=58, extra=False)
            pos += beats
    end = dur - 0.1
    p.damp_all(end)
    fix_overlaps(p.notes, end)
    return p.notes


def fix_overlaps(notes, end):
    """一根弦同一时刻只能响一个音：同通道后音截断前音"""
    by = {}
    for n in notes:
        n[1] = min(n[1], end)
        by.setdefault(n[2], []).append(n)
    for lst in by.values():
        lst.sort(key=lambda n: n[0])
        for a, b in zip(lst, lst[1:]):
            if a[1] > b[0] - 0.004:
                a[1] = b[0] - 0.004
    for n in notes:
        if n[1] <= n[0]:
            n[1] = n[0] + 0.005


# ---------------------------------------------------------------- MIDI
def vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def write_midi(path, notes, bpm, program, reverb_send, end_sec):
    tps = PPQ * bpm / 60.0

    def tick(s):
        return max(0, int(round(s * tps)))

    ev = [(0, 0, b"\xff\x51\x03" + struct.pack(">I", int(round(60_000_000 / bpm)))[1:])]
    for ch in range(6):
        pan = 50 + ch * 6                # 6 弦略偏左 → 1 弦略偏右
        for d in (bytes([0xC0 | ch, program]),
                  bytes([0xB0 | ch, 7, 100]),
                  bytes([0xB0 | ch, 10, pan]),
                  bytes([0xB0 | ch, 91, reverb_send]),
                  bytes([0xB0 | ch, 93, 0])):
            ev.append((0, 0, d))
    for on, off, ch, pitch, vel in notes:
        a, b = tick(on), tick(off)
        if b <= a:
            b = a + 1
        ev.append((a, 2, bytes([0x90 | ch, pitch, vel])))
        ev.append((b, 1, bytes([0x80 | ch, pitch, 0])))
    ev.sort(key=lambda e: (e[0], e[1]))
    body = bytearray()
    last = 0
    for t, _, d in ev:
        body += vlq(t - last) + d
        last = t
    end = max(last, tick(end_sec))
    body += vlq(end - last) + b"\xff\x2f\x00"
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 0, 1, PPQ))
        f.write(b"MTrk" + struct.pack(">I", len(body)) + bytes(body))


# ---------------------------------------------------------------- 渲染
def find_sf2(arg):
    if arg:
        p = Path(arg).expanduser()
        if p.is_file():
            return p
        die(f"--sf2 指定的 SoundFont 不存在：{arg}（显式指定时不回退）")
    cands = []
    if os.environ.get("PVC_SF2"):
        cands.append(os.environ["PVC_SF2"])
    cands += SF2_CANDIDATES
    cands.append(str(Path(__file__).resolve().parent.parent / "assets" / "sf2" / "FluidR3_GM.sf2"))
    for c in cands:
        p = Path(c).expanduser()
        if p.is_file():
            return p
    die("找不到 SoundFont：请用 --sf2 或环境变量 PVC_SF2 指定 FluidR3_GM.sf2 路径\n已尝试：\n  "
        + "\n  ".join(cands))


def render(fs_bin, sf2, mid, wav_tmp, gain, reverb):
    cmd = [fs_bin, "-ni", "-g", f"{gain:.3f}", "-r", str(SR),
           "-o", "synth.chorus.active=0",
           "-o", "synth.reverb.active=1",
           "-o", f"synth.reverb.room-size={0.2 + 0.4 * reverb:.3f}",
           "-o", "synth.reverb.damp=0.35",
           "-o", "synth.reverb.width=0.9",
           "-T", "wav", "-O", "s16",
           "-F", str(wav_tmp), str(sf2), str(mid)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not wav_tmp.exists() or wav_tmp.stat().st_size < 1000:
        die(f"fluidsynth 渲染失败 (rc={r.returncode})\nCMD: {' '.join(cmd)}\n"
            f"STDERR: {r.stderr[-2000:]}\nSTDOUT: {r.stdout[-1000:]}", 4)


def load_wav(path):
    import numpy as np
    with wave.open(str(path), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        die(f"fluidsynth 输出位深 {sw * 8}bit，预期 16bit", 4)
    x = np.frombuffer(raw, dtype="<i2").astype(np.float64).reshape(-1, ch) / 32768.0
    if ch == 1:
        x = np.repeat(x, 2, axis=1)
    x = x[:, :2]
    if sr != SR:
        warn(f"fluidsynth 输出 {sr} Hz，线性重采样到 {SR} Hz")
        t_old = np.arange(len(x)) / sr
        t_new = np.arange(int(len(x) * SR / sr)) / SR
        x = np.stack([np.interp(t_new, t_old, x[:, c]) for c in range(2)], axis=1)
    return x


def finalize(x, dur, out):
    import numpy as np
    if np.max(np.abs(x)) >= 0.999:
        warn("fluidsynth 输出疑似削波（峰值≈满刻度），请降低 --gain")
    N = int(round(dur * SR))
    y = np.zeros((N, 2))
    m = min(N, len(x))
    y[:m] = x[:m]
    fi = int(0.02 * SR)
    y[:fi] *= np.linspace(0.0, 1.0, fi)[:, None]
    fo = int(2.0 * SR)
    y[-fo:] *= (0.5 * (1 + np.cos(np.linspace(0.0, np.pi, fo))))[:, None]
    pk = float(np.max(np.abs(y)))
    if pk < 1e-6:
        die("渲染结果无声：检查 SoundFont 是否为 GM 音色库、program 是否存在", 4)
    y *= PEAK / pk
    y16 = np.clip(np.round(y * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y16.tobytes())


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=f"木吉他 BGM（SoundFont 采样）v{VERSION}")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dur", type=float, default=60.0, help="秒")
    ap.add_argument("--out", help="输出 wav（16bit/48k/立体声）")
    ap.add_argument("--key", default="D", choices=list(KEY_OFFSET), help="相当于变调夹移调")
    ap.add_argument("--bpm", type=float, default=96.0)
    ap.add_argument("--density", type=float, default=0.85, help="高音填充/上扫保留概率 0–1")
    ap.add_argument("--pattern", default="mix", choices=["mix", "finger", "strum"])
    ap.add_argument("--guitar", default="steel", choices=list(GUITAR_PROGRAM))
    ap.add_argument("--reverb", type=float, default=0.35, help="0–1")
    ap.add_argument("--gain", type=float, default=0.4, help="fluidsynth 增益（最终会归一化）")
    ap.add_argument("--sf2", help="SoundFont 路径")
    ap.add_argument("--fluidsynth", default="fluidsynth", help="fluidsynth 可执行文件")
    ap.add_argument("--midi-out", help="另存 MIDI")
    ap.add_argument("--print-chords", action="store_true", help="输出每小节和弦 JSON 并退出（不渲染）")
    ap.add_argument("--version", action="version", version=VERSION)
    a = ap.parse_args()

    if not (0 < a.density <= 1):
        die("--density 需在 (0, 1]")
    if not (0 <= a.reverb <= 1):
        die("--reverb 需在 [0, 1]")
    if not (60 <= a.bpm <= 130):
        die("--bpm 需在 60–130")
    if not (0 < a.dur <= 900):
        die("--dur 需在 (0, 900]")
    if not a.print_chords and not a.out:
        die("需要 --out（或使用 --print-chords）")

    shift = KEY_OFFSET[a.key]
    bars = plan_bars(a.dur, a.bpm, a.seed, a.pattern)
    errs = self_check(bars, shift)
    if errs:
        die("和弦自检失败：\n  " + "\n  ".join(errs), 3)
    notes = perform(bars, a.bpm, shift, a.density, a.seed, a.dur)
    scale = {(2 + shift + d) % 12 for d in MAJOR}
    bad = [n for n in notes if n[3] % 12 not in scale]
    if bad:
        die(f"演奏自检失败：{len(bad)} 个音不在大调音阶内", 3)

    program = GUITAR_PROGRAM[a.guitar]
    send = int(20 + 70 * a.reverb)

    if a.print_chords:
        out = [{"bar": b["bar"], "kind": b["kind"],
                "chords": [{"name": nm, "beats": bt,
                            "midi": [n for _, n in voicing(nm, shift)]} for nm, bt in b["segs"]]}
               for b in bars]
        print(json.dumps({"version": VERSION, "seed": a.seed, "key": a.key, "bpm": a.bpm,
                          "pattern": a.pattern, "notes": len(notes), "bars": out},
                         ensure_ascii=False, indent=1))
        if a.midi_out:
            write_midi(a.midi_out, notes, a.bpm, program, send, a.dur)
        return

    fs_bin = shutil.which(a.fluidsynth) or (a.fluidsynth if Path(a.fluidsynth).is_file() else None)
    if not fs_bin:
        die(f"找不到 fluidsynth 可执行文件：{a.fluidsynth}")
    sf2 = find_sf2(a.sf2)
    try:
        import numpy  # noqa: F401
    except ImportError:
        die("缺少 numpy：请用与 gen_bgm.py 相同的 Python（Hermes venv）运行")

    t_start = time.time()
    with tempfile.TemporaryDirectory() as td:
        mid = Path(a.midi_out) if a.midi_out else Path(td) / "bgm.mid"
        write_midi(mid, notes, a.bpm, program, send, a.dur)
        wav_tmp = Path(td) / "raw.wav"
        render(fs_bin, sf2, mid, wav_tmp, a.gain, a.reverb)
        x = load_wav(wav_tmp)
    finalize(x, a.dur, a.out)
    print(f"[gen_bgm_guitar] OK out={a.out} bars={len(bars)} notes={len(notes)} "
          f"guitar={a.guitar} pattern={a.pattern} key={a.key} bpm={a.bpm:g} "
          f"render={time.time() - t_start:.2f}s sf2={sf2}", file=sys.stderr)


if __name__ == "__main__":
    main()
