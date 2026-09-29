# ffmpeg-recipes.md —— ffmpeg 命令唯一出处

> **什么时候读我**：要手写 ffmpeg 命令时。**先看 `scripts/` 有没有现成脚本**，脚本覆盖不到的才用这里的命令。所有命令统一 **1920×1080**（720p 只允许出现在「LRV 仅供查看」上下文）。

## 通用红线

- 1080p **不要 `zoompan`**（小数变焦在高分辨率像整片在晃）；运镜一律 `scripts/pan_still.sh` 或 `crop`+`t`。
- `rx`/`ry` 必须是 **16 的倍数**（24 会直接起不来）。
- overlay 的 `alpha='if(lt(t,...),...)'` 嵌套逗号会被命令行拆开：写进 **`-filter_complex_script` 文件**，或只用 `enable=`。
- 照片/无声段补静音轨、单段静音：一律 **`apad` 到视频时长**，不用 `anullsrc`+`-shortest`（每切短十几毫秒 AAC，接到有声段就音画不同步，裁决 C4）。单段静音直接用 `scripts/mute_segment.sh`。
- 抽帧认画面：`ffmpeg -i FILE -ss T -frames:v 1 out.jpg`，**seek 放 `-i` 后面**。

## 4K50 HEVC seek（会漂）

- `-ss` 放 `-i` **前**（input-seek）：后半段会跳到完全另一幅画面（远山变成公路/手机）。早段（大约前 1 分钟）还可以 input-seek；**晚段必须 `-ss` 放 `-i` 后**（output-seek），或改切这条的开头。
- 抽完段**看 VID 首帧**再 concat——LRV 同一秒对上了不等于 VID 是同一幅。规则背景见 [footage-sources.md](footage-sources.md)「LRV/VID」。

## 手机延时放慢（setpts，不插帧）

源文件常 ~2s/60 帧、没音频。`fps=30` 后再 `setpts`（帧率会降，播放正常）。倍率阶梯见 [preferences.md](preferences.md)。

```
# 0.65x → setpts = 1/0.65 ≈ 1.538（0.5x→2.0，0.4x→2.5）
ffmpeg -i SRC -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p,setpts=1.538*PTS" -an -c:v libx264 -preset fast -crf 20 out.v.mp4
# 补一条静音轨：apad 到视频时长（不是 anullsrc+-shortest）
VDUR=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 out.v.mp4)
ffmpeg -i out.v.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a \
  -c:v copy -c:a aac -ar 48000 -b:a 128k -af "apad" -t "$VDUR" out.mp4
```

## 竖图上摇（8s，脚下停 0.8s）

`zoompan` 的 `d` 不是变量（`on/d` 会报 Undefined constant）。用 `crop`+`t`：

```
ffmpeg -loop 1 -i STAIRS.jpg -t 8 \
  -vf "scale=1920:-2,crop=1920:1080:0:'(in_h-1080)*(1-min(1\,max(0\,(t-0.8)/6.2)))',fps=30,format=yuv420p" \
  -c:v libx264 -preset fast -crf 20 -an stairs.v.mp4
```

## 横图慢移 / 静帧

优先 `scripts/pan_still.sh`（锁 y 只移 x、余量不足自动退 static、EXIF 校正、抽首尾帧）。脚本覆盖不到时：

```
ffmpeg -loop 1 -i PIC.jpg -t SEC \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080:'if(gt(in_w,1920),(in_w-1920)*t/SEC,0)':Y,fps=30,format=yuv420p" \
  -c:v libx264 -preset fast -crf 18 -an pic.v.mp4
```

（旧版让 x、y 同时移动是错的：**锁 y 只移 x**，裁决 C5。）

## 手持防抖

```
ffmpeg -i SRC -vf "deshake=rx=32:ry=32,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p" ...
```

`rx`/`ry` 必须是 16 的倍数；deshake 后 `crop` 回画幅。

## concat

照片+有声混剪用 **concat filter**（同一时钟），不要只靠 demuxer copy：

```
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" out.mp4
```

已编码段可 `-c copy` concat；Non-monotonic DTS 常见，以最终 re-encode 的 `_dc.mp4` 为准。

## 片上字幕（中文）

Pillow 渲透明 PNG，再 `overlay` + `enable='between(t,...)'`。字体**手札体** `Hannotate.ttc` index=0（查找与禁令见 [preferences.md](preferences.md)「字体」）。位置按裁决 C1。话题标签不上屏。

**烧字幕先烧进高码率母版 `vN_sub.mp4`，再用 `scripts/export_discord.sh` 另出 Discord 版**（裁决 C2；不要再一次编进 Discord 版、不要再出现 1100k 的 Discord 版）：

```
ffmpeg -i CUT.mp4 -loop 1 -i overlay_open.png -loop 1 -i overlay_end.png \
  -filter_complex_script sub.txt -map "[v]" -map 0:a -t DUR \
  -c:v libx264 -preset medium -b:v 2500k -maxrate 3000k -bufsize 6000k \
  -c:a copy -pix_fmt yuv420p -movflags +faststart vN_sub.mp4
# sub.txt 里：
# [0:v][1:v]overlay=0:0:enable='between(t,0.9,6.5)':format=auto[v1];
# [v1][2:v]overlay=0:0:enable='between(t,END-3.7,END)':format=auto[v]
```

- 字只叠开场路/景，进下一镜前退掉（`enable` 区间就是退场）。
- 不要用 `fade`+`setpts` 挪 PNG 时间轴（会拖死或截断片长）。
- 结尾字**先报再烧**，流程见 [preferences.md](preferences.md)「结尾字流程」。

## 垫乐

- 生成：`scripts/gen_bgm.py`（`--seed N --dur 秒 [--preset default|plain|lively|acoustic]`；acoustic 为木吉他，`--no-strum` 全程指弹；大调、每小节一和弦、内置音阶自检）。不拆商业曲，每天换 seed。旧 v2 在 `scripts/legacy/`，不再默认使用。
- 混音：`scripts/mix_bgm.sh`（原声 ×1.18、BGM highpass 140/lowpass 10000 ×0.72、淡入 2.6s/淡出 4.3s、sidechain、末尾 `alimiter=limit=0.95`）。只从**没垫过**的 `vN.mp4` 混，输出 `vN_bgm.mp4` 归档母版。
- BGM 比片长短：`acrossfade` 接同一条，**禁止 `apad` 补静音**：

```
ffmpeg -i bgm.wav -i bgm.wav -filter_complex "[0:a][1:a]acrossfade=d=8:c1=tri:c2=tri" bgm_long.wav
```
