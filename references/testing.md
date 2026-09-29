# testing.md — 改 scripts/ 后的回归验证

> **什么时候读我**：改过 `scripts/` 任何脚本、或要交付「脚本已修」的证据时。全部在 `/tmp/pvc-test/` 用纯合成素材跑（`testsrc2` / `sine` / `anullsrc`）；不碰真实素材、移动硬盘、网盘、Discord。

动 skill 本体前先把整个目录备份成 `<name>.bak-YYYYMMDD/`；备份放 skills 目录里会被索引成第二个同名 skill，记得把备份的 frontmatter `name` 改成 `<name>-bak-YYYYMMDD`，否则 `skill_view` 会报歧义。

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
c. 自检矩阵：seed 1–5 × pattern mix/finger/strum/sparse × key C/D/G，共 60 次 `--print-chords`，全部退出码 0。
d. MIDI 可复现：`--seed 7 --dur 60 --print-chords --midi-out x.mid` 连跑两次，MD5 相同。另外完整渲染两次，WAV 的 MD5 是否相同仅作参考记录，不计 FAIL。
e. 性能：`--seed 1 --dur 180 --out long.wav` 耗时 ≤ 15 s，记录实际秒数；stderr 中不得出现"削波"WARN。
f. 规格（针对 long.wav）：
   - ffprobe 显示 48000 Hz、2 声道、s16，时长 180.000 s（±1 采样）。
   - `ffmpeg -i long.wav -af volumedetect -f null -` 的 max_volume 在 -3.5 到 -2.5 dB 之间。
   - `ffmpeg -sseof -0.3 -i long.wav -af volumedetect -f null -` 的 max_volume < -25 dB。
g. 旧预设不变：
   - 先运行 `git show 457e704:scripts/gen_bgm.py > ref.py`。
   - ref.py 与 scripts/gen_bgm.py 分别生成 default/plain/lively（seed 1，dur 60），三对 MD5 必须完全相同。
h. 负例（各自退出码必须为 2，并有明确报错）：`--sf2 /nonexistent.sf2`、`--fluidsynth /nonexistent`、`--dur 5`。
i. 仓库卫生：
   - `git ls-files | grep -i '\.sf2$'` 为空。
   - 在 CHANGELOG.md 以外 grep `Karplus`，结果为空。
j. 旧 pattern 不变：用 `git show a624a61:scripts/gen_bgm_guitar.py > ref_g.py`（BASE），对 mix/finger/strum 各跑 `--seed 7 --dur 60 --print-chords --midi-out`，新旧两边的 MIDI MD5 必须完全相同。

## 链路验证点

- 90s 合成片（testsrc2 + sine「人声」）→ `mix_bgm.sh`（BGM 故意短于片长，必须走 acrossfade 接长）→ `export_discord.sh` → `check_delivery.sh` 全 PASS。
- `mute_segment.sh` 用 4.017s 这类非整秒切片：音画差 ≤1 帧。
- 负例也要跑：`mix_bgm.sh` 收到文件名含 `_bgm` 的输入必须非零退出。

## grep 门（改完必查）

- `1280:720`、`templates/`、零宽字符（ZWSP/ZWNJ/ZWJ/BOM）：0 处。
- `1100k`、`zoompan`、`STHeiti`：只允许「禁止/作废」语境出现。

## 试听件
- seed 用当天日期，各 60 s，文件名只用 ASCII，通过 MEDIA: 发给用户。
- 木吉他：
  - bgm_nylon_finger_lite_s<seed>.wav（`--pattern finger` + `--density 0.5` + `--bpm 88`）
  - bgm_nylon_sparse_s<seed>.wav（`--pattern sparse` + `--bpm 88`）
  - bgm_nylon_sparse_slow_s<seed>.wav（`--pattern sparse` + `--bpm 80` + `--density 0.6` + `--reverb 0.5`）
- 合成器版（default/plain/lively）已在 v2.1.0 试听过，除非用户要求，不重复生成。
- 默认值由用户试听后决定，agent 不做选择。

