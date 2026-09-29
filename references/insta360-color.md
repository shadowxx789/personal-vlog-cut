# insta360-color.md —— 正片 / I-Log 判定与还原

> **什么时候读我**：拿到 Insta360 素材、要决定套不套 LUT、或要进 Insta360 Studio 剪时。

## 先抽帧，再判断（不要按机型套 LUT）

- **色彩先抽帧**。Luna Ultra 正片可以在机内烘好；文件仍标 bt709，跟灰片 I-Log 一样——**不要因 `color_transfer=bt709` 就判正片**。
- **已是正片的判据**：石板阴影实、砖/肤反差正常、阳光硬边。→ **不要再**套 Studio「色彩还原」LUT、ffmpeg `eq`、或别人的 cube。二次正片会过饱和偏色。
- **当 I-Log 的判据**：帧灰闷/低对比/肤色闷黄，或他点名「灰片 / iLog 要套官方还原 LUT」。
- 他说**录的时候选了正片**：就按已烘好走，除非帧打脸。

## 官方 cube

- 路径：`/Applications/INSTA360 Studio.app/Contents/data/i_log/Luna_I-Log_to_Rec709.cube`。
- ChatCut 里**单独** `push_asset` 这个文件，**只挂 `VID_`**；照片不套。步骤见 [chatcut.md](chatcut.md)「LUT」。
- **照片 / Ken Burns 已是 sRGB，从不要套 log**。
- **不要叠库里的索尼/佳能 Log LUT**（那是给未还原 Log 的，会二次偏色）。`VID_` 已挂官方 cube 后同理。
- 没有官方 cube：才轻 `eq` + 暖；没 Studio 不要乱套别人 LUT；不要用网上别人的 LUT。

## Insta360 Studio（要求用 Studio 剪时）

- 加载 `insta360-studio`。**色彩判定完立刻进时间线/导出**，不要停在 LUT 讨论上。
- 工程是空的、没有导出文件 = 没剪完，不要说成片已好。
- JPG 在 Studio 里**不能裁**；广角 MP4 不能变焦——运镜/铅顶仍要先做 16:9 静帧（`scripts/pan_still.sh`）再进箱。
