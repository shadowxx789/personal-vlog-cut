#!/usr/bin/env python3
"""gen_bgm.py — 生成原创垫乐（bright 大调稀疏拨弦 / quiet 闷垫）。

v2.0.0：seed 真正生效；只用大调 I/IV/V 走向（无小三和弦）；bright 不用 IIR、
不加厚低音（旧版「呜呜」来源）；48kHz 与混音链一致；峰值约 −3 dBFS。
性能：150 秒 wav ≤ 10 秒（numpy 矢量化）。

quiet 模式被评价为「诡异」，只在他明确要安静到发闷时用。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

def _ensure_numpy():
    try:
        import numpy  # noqa: F401
        return
    except ImportError:
        pass
    candidates = []
    if os.environ.get("PVC_PYTHON"):
        candidates.append(os.environ["PVC_PYTHON"])
    candidates += ["python3", "/opt/homebrew/bin/python3.11", "/usr/local/bin/python3"]
    for cand in candidates:
        path = shutil.which(cand) or (cand if os.path.isfile(cand) else None)
        if not path:
            continue
        try:
            out = subprocess.run([path, "-c", "import numpy"], capture_output=True)
            if out.returncode == 0:
                os.execv(path, [path] + sys.argv)
        except OSError:
            continue
    uv = shutil.which("uv") or os.path.expanduser("~/.hermes/bin/uv")
    if uv and os.path.isfile(uv):
        os.execv(uv, [uv, "run", "--with", "numpy", "python"] + sys.argv)
    sys.exit("gen_bgm.py: 找不到带 numpy 的 python（试过 $PVC_PYTHON/python3/3.11/uv）。请先装 numpy。")

_ensure_numpy()
import numpy as np  # noqa: E402

SR = 48000
PEAK = 0.7  # 约 −3 dBFS

KEY_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# 和弦形状（相对根音半音）。只用 I/IV/V 与挂留/加六变体——不含小三度。
SHAPES = {
    "triad": [0, 4, 7],
    "sus4": [0, 5, 7],
    "add6": [0, 4, 7, 9],
    "power": [0, 7, 12],
}
# 走向（罗马级数）。只用 I/IV/V。
PROGS = [
    ["I", "V", "IV", "I"],
    ["I", "IV", "V", "IV"],
    ["I", "I", "IV", "V"],
    ["I", "V", "I", "IV"],
    ["I", "IV", "I", "V"],
]
DEG_ROOT = {"I": 0, "IV": 5, "V": 7}


def midi(n):
    return 440.0 * (2.0 ** ((n - 69) / 12.0))


def make_chords(seed, key, n_bars):
    """返回 (chord_midi_lists, progression_labels)。同 seed 完整复现。"""
    rng = np.random.default_rng(seed)
    root_pc = KEY_PC[key.upper()]
    base = 36 + root_pc  # C2 起
    prog = PROGS[int(rng.integers(len(PROGS)))]
    shape_names = list(SHAPES)
    chords, labels = [], []
    for i in range(n_bars):
        deg = prog[i % len(prog)]
        shape = shape_names[int(rng.integers(len(shape_names)))]
        root = base + DEG_ROOT[deg]
        if deg == "V":
            root -= 12 if root > base + 4 else 0
        chords.append([midi(root + iv) for iv in SHAPES[shape]])
        labels.append(f"{deg}:{shape}")
    return chords, labels


def _window(n, fade_in, fade_out):
    w = np.ones(n)
    fi = min(int(fade_in * SR), n // 2)
    fo = min(int(fade_out * SR), n // 2)
    if fi > 0:
        w[:fi] = np.linspace(0.0, 1.0, fi)
    if fo > 0:
        w[-fo:] = np.linspace(1.0, 0.0, fo)
    return w


def _pluck(t_arr, f, amp, decay):
    e = np.exp(-decay * t_arr)
    atk = int(0.012 * SR)
    if atk and atk < len(e):
        e[:atk] *= np.linspace(0.0, 1.0, atk)
    return amp * e * (
        np.sin(2 * np.pi * f * t_arr)
        + 0.12 * np.exp(-4 * t_arr) * np.sin(4 * np.pi * f * t_arr)
    )


def _render(chords, seed, dur, style, bar, bar_gap, bass, key):
    rng = np.random.default_rng(seed + 1)
    n = int(dur * SR)
    left = np.zeros(n)
    right = np.zeros(n)
    n_bars = int(np.ceil(dur / bar)) + 1
    xfade = 1.5

    for i in range(n_bars):
        ch = chords[i % len(chords)]
        start = int(i * bar * SR)
        if bar_gap == "on":
            seg_len = int((bar + xfade) * SR)
            win = _window(seg_len, xfade, xfade)
        else:
            seg_len = int(bar * SR)
            win = _window(seg_len, 1.2, 1.4)
        tt = np.arange(seg_len) / SR
        seg_l = np.zeros(seg_len)
        seg_r = np.zeros(seg_len)
        for k, f in enumerate(ch):
            amp = (0.05 if k < 2 else 0.032) * win
            if style == "quiet":
                amp = amp * 1.6
            seg_l += amp * np.sin(2 * np.pi * f * tt)
            seg_r += amp * np.sin(2 * np.pi * f * tt + 0.03)
        if style == "quiet":  # 轻 detune + hiss（诡异口味道具，仅 quiet）
            det = 0.0018 * np.sin(2 * np.pi * 0.07 * tt + i)
            seg_l += 0.02 * win * np.sin(2 * np.pi * ch[0] * (1 + det) * tt)
            seg_r += 0.02 * win * np.sin(2 * np.pi * ch[0] * (1 - det) * tt)
        if bass == "on":
            b = 0.0225 * win * np.sin(2 * np.pi * ch[0] * tt)  # 旧版一半音量
            seg_l += b
            seg_r += b
        end = min(n, start + seg_len)
        if start >= n:
            break
        sl = seg_l[: end - start]
        sr_ = seg_r[: end - start]
        left[start:end] += sl
        right[start:end] += sr_

    # 拨弦：五声音阶选音 + 时间 ±0.3s 抖动 + 声像微抖
    pent = [0, 2, 4, 7, 9, 12]
    root_pc = KEY_PC[key.upper()]
    pluck_base = 62 + root_pc
    n_pluck_per_bar = 1 if style == "quiet" else 2
    for i in range(n_bars):
        for j in range(n_pluck_per_bar):
            t0 = i * bar + (0.9 + j * 4.6) + float(rng.uniform(-0.3, 0.3))
            if style == "quiet":
                t0 = i * bar + 0.12 + float(rng.uniform(-0.3, 0.3))
            if t0 < 0 or t0 >= dur - 1.5:
                continue
            note = pluck_base + pent[int(rng.integers(len(pent)))]
            f = midi(note)
            pan = float(np.clip(0.5 + rng.normal(0, 0.08), 0.15, 0.85))
            start = int(t0 * SR)
            seg_len = int(2.4 * SR)
            tt = np.arange(seg_len) / SR
            s = _pluck(tt, f, 0.16, 1.6)
            end = min(n, start + seg_len)
            left[start:end] += s[: end - start] * (1.0 - pan)
            right[start:end] += s[: end - start] * pan

    peak = max(float(np.max(np.abs(left))), float(np.max(np.abs(right))), 1e-9)
    g = PEAK / peak
    return left * g, right * g


def write_wav(path, left, right):
    stereo = np.empty((len(left), 2), dtype=np.int16)
    stereo[:, 0] = np.clip(left * 32767, -32767, 32767).astype(np.int16)
    stereo[:, 1] = np.clip(right * 32767, -32767, 32767).astype(np.int16)
    import wave
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(stereo.tobytes())


def main():
    ap = argparse.ArgumentParser(
        description="生成原创垫乐 wav（16-bit 48kHz 立体声，峰值约 −3 dBFS）",
        epilog="quiet 被评价为「诡异」，只在明确要安静到发闷时用。每天换 seed，不要复用上一趟的 wav。\n"
               "--bar-gap both（默认）：一次生成 A（每小节淡到 0，接近旧听感）和 B（小节间交叉淡化）两版。",
    )
    ap.add_argument("--style", choices=["bright", "quiet"], default="bright")
    ap.add_argument("--seed", type=int, required=True, help="必填；换 seed 换听感，同 seed 可复现")
    ap.add_argument("--dur", type=float, default=150.0, help="秒（建议成片 + 30s 余量）")
    ap.add_argument("--out", default="bgm.wav", help="输出路径；both 时派生 _A/_B")
    ap.add_argument("--key", default="D", help="默认 D")
    ap.add_argument("--bass", choices=["on", "off"], default="off", help="低音开关，默认关（bright 不要厚低音）")
    ap.add_argument("--bar-gap", choices=["on", "off", "both"], default="both",
                    help="小节衔接：off=每小节淡到 0（A 版），on=交叉淡化（B 版），both=两版都出")
    ap.add_argument("--print-chords", action="store_true", help="只打印和弦表（JSON）后退出，供测试断言")
    args = ap.parse_args()

    if args.key.upper() not in KEY_PC:
        sys.exit(f"gen_bgm.py: 不支持的调 {args.key}（可用 {list(KEY_PC)}）")
    if args.dur <= 0:
        sys.exit("gen_bgm.py: --dur 必须 > 0")

    chords, labels = make_chords(args.seed, args.key, int(np.ceil(args.dur / 10.0)) + 1)
    # 自检：不允许小三和弦
    for ch in chords:
        root = min(ch)
        for f in ch:
            iv = round(12 * np.log2(f / root)) % 12
            if iv == 3:
                sys.exit(f"gen_bgm.py: 和弦表出现小三度 {ch}，违反 No minor 规则")

    if args.print_chords:
        print(json.dumps({"labels": labels, "midi": [[round(x, 2) for x in c] for c in chords]}, ensure_ascii=False))
        return

    base, ext = os.path.splitext(args.out)
    modes = ["off", "on"] if args.bar_gap == "both" else [args.bar_gap]
    for mode in modes:
        out = f"{base}_A{ext}" if (args.bar_gap == "both" and mode == "off") else \
              f"{base}_B{ext}" if args.bar_gap == "both" else args.out
        bar = 10.0 if args.style == "bright" else 8.0
        left, right = _render(chords, args.seed, args.dur, args.style, bar, mode, args.bass, args.key)
        write_wav(out, left, right)
        print(f"wrote {out} style={args.style} seed={args.seed} dur={args.dur}s "
              f"bar-gap={mode} peak={PEAK} (−3 dBFS)")


if __name__ == "__main__":
    main()