## v2.5.0 验证点（pan_still 帧率/fit、export two-pass、limiter 0.89、wc -c）

**T1 平移不顿。** 做一张 2400×1080 的横向亮度渐变图，hpan 8 s：

```bash
ffmpeg -f lavfi -i "color=black:s=2400x1080,geq=lum='X*235/W+16':cb=128:cr=128" -frames:v 1 grad.png
scripts/pan_still.sh grad.png hpan.mp4 --mode hpan --dur 8   # 参数名以脚本实际为准
ffmpeg -i hpan.mp4 -vf "crop=4:1080:0:0,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=yavg.txt" -f null -
```

判定标准：

- ffprobe 显示 `r_frame_rate=30/1`，帧数为 240（±1）。
- 相邻帧 YAVG 差值：除首尾各 1 帧外不许为 0（有 0 就说明有重复帧）；差值的标准差 / 均值 < 0.2。
- 贴出差值的 min/max/均值/标准差。同一测试用 BASE 版脚本（`git show e57fb28:scripts/pan_still.sh`）也跑一次作对照，预期对照版会出现 0 差值。

**T2 static 默认无黑边。** 做一张 1600×1200（4:3）的 testsrc2 图片，static 模式：

- 输出为 1920×1080。
- 最左 4 列和最右 4 列的 YAVG 都 > 30（黑边的 YAVG 约为 16）。

**T3 `--fit contain`。** 同一张图加 `--fit contain`：

- 最左 4 列的 YAVG ≤ 20（有 pad 黑边）。

**T4 two-pass 不超限。** 生成 240 s 的高噪声素材：

```bash
ffmpeg -f lavfi -i "testsrc2=s=1920x1080:r=30,noise=alls=40:allf=t" -f lavfi -i "sine=f=440:r=48000" -t 240 -c:v libx264 -crf 18 -c:a aac -ac 2 src240.mp4
```

跑 export_discord.sh，判定标准：

- exit 0，文件大小 < 上限，check_delivery.sh 全部 PASS。
- passlog 残留：`find /tmp "$(pwd)" -name '*2pass*' -newer src240.mp4` 结果为空。
- 贴出实际大小和视频码率。

**T5 重试路径。** 分两种情况：

- 用 `PVC_DISCORD_LIMIT_BYTES` 设一个比 T4 结果小约 8% 的值再跑：应当触发 1 次重试后成功，日志里能看到两次尝试的码率和大小。
- 再设一个比 T4 结果小 40% 的值：应当 3 次尝试后 exit 非 0，报错里有每次的大小。
- 两种情况下 passlog 都不能有残留。

**T6 limiter。** 分四项检查：

- 用 `sine=f=1000` 加 `volume=0dB` 做一条接近满刻度的 BGM wav，和 30 s 的 testsrc2+sine 视频一起跑 mix_bgm.sh。
- 用 volumedetect 查 `vN_bgm.mp4` 的 max_volume，应当 ≤ −0.5 dB。
- 再跑 export_discord.sh，check_delivery.sh 的峰值项必须 PASS。
- 另外用默认木吉他命令生成的 BGM 也混一次，只记录 max_volume，不作判定。

**T7 卫生 + 旧回归。**

- `grep -rn 'stat -f' scripts/` 为空。
- `grep -rn -- '-loop 1 -i' scripts/ references/`：只允许出现在「片上字幕」的 overlay PNG 示例里。
- `grep -rn 'limit=0.95'`（CHANGELOG 以外）为空。
- `git diff --stat e57fb28 -- scripts/gen_bgm.py scripts/gen_bgm_guitar.py scripts/legacy/` 为空。
- 默认 BGM 两条命令复跑，MD5 仍为 `4f0547731ef7c15112377bc494537b61` / `96bf2aa32f62954ec52e9226dcf12549`。
- testing.md 原有的全部验证点再完整跑一遍（mute_segment、check_delivery、pan_still 原有项等）。
