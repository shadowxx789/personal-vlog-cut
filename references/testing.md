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

- 同 seed 跑两次 md5 相同；不同 seed md5 不同（seed 必须真的进随机流）。
- `--print-chords` 加外部断言：任何和弦相对根音不得出现小三度（3 半音）。
- 150s 生成耗时 ≤10s（必须 numpy 矢量化，不许逐样本 Python 循环）。

## 链路验证点

- 90s 合成片（testsrc2 + sine「人声」）→ `mix_bgm.sh`（BGM 故意短于片长，必须走 acrossfade 接长）→ `export_discord.sh` → `check_delivery.sh` 全 PASS。
- `mute_segment.sh` 用 4.017s 这类非整秒切片：音画差 ≤1 帧。
- 负例也要跑：`mix_bgm.sh` 收到文件名含 `_bgm` 的输入必须非零退出。

## grep 门（改完必查）

- `1280:720`、`templates/`、零宽字符（ZWSP/ZWNJ/ZWJ/BOM）：0 处。
- `1100k`、`zoompan`、`STHeiti`：只允许「禁止/作废」语境出现。

## 试听件

A/B 各出一版（`--bar-gap off|on`、60s、当天新 seed、ASCII 文件名），`MEDIA:` 发上来。
