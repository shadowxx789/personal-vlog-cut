---
name: personal-vlog-cut
description: "剪 用户 的个人爬山/旅行/明信片 vlog（ffmpeg 或 ChatCut Desktop）：看素材先分析、粗剪、按秒数重剪、生成与混垫乐、烧手札字幕、写小红书文案、发 Discord、传夸克归档。Use for personal hike/travel vlog cutting."
version: 2.4.0
---

# Personal vlog cut

用户 要的是一张明信片，不是一个频道。参考博主只借气口，不借体量。

**规则只写一处。** 本文件只放流程和最高频默认值；细节看 `references/` 对应篇，脚本看 `scripts/`。同一条规则以最后一次用户纠正为准（裁决记录在 CHANGELOG.md）。

## 0. 流程总览

等素材 → 先讲分析（他点名时只分析不开剪）→ 粗剪/按秒数重剪 → 画面切定后垫乐 → 烧字幕（片头可直烧，结尾字先报）→ 交付 / 归档。

## 1. 等素材（没素材就停）

「就用今天的素材」≠ 素材已在磁盘上。没给路径/网盘/频道文件：停，说一句怎么丢，等他丢。不扫 Downloads/Desktop/Movies 猜山。中途被告知「素材还没给你」：立刻停搜，不解释。
移动硬盘、夸克、LRV/VID 规则：见 [references/footage-sources.md](references/footage-sources.md)。

## 2. 默认偏好（没明说就按这个）

- 时长 **2–3 分钟**；入选表已钉死、他说「别砍」：一条不丢，上限 **4 分钟**。
- **不额外写/配旁白 ≠ 静音**：自带说话、脚步、风必须留。明说某段不要原声才静那几切（BGM 留）。杂音含别人讲话；**本人讲话必须留**。
- 晃太快的镜头不进；下山收至少约 **20s**；开场第二镜不拍脸部特写。
- **地名听用户的**，不用素材文件夹/文件名。
- 放慢阶梯：**0.65–0.7x → 0.5x → 0.4x**，`setpts` 不插帧。
- 照片默认 **4s**；开场那张要让音乐先出来时约 **8s**。
- BGM：大调、稀疏、不诡异不呜呜；垫乐 `volume` **0.72**，口播段 **−22dB**；每天换 seed。
- 不要地理论文、机身参数、摄影哲学、「感谢大自然」。Discord：短句短段、结论先行。

完整清单（字幕位置、字体、BGM 口味、镜头取舍）：见 [references/preferences.md](references/preferences.md)。

## 3. 先讲分析（他说「读一下…先讲分析」时）

只交付判断，不开剪。清单 → 抽帧看画面 → 写明证据盲区 → 预选表（时长用区间）。盘里有 `02_优秀`/`03_普通`/`00_待删除` 时的取舍规则、一天两地拆两张明信片：见 [references/analysis-first.md](references/analysis-first.md)。

## 4. 剪辑配方（短 vlog）

1. 开**场**：地点或上路，一两个画面说清地方。
2. 走：脚、树、背影；切点慢于广告，留住风声/脚步。
3. 一个小意外或停下来的瞬间（人味，不是高光）。
4. 山顶或回头看的那一眼，可以慢一拍或静帧。
5. 下山/回家收，留得住；不要口号、不要切太短。

「借一个博主的感觉」（例：Linksphotograph）：默认借气口不仿节目，见 [references/linksphotograph.md](references/linksphotograph.md)。

## 5. 脚本（能用脚本不手写命令）

