# testing.md — 改 scripts/ 后的回归验证

> **什么时候读我**：改过 `scripts/` 任何脚本、或要交付「脚本已修」的证据时。全部在 `/tmp/pvc-test/` 用纯合成素材跑（`testsrc2` / `sine` / `anullsrc`）；不碰真实素材、移动硬盘、网盘、Discord。

动 skill 本体前先把整个目录备份成 `<name>.bak-YYYYMMDD/`；备份放 skills 目录里会被索引成第二个同名 skill，记得把备份的 frontmatter `name` 改成 `<name>-bak-YYYYMMDD`，否则 `skill_view` 会报歧义。

## 金标准表（测试一律不引用 commit hash）

> **本地仓和公开仓 hash 不同，测试一律不引用 commit hash。**下面的值是唯一判据。

| 项目 | 金标准值 |
|---|---|
| `scripts/gen_bgm.py` sha256（v3.0.0） | `979a02f9c0e0cd743b310173b1fa99fca2ef70f572c63c7f5b0fc97a511a80f7` |
| `scripts/gen_bgm_guitar.py` sha256（v1.2.1） | `bc6b371a00467a47627c8ec116b0d2cb45802b3ae3e91f000f3ec31633570664` |
| `scripts/legacy/gen_bgm_v2.py` sha256 | `dc2c3c810dd3df144f9942796a1224ed1000ea369e6909ac137eb4840a58bb7e` |
| gen_bgm default（seed 1，dur 60）WAV md5 | `3d4043a9dad21e6f2dd6bcd900ce3a84` |
| gen_bgm plain（seed 1，dur 60）WAV md5 | `032ac7baa1f78adbdfbec56247cb7f1a` |
| gen_bgm lively（seed 1，dur 60）WAV md5 | `a02967892cdb87dcd368a129275bbe43` |
| gen_bgm_guitar mix（seed 7，dur 60）MIDI md5 | `512d615a8b64351d0d5c0b4cb5e652ae` |
| gen_bgm_guitar finger（seed 7，dur 60）MIDI md5 | `d275b45255380c957eac7f16923afff6` |
| gen_bgm_guitar strum（seed 7，dur 60）MIDI md5 | `2f2d8dd6f1b901e57c5cb5deb98b1798` |
| 默认 BGM（nylon sparse 88，seed 20260929，dur 60）WAV md5 | `4f0547731ef7c15112377bc494537b61` |
| 备选 BGM（nylon sparse 80 / density 0.6 / reverb 0.5，seed 20260929，dur 60）WAV md5 | `96bf2aa32f62954ec52e9226dcf12549` |

## 素材合成（先造图，再跑脚本）

- 画幅组：`testsrc2` 各一张 4:3 1600×1200、16:9 1920×1080、竖 1200×1920、10000×1250 全景。
- **坐标编码图**验证运镜轴向：R=x/W、G=y/H 的渐变（Pillow 逐像素字节流，别用 putpixel 循环）。首尾帧均值比肉眼可靠。
- **EXIF 图**：先做显示态图（如上红下蓝竖构图），`rotate(90, expand=True)` 得 raw，再写 `exif[274]=6`。校正正确 = 输出里红色仍在显示顶部。

## pan_still.sh 验证点

- 横摇：首尾帧 ΔR 大（x 在动）、ΔG≈0（y 锁住）。余量不足时 auto 必须打「退回 static」提示。
- 竖摇：上红下蓝图首帧蓝、尾帧红（从下往上）；这一步同时证明 EXIF 校正生效（没校正会判成 hpan）。
- 全景（>8000 宽）先缩再摇。
- **宽度公式**：高度铺满 1080 后的宽度 = `W*1080/H`。写反（`H*1080/W`）会把全景误判成余量不足。

## gen_bgm.py 验证点

- 同 seed 同参数跑两次 md5 相同；换 seed md5 不同。
- `--print-chords` 输出 MIDI 整数（v2 输出的是 Hz，旧断言要改）。外部再断言一遍：
  ```bash
  python scripts/gen_bgm.py --seed 3 --print-chords | python3 -c '
  import json,sys; d=json.load(sys.stdin); T=d["tonic_midi"]; M={0,2,4,5,7,9,11}
  for b in d["bars"]:
      r={(m-b["root"])%12 for m in b["midi"]}
      assert 3 not in r and (4 in r or 5 in r), b
      assert all((m-T)%12 in M for m in b["midi"]), b
  print("chords OK", d["n_bars"], "bars,", d["notes_checked"], "notes")'
  ```
