#!/usr/bin/env python3
"""gen_bgm.py v3.0.0 — 明亮夏日垫乐：指弹拨弦 + 短贝斯 + 稀疏钟琴 + 很轻的沙锤 + 小房间混响。

为什么不用 v2（已移到 scripts/legacy/gen_bgm_v2.py）：
  (a) pluck_base=62+root_pc，拨弦比主调高一个全音（D 调弹成 E 五声，G# 撞 IV 和弦的 G）
  (b) 垫子是 D2/A1 纯正弦密集三和弦，发糊发闷
  (c) 和弦形状随机抽到 power/sus4，约一半小节没有三度
  (d) 10s 一个和弦、无律动、无混响、每小节淡到 0 → 听着阴郁

v3：中高音区、每小节一个和弦、带泛音的拨弦、不做整轨低通、只用大调/挂留和弦、
有轻律动、每 4 小节换一种织体、中间插「喘口气」段。

自检（任一失败都退出非零，不出文件）：
  1. 和弦相对根音不得含小三度，必须含大三度或挂四
  2. 所有拨弦/贝斯/钟琴音必须在主调大调音阶内

用法：
  python gen_bgm.py --seed 20260929 --dur 180 --out bgm.wav
  python gen_bgm.py --seed 7 --preset plain --dur 60 --out s7_plain.wav
  python gen_bgm.py --seed 7 --print-chords            # 只打印和弦表 JSON，不渲染
  python gen_bgm.py --seed 7 --style quiet --out q.wav  # 转调 legacy v2（不推荐）
每次新片换 seed；同一个 seed + 同一组参数可以完整复现（md5 相同）。
输出长度 = 按 --dur 取整后的小节数 + 约 4.5 秒尾音。
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

VERSION = "3.0.0"
HERE = Path(__file__).resolve().parent
LEGACY = HERE / "legacy" / "gen_bgm_v2.py"


def _ensure_numpy():
    try:
        import numpy  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("PVC_BGM_REEXEC"):
        sys.exit("gen_bgm.py: 换了解释器仍找不到 numpy，请先装 numpy。")
    os.environ["PVC_BGM_REEXEC"] = "1"
    cands = [os.environ.get("PVC_PYTHON"), "python3",
             "/opt/homebrew/bin/python3.11", "/usr/local/bin/python3"]
    me = os.path.realpath(sys.executable)
    for c in cands:
        if not c:
            continue
        p = shutil.which(c) or (c if os.path.isfile(c) else None)
        if not p or os.path.realpath(p) == me:
            continue
        try:
            if subprocess.run([p, "-c", "import numpy"], capture_output=True).returncode == 0:
                os.execv(p, [p] + sys.argv)
        except OSError:
            continue
    uv = shutil.which("uv") or os.path.expanduser("~/.hermes/bin/uv")
    if uv and os.path.isfile(uv):
        os.execv(uv, [uv, "run", "--with", "numpy", "python"] + sys.argv)
    sys.exit("gen_bgm.py: 找不到带 numpy 的 python（试过 $PVC_PYTHON / python3 / 3.11 / uv）。")


_ensure_numpy()
import numpy as np  # noqa: E402

SR = 48000
TAIL = 4.5
PEAK_DB = -3.0

KEY_OFFSET = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR = {0, 2, 4, 5, 7, 9, 11}

# 和弦名 -> (根音, 和弦音)，单位是相对主音的半音。只用大三和挂留色彩。
CHORDS = {
    "I":    (0,  [0, 4, 7, 14]),    # Iadd9
    "I6":   (0,  [0, 4, 7, 9]),
    "IV":   (5,  [5, 9, 12, 16]),   # IVmaj7
    "IV9":  (5,  [5, 9, 12, 19]),   # IVadd9
    "V":    (-5, [-5, -1, 2, 7]),
    "Vsus": (-5, [-5, 0, 2, 7]),    # Vsus4
}
PROGS = [
    ["I", "IV", "I", "V"],
    ["I", "V", "IV9", "I"],
    ["IV", "I", "Vsus", "V"],
    ["I", "I6", "IV", "V"],
    ["IV9", "V", "I", "I6"],
    ["I", "Vsus", "IV", "IV9"],
]
# 一小节 8 个八分音符位；数字 = 和弦音序号（0 最低），None = 休止
PATTERNS = [
    [0, None, 2, 1, 3, None, 2, 1],
    [0, 2, 1, 3, None, 2, 3, None],
    [0, None, 1, 2, None, 3, 2, None],
    [0, 3, None, 2, 1, None, 3, 2],
    [0, None, 2, None, 1, 3, None, 2],
]
PENTA = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24]  # 大调五声，两个八度

PRESETS = {
    "default": dict(key="D", bpm=100.0, density=0.85, reverb=0.35, bell=True, shaker=True),
    "plain":   dict(key="D", bpm=100.0, density=0.70, reverb=0.35, bell=False, shaker=False),
    "lively":  dict(key="E", bpm=108.0, density=0.85, reverb=0.30, bell=True, shaker=True),
}


def midi_hz(n):
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


def tonic(key):
    t = 60 + KEY_OFFSET[key]
    return t - 12 if t >= 66 else t  # 主音落在 G3..F4


# ---------------------------------------------------------------- 作曲

def make_motif(rng):
    """两小节的小旋律：3–5 个四分音符，第一拍必有，略往上走。"""
    k = int(rng.integers(3, 6))
    slots = [0] + sorted(int(s) for s in rng.choice(np.arange(1, 8), size=k - 1, replace=False))
    idx, notes = int(rng.integers(3, 6)), []
    for s in slots:
        notes.append((s, idx))
        idx = int(np.clip(idx + rng.choice([-1, 1, 1, 2, -2]), 2, 9))
    return notes


def compose(seed, key, bpm, dur, density, bell_on, shaker_on):
    rng = np.random.default_rng(seed)
    T = tonic(key)
    bar = 240.0 / bpm
    eighth = bar / 8
    n_bars = max(8, int(round(dur / bar)))
    n_phr = math.ceil(n_bars / 4)

    cycle = ["A", "B", "A", "B", "breath"]
    roles = ["intro"] + [cycle[(i - 1) % len(cycle)] for i in range(1, n_phr)]
    if n_phr > 2:
        roles[-1] = "A"  # 收尾那句轻一点
    drop = (1.0 - density) * 0.6

    events, bars = [], []

    def ev(kind, t, note, pan, gain, var=0):
        events.append((kind, float(t), None if note is None else int(note),
                       float(pan), float(gain), int(var)))

    last = None
    for p in range(n_phr):
        role = roles[p]
        last = int(rng.choice([i for i in range(len(PROGS)) if i != last]))
        prog = PROGS[last]
        pat = PATTERNS[int(rng.integers(len(PATTERNS)))]
        motif = make_motif(rng) if role == "B" else None

        for b in range(4):
            bi = p * 4 + b
            if bi >= n_bars:
                break
            tb = bi * bar
            final = bi == n_bars - 1
            name = "I" if final else prog[b]
            root, tones = CHORDS[name]
            voicing = sorted(T + x for x in tones)
            bars.append({"bar": bi, "t": round(tb, 3), "role": role, "chord": name,
                         "root": T + root, "midi": voicing})

            if final:  # 最后扫一下 I 和弦，让它自然响完
                for j, nt in enumerate(voicing + [voicing[1] + 12]):
                    ev("pluck", tb + j * 0.028, nt, 0.35 + 0.08 * j, 0.45, 1)
                ev("bass", tb, T - 12 + root, 0.5, 0.4)
                continue

            for slot, vi in enumerate(pat):  # 指弹拨弦
                if vi is None:
                    continue
                if role == "intro" and slot % 2:
                    continue
                if role == "breath" and slot not in (0, 3, 5):
                    continue
                if slot and rng.random() < drop:
                    continue
                t0 = tb + slot * eighth + (0.012 if slot % 2 else 0.0) + rng.normal(0, 0.005)
                vel = (0.75 if slot == 0 else 0.5) + 0.15 * rng.random()
                nt = voicing[min(vi, len(voicing) - 1)]
                ev("pluck", t0, nt, 0.38 + 0.08 * vi, vel * 0.5, 2 if role == "B" else 1)

            if role != "intro":  # 短拨贝斯，不长鸣
                bn = T - 12 + root
                ev("bass", tb + rng.normal(0, 0.004), bn, 0.5, 0.4)
                if role != "breath":
                    second = bn + (7 if rng.random() < 0.4 else 0)
                    ev("bass", tb + 4 * eighth, second, 0.5, 0.3)

            if role == "B" and shaker_on:
                for slot in (1, 3, 5, 7):
                    ev("shaker", tb + slot * eighth + 0.012, None, 0.72,
                       0.05 + 0.02 * rng.random())

            if motif and bell_on:  # 前两小节问，后两小节答（落回主音）
                use = motif if b < 2 else motif[:-1] + [(motif[-1][0], 5)]
                for s, idx in use:
                    if s // 4 == b % 2:
                        ev("bell", tb + (s % 4) * 2 * eighth + rng.normal(0, 0.004),
                           T + 12 + PENTA[idx], 0.62, 0.16)

    return {"T": T, "key": key, "bpm": bpm, "bar": bar, "n_bars": n_bars,
            "roles": roles, "bars": bars, "events": events}


def check_song(song):
    """两道自检。失败直接退出非零。返回检查过的音符数。"""
    for b in song["bars"]:
        rel = {(m - b["root"]) % 12 for m in b["midi"]}
        if 3 in rel:
            sys.exit(f"gen_bgm.py: 第 {b['bar']} 小节 {b['chord']} 含小三度 {b['midi']}，违反「不要小调」")
        if not (4 in rel or 5 in rel):
            sys.exit(f"gen_bgm.py: 第 {b['bar']} 小节 {b['chord']} 缺大三度/挂四 {b['midi']}")
    T, n = song["T"], 0
    for kind, t, note, *_ in song["events"]:
        if note is None:
            continue
        n += 1
        if (note - T) % 12 not in MAJOR:
            sys.exit(f"gen_bgm.py: {kind} 音 midi={note} @ {t:.2f}s 不在 {song['key']} 大调音阶内（跑调）")
    return n


# ---------------------------------------------------------------- 音色

class Synth:
    """向量化加法合成，按音高缓存。"""

    def __init__(self):
        self.cache = {}

    def pluck(self, note, bright):
        key = ("p", note, bright)
        if key not in self.cache:
            f = midi_hz(note)
            t = np.arange(int(2.4 * SR)) / SR
            y = np.zeros_like(t)
            roll = 0.55 + 0.15 * bright
            for k in range(1, 11):
                fk = f * k * (1 + 0.0003 * k * k)  # 轻微非谐，像真弦
                if fk > SR * 0.45:
                    break
                pick = abs(math.sin(math.pi * k * 0.2))  # 拨弦位置
                a = pick * roll ** (k - 1) / k
                y += a * np.exp(-(2.0 + 1.1 * k) * t) * np.sin(2 * np.pi * fk * t)
            y *= np.minimum(1.0, t / 0.002)
            self.cache[key] = y / np.max(np.abs(y))
        return self.cache[key]

    def bass(self, note):
        key = ("b", note)
        if key not in self.cache:
            f = midi_hz(note)
            t = np.arange(int(1.8 * SR)) / SR
            y = np.zeros_like(t)
            for k, a in enumerate((1.0, 0.4, 0.18, 0.08), start=1):
                y += a * np.exp(-(1.8 + 0.9 * k) * t) * np.sin(2 * np.pi * f * k * t)
            y *= np.minimum(1.0, t / 0.004)
            self.cache[key] = y / np.max(np.abs(y))
        return self.cache[key]

    def bell(self, note):
        key = ("g", note)
        if key not in self.cache:
            f = midi_hz(note)
            t = np.arange(int(2.5 * SR)) / SR
            y = np.zeros_like(t)
            for ratio, a, dec in ((1, 1, 1.6), (2.76, 0.3, 4), (5.4, 0.1, 7), (8.93, 0.04, 11)):
                if f * ratio < SR * 0.45:
                    y += a * np.exp(-dec * t) * np.sin(2 * np.pi * f * ratio * t)
            y *= np.minimum(1.0, t / 0.001)
            self.cache[key] = y / np.max(np.abs(y))
        return self.cache[key]


def shaker(rng):
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    x = np.diff(rng.standard_normal(n + 1))  # 粗高通，只留沙沙声
    return x * np.minimum(1.0, t / 0.004) * np.exp(-t / 0.018) * 0.5


def place(L, R, sig, t0, pan, gain):
    s = int(round(t0 * SR))
    if s < 0:
        sig, s = sig[-s:], 0
    e = min(len(L), s + len(sig))
    if e <= s:
        return
    seg = sig[: e - s] * gain
    L[s:e] += seg * math.cos(pan * math.pi / 2)
    R[s:e] += seg * math.sin(pan * math.pi / 2)


# ---------------------------------------------------------------- 混响（分块向量化）

def _comb(x, d, g):
    y = x.copy()
    for s in range(d, len(x), d):
        e = min(s + d, len(x))
        y[s:e] += g * y[s - d:e - d]
    return y


def _allpass(x, d, g):
    y = np.empty_like(x)
    y[:d] = -g * x[:d]
    for s in range(d, len(x), d):
        e = min(s + d, len(x))
        y[s:e] = -g * x[s:e] + x[s - d:e - d] + g * y[s - d:e - d]
    return y


def reverb(x, spread_ms, amount):
    """小房间混响（RT 约 0.8s）。只让湿声柔一点，干声不做低通。"""
    x = np.convolve(x, np.ones(4) / 4, mode="same")
    wet = np.zeros_like(x)
    for ms, g in ((29.7, 0.78), (37.1, 0.76), (41.1, 0.74), (43.7, 0.72)):
        wet += _comb(x, int((ms + spread_ms) * SR / 1000), g)
    for ms in (5.0, 3.1):
        wet = _allpass(wet, int((ms + spread_ms * 0.1) * SR / 1000), 0.6)
    return wet / 4 * amount


# ---------------------------------------------------------------- 渲染 / 输出

def render(song, seed, reverb_amt):
    syn = Synth()
    nrng = np.random.default_rng(seed + 7919)  # 只给沙锤噪声用，不影响作曲
    N = int((song["n_bars"] * song["bar"] + TAIL) * SR)
    L, R = np.zeros(N), np.zeros(N)
    for kind, t, note, pan, gain, var in song["events"]:
        if kind == "pluck":
            sig = syn.pluck(note, var)
        elif kind == "bass":
            sig = syn.bass(note)
        elif kind == "bell":
            sig = syn.bell(note)
        else:
            sig = shaker(nrng)
        place(L, R, sig, t, pan, gain)

    if reverb_amt > 0:
        L = L + reverb(L, 0.0, reverb_amt)
        R = R + reverb(R, 0.9, reverb_amt)
    fi, fo = int(1.0 * SR), int(3.5 * SR)
    for ch in (L, R):
        ch[:fi] *= np.linspace(0, 1, fi)
        ch[-fo:] *= np.linspace(1, 0, fo)
    peak = max(float(np.max(np.abs(L))), float(np.max(np.abs(R))), 1e-9)
    g = 10 ** (PEAK_DB / 20) / math.tanh(1.1)
    L = np.tanh(1.1 * L / peak) * g
    R = np.tanh(1.1 * R / peak) * g
    return L, R


def write_wav(path, L, R):
    pcm = (np.clip(np.stack([L, R], axis=1), -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def run_legacy(a):
    if not LEGACY.is_file():
        sys.exit(f"gen_bgm.py: --style quiet 需要 {LEGACY}，文件不存在。")
    print("gen_bgm.py: 警告：quiet 是 v2 旧垫乐，被评价为「诡异/阴郁」，"
          "只在他明确要安静到发闷时用。", file=sys.stderr)
    out = a.out or f"bgm_quiet_s{a.seed}.wav"
    cmd = [sys.executable, str(LEGACY), "--style", "quiet", "--seed", str(a.seed),
           "--dur", str(a.dur), "--out", out, "--key", (a.key or "D").upper(), "--bar-gap", "off"]
    os.execv(sys.executable, cmd)


def main():
    ap = argparse.ArgumentParser(
        description=f"明亮夏日垫乐 v{VERSION}（16-bit 48kHz 立体声，峰值约 −3 dBFS）",
        epilog="预设：default（指弹+钟琴+沙锤）/ plain（只有吉他和贝斯，稀一点）/ "
               "lively（E 调、108 BPM）。单独给的参数会覆盖预设。每次新片换 seed。",
    )
    ap.add_argument("--seed", type=int, required=True, help="必填；同 seed 同参数可复现")
    ap.add_argument("--dur", type=float, default=180.0, help="秒，按整小节取整，另加约 4.5s 尾音")
    ap.add_argument("--out", default=None, help="输出 wav（用 ASCII 文件名）")
    ap.add_argument("--style", choices=["bright", "quiet"], default="bright",
                    help="bright = v3（默认）；quiet = 转调 legacy v2，不推荐")
    ap.add_argument("--preset", choices=list(PRESETS), default="default")
    ap.add_argument("--key", default=None, help=f"调：{'/'.join(KEY_OFFSET)}")
    ap.add_argument("--bpm", type=float, default=None, help="建议 88–112")
    ap.add_argument("--density", type=float, default=None, help="0–1，越小越稀")
    ap.add_argument("--reverb", type=float, default=None, help="0–1")
    ap.add_argument("--bell", action=argparse.BooleanOptionalAction, default=None, help="钟琴小旋律")
    ap.add_argument("--shaker", action=argparse.BooleanOptionalAction, default=None, help="沙锤")
    ap.add_argument("--print-chords", action="store_true",
                    help="只作曲 + 自检，打印和弦表 JSON（MIDI 整数）后退出，不渲染")
    ap.add_argument("--version", action="version", version=VERSION)
    a = ap.parse_args()

    if a.style == "quiet":
        run_legacy(a)

    for k, v in PRESETS[a.preset].items():
        if getattr(a, k) is None:
            setattr(a, k, v)
    a.key = a.key.upper()
    if a.key not in KEY_OFFSET:
        sys.exit(f"gen_bgm.py: 不支持的调 {a.key}（可用 {'/'.join(KEY_OFFSET)}）")
    if a.dur <= 0:
        sys.exit("gen_bgm.py: --dur 必须 > 0")
    if not 60 <= a.bpm <= 140:
        sys.exit("gen_bgm.py: --bpm 应在 60–140 之间")
    if not 0 <= a.density <= 1 or not 0 <= a.reverb <= 1:
        sys.exit("gen_bgm.py: --density / --reverb 应在 0–1 之间")

    t0 = time.time()
    song = compose(a.seed, a.key, a.bpm, a.dur, a.density, a.bell, a.shaker)
    n_checked = check_song(song)

    if a.print_chords:
        print(json.dumps({
            "version": VERSION, "seed": a.seed, "preset": a.preset, "key": a.key,
            "tonic_midi": song["T"], "bpm": a.bpm, "bar_sec": round(song["bar"], 4),
            "n_bars": song["n_bars"], "roles": song["roles"], "bars": song["bars"],
            "notes_checked": n_checked, "scale_ok": True,
        }, ensure_ascii=False))
        return

    out = a.out or f"bgm_{a.preset}_s{a.seed}.wav"
    if not out.isascii():
        print(f"gen_bgm.py: 警告：输出文件名非 ASCII（{out}），发 Discord 前要改名。", file=sys.stderr)
    L, R = render(song, a.seed, a.reverb)
    write_wav(out, L, R)
    if os.path.getsize(out) == 0:
        sys.exit(f"gen_bgm.py: 输出为空 {out}")
    sec = len(L) / SR
    print(f"wrote {out}  {sec:.1f}s  v{VERSION} preset={a.preset} seed={a.seed} key={a.key} "
          f"bpm={a.bpm:g} density={a.density:g} reverb={a.reverb:g} "
          f"bell={'on' if a.bell else 'off'} shaker={'on' if a.shaker else 'off'}  "
          f"bars={song['n_bars']} notes={n_checked}  render {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