| 脚本 | 干什么 |
|---|---|
| `scripts/gen_bgm.py` | 生成垫乐 v3（指弹风；`--seed` 必填，`--preset default\|plain\|lively`；内置小三度和音阶自检；`--style quiet` 转调 legacy v2，不推荐） |
| `scripts/gen_bgm_guitar.py` | 木吉他 BGM（FluidR3_GM 采样 + fluidsynth）：开放和弦，指弹/轻扫交替；`--pattern mix\|finger\|strum\|sparse`、`--guitar steel\|nylon`、`--key`、`--bpm`（默认 96）、`--density`、`--print-chords`、`--midi-out`；需要 fluidsynth 和 `$PVC_SF2` |
| `scripts/pan_still.sh` | 静帧 → 16:9 1080p 运镜 mp4（横摇锁 y 只移 x / 竖摇从下往上；**禁 zoompan**） |
| `scripts/mix_bgm.sh` | 原声 + 垫乐 sidechain + `alimiter`，输出 `vN_bgm.mp4` 归档母版 |
| `scripts/mute_segment.sh` | 单切静音（`apad` 到视频时长，音画差 ≤1 帧） |
| `scripts/export_discord.sh` | 按片长算码率压到约 9MB、1080p、ASCII 名，自动跑体检 |
| `scripts/check_delivery.sh` | 交付前体检 + 接触表（**抽帧必须看一眼**） |

ffmpeg 命令唯一出处：[references/ffmpeg-recipes.md](references/ffmpeg-recipes.md)（放慢、deshake、concat、烧字幕、4K50 seek）。改过 scripts/ 就按 [references/testing.md](references/testing.md) 跑回归（纯合成素材 + grep 门）。

## 6. 文案与片上字幕

「帮我写个文案」默认小红书：标题一行 + 两三句正文 + `#地名 #爬山`，标签不上屏。
「把文案放成字幕」：字体**手札体**（`Hannotate.ttc` index=0，禁止黑体/Heiti）；开头三句叠开场约 1–6.5s 放画面中下；片头日标题放天空、避开脸和牌匾，可直烧；**结尾字先报给他、点头再烧**（「按惯例加下山了」= 已点头），放天空/画面上方空处，不居中不放下沿。字进下一镜（尤其脸）前退掉。
位置、字体查找、事件先例：见 [references/preferences.md](references/preferences.md)「字幕」。

## 7. Recut：看画面，不看注释

他说的秒数以他看到的 `_dc.mp4` 为准（`-ss` 放 `-i` 后抽帧认画面）；复用 `NN.mp4` 先抽帧；只改点名的那几张；复盘只重编被改的切。完整规则见 [references/recut.md](references/recut.md)。

## 8. ChatCut Desktop / Antigravity

- 他点名「指挥 Antigravity / 让 agy 用 ChatCut」：Hermes 只预检 + 写任务书派活（**静帧和 VID 都要给绝对路径**），加载 `antigravity-cli`。见 [references/chatcut.md](references/chatcut.md)「Antigravity 派活」。
- 他要用 ChatCut 继续这张明信片、没点名 Antigravity：走 Desktop MCP（先锁 16:9 画幅），不要改跑 ffmpeg concat。步骤顺序表、挂上≠套上、Relink、BGM 首尾相接：见 [references/chatcut.md](references/chatcut.md)。
- 要 Insta360 Studio 剪：加载 `insta360-studio`，算换手，不要用 ffmpeg 充数。色彩判定：见 [references/insta360-color.md](references/insta360-color.md)。

## 9. 交付

- 成片 `MEDIA:` 发 Discord：1080p、SAR 1:1、DAR 16:9、yuv420p，**8–10MB**、ASCII 文件名。先说时长和用了哪几段。
- 接触表/缩略图 `MEDIA:` 不上屏时走 Bot API 上传当前 thread。
- 「无损归档」传**没压 Discord 的** `vN_bgm.mp4` 到夸克当天夹。
- 验收是频道里能点开的链接，不是本地路径。
细节（压缩参数、压扁排查、夸克步骤）：见 [references/delivery.md](references/delivery.md)。

## 10. 跨 skill 加载

| 场景 | 加载 |
|---|---|
| 夸克下载 / 归档上传 | `quark-netdisk-ops` |
| Antigravity 派活 | `antigravity-cli` |
| 要 Insta360 Studio 剪 / 还原 LUT | `insta360-studio` |

## 红线

不碰真实素材做测试（测试只用 `testsrc2`/`sine`/`anullsrc` 合成素材）；结尾字没点头不烧；不拆商业曲；BGM 只从没垫过的 `vN.mp4` 混；**会改变声音的修改一律出 A/B 两版让他听了再定**，不自己拍板。
