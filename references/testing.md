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

## 链路验证点

- 90s 合成片（testsrc2 + sine「人声」）→ `mix_bgm.sh`（BGM 故意短于片长，必须走 acrossfade 接长）→ `export_discord.sh` → `check_delivery.sh` 全 PASS。
- `mute_segment.sh` 用 4.017s 这类非整秒切片：音画差 ≤1 帧。
- 负例也要跑：`mix_bgm.sh` 收到文件名含 `_bgm` 的输入必须非零退出。

## grep 门（改完必查）

- `1280:720`、`templates/`、零宽字符（ZWSP/ZWNJ/ZWJ/BOM）：0 处。
- `1100k`、`zoompan`、`STHeiti`：只允许「禁止/作废」语境出现。

## 试听件

同一个当天新 seed，60s，出 3 版：`--preset default` / `plain` / `lively`，
文件名 `bgm_<preset>_s<seed>.wav`（脚本默认就是 ASCII），`MEDIA:` 发上来，不要自己选。