- 三种预设 × 三个 seed 都要能过自检（脚本内部自检失败会非零退出）。
- `--dur 180` 渲染耗时 ≤ 10s。
- 负例：把 `scripts/legacy/gen_bgm_v2.py` 临时改名后，`--style quiet` 必须非零退出；测完改回。
- 正例：`--style quiet --seed 1 --dur 20` 能出 wav（legacy 转调可用）。

## gen_bgm_guitar.py 验证点
工作目录 /tmp/pvc-test/，G=scripts/gen_bgm_guitar.py

a. 依赖：`fluidsynth --version` 有输出；`$PVC_SF2` 存在；记录 sha256，并与 references/third-party.md 一致。
b. 作曲可复现：`--seed 1 --dur 60 --print-chords` 连跑两次，diff 为空；`--seed 2` 的输出与 seed 1 不同。
c. 自检矩阵：seed 1–5 × pattern mix/finger/strum/sparse/wander × key C/D/G，共 75 次 `--print-chords`，全部退出码 0。
d. MIDI 可复现：`--seed 7 --dur 60 --print-chords --midi-out x.mid` 连跑两次，MD5 相同。另外完整渲染两次，WAV 的 MD5 是否相同仅作参考记录，不计 FAIL。
e. 性能：`--seed 1 --dur 180 --out long.wav` 耗时 ≤ 15 s，记录实际秒数；stderr 中不得出现"削波"WARN。
f. 规格（针对 long.wav）：
   - ffprobe 显示 48000 Hz、2 声道、s16，时长 180.000 s（±1 采样）。
   - `ffmpeg -i long.wav -af volumedetect -f null -` 的 max_volume 在 -3.5 到 -2.5 dB 之间。
   - `ffmpeg -sseof -0.3 -i long.wav -af volumedetect -f null -` 的 max_volume < -25 dB。
g. 旧预设不变（金标准，不引用 commit hash）：
   - `shasum -a 256 scripts/gen_bgm.py` 必须等于金标准表的 v3.0.0 sha256（完整值比对，不做前缀比对）。
   - default/plain/lively（seed 1，dur 60）三个 WAV 的 MD5 必须分别等于金标准表的值（完整值）。
h. 负例（各自退出码必须为 2，并有明确报错）：`--sf2 /nonexistent.sf2`、`--fluidsynth /nonexistent`、`--dur 5`。
i. 仓库卫生：
   - `git ls-files | grep -i '\.sf2$'` 为空。
   - `grep -rn 'Karplu[s]' . --exclude=CHANGELOG.md --exclude-dir=.git`，结果为空。
   - `git ls-files | grep -E '\.pyc$|__pycache__'` 为空。
j. 旧 pattern 不变（金标准，不引用 commit hash）：对 mix/finger/strum 各跑 `--seed 7 --dur 60 --print-chords --midi-out`，MIDI 的 MD5 必须分别等于金标准表的 mix/finger/strum 值（完整值）。
k. wander 验证点：
   - k1 可复现：同 seed 两次 MIDI MD5 相同；seed 1 与 seed 2 不同。
   - k2 量化后比较（起音对齐到八分音符格子，忽略力度和人性化偏移）：
     - k2a 节奏骨架：每小节签名 = 起音格位集合（0–7）。seed 20260929、dur 120，分别报告 wander 和 sparse 的不同签名数、相邻小节签名相同的占比。判据：wander 不同签名 ≥ 8，相邻相同 ≤ 25%；并且两项都要明显优于 sparse。sparse 若也达标，报告口径问题，不许改阈值。
     - k2b 顶线：每个格位取最高音，组成序列，按 4 小节一窗滑动。报告 wander 和 sparse 的不同窗口占比。判据：wander ≥ 0.90，且高于 sparse。
   - k3 旋律规则：所有旋律音都在五声音阶内、落在 62–76；强拍上的旋律音 100% 是和弦音。每个旋律音时长 ≥ 0.15 s（用来抓 5ms 残音）；报告旋律音总数，并与修复前的 34 对照。
   - k4 密度：dur 180 的音符数在 sparse（347）的 1.0–1.5 倍之间。
   - k5 规格：沿用 f 的规格检查（48k/2ch/s16、峰值约 −3.1 dB、尾部 < −25 dB）。
   - k6 density：同 seed，`--density 0.6` 的音符数 < `0.85` 的音符数。

## 链路验证点

- 90s 合成片（testsrc2 + sine「人声」）→ `mix_bgm.sh`（BGM 故意短于片长，必须走 acrossfade 接长）→ `export_discord.sh` → `check_delivery.sh` 全 PASS。
- `mute_segment.sh` 用 4.017s 这类非整秒切片：音画差 ≤1 帧。
- 负例也要跑：`mix_bgm.sh` 收到文件名含 `_bgm` 的输入必须非零退出。

## grep 门（改完必查）

- `1280:720`、`templates/`、零宽字符（ZWSP/ZWNJ/ZWJ/BOM）：0 处。
- `1100k`、`zoompan`、`STHeiti`：只允许「禁止/作废」语境出现。

## 试听件
- 默认 BGM 已定（见 preferences.md「当前默认」）。只有会改变声音的修改才出试听件：ASCII 文件名，60 s，seed 用当天日期，改前改后各一版，通过 MEDIA: 发出，由用户决定。

**T9 全景限速。** 10000×1250 的亮度渐变全景图（整幅 YAVG 需要渐变图才能算 dx；沿用 T1 公式，宽度换成缩放后的 8640（10000×1250→8000×1000→铺满 1080 高）），hpan，4 s：

- dx 均值 ≤ MAXSPD+0.05（默认 10.05），停帧 0，日志里有"只平移中间"提示，且新版只平移中间 1200px，提示里带「全程扫完需 --dur 22.4」（数值以实际为准，报原文）。
- 对照 v2.5.1 版 pan_still.sh：dx≈56 px。
- 再用 1600×1200 的图跑一次，确认 dx 仍约为 4 px，没有被限速。

**T9b 竖图限速反例。** 3024×4032 全高线性渐变竖图（geq 合成，顶 R=255→底 R=0），vpan 默认参数：

- 默认：不出现限速提示，尾帧 R ≥ 185（理论≈194）。
- 反例 `--max-speed 5`：出现限速提示，尾帧 R ≤ 170（理论≈161）。
- 注：分带图在限速 5 下 R≈208，测不出旧 bug，禁用。

**T10 --dur 保留。** 做一张余量不足的图（比如 1920×1000），`--mode hpan --dur 8`：

- 输出应为 8 s（240 帧），日志里有"退回 static"。
- BASE 对照应为 4 s。

**T11 文件名。** `export_discord.sh src.mp4 /tmp/pvc-test/v252/山行.mp4`：

- 输出文件名不以 `.` 开头，stem 非空，check_delivery 全部 PASS。

**T11b 确定性命名。**

- 山行.mp4 / 河边.mp4 省略 OUT → 名字不同，形如 `export_<8hex>_dc.mp4`。
- 山行2.mp4 / 河边2.mp4 → 名字不同，形如 `2_<8hex>_dc.mp4`。
- 山行.mp4 导出两次 → 名字相同。
- trip.mp4 → `trip_dc.mp4`（无哈希、无提示）。
- 显式 OUT=trip.mov → `trip.mp4` + 扩展名提示。
- 全部 check_delivery PASS。

**T12 mix_bgm 负例。**

- 输入无音轨的视频应 exit 1，并带"mute_segment"提示。
- 输入 5 s 的片子应 exit 1。

**T13 HEIC。** `sips -s format heic test.png --out test.heic` 生成测试图，pan_still static 能出 1920×1080 的片子。没有 sips 的环境记为 SKIP。

**T14 参数校验。**

- `--dur 0`、`--dur abc`、`--anchor-y 1.5` 各自 exit 2，并且有明确报错。
- `--anchor-y abc`、`--dur 2x`、`--hold abc`、`--hold -1`、`--max-speed 1e3` 均 exit 2 且报错明确；`--mode vpan --dur 0.5` → exit 2（回归）。
- `pan_still.sh img.png --dur`（缺值）→ exit 2，报错含「缺少取值」，不得出现 unbound variable。
