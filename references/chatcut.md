# chatcut.md —— ChatCut Desktop 明信片 / Antigravity 派活

> **什么时候读我**：用户要用 ChatCut Desktop 继续这张明信片，或点名「指挥 Antigravity / 让 agy 用 ChatCut」时。BGM/字幕仍听 SKILL.md：画面切定再加乐，结尾字先报再烧。

## A. 步骤顺序表（Hermes 自己走 Desktop MCP）

1. `list_projects` → `target_project`（空工程也先绑；**已有同名空项目就 target，不要再 create_project**）。
2. **锁画幅**：`manage_timelines action=update`：`width=1920 height=1080 ratio=16:9 fit=cover`。**必须在第一张静帧之前**——第一张 4:3 照片会把 composition 拉成照片像素，之后 16:9 视频会被左右 crop。
3. `push_asset` 入选清单**绝对路径**，一次打齐照片 + `VID_`（**不要 LRV、不要 `00_待删除`**）。外部硬盘第一次读可能弹 macOS 权限。
4. **LUT 单独 push**（见 B 节）。
5. 视频入点：`inspect_asset sourceFrameCount` 找稳的几秒；`sourceStartFromInSeconds` + `durationInFrames`。他说「整段留」就省 duration。
6. 时间线：`edit_item` `trackId:V1` + `alignTo:track-end`。视频 `fit:cover`；照片默认 cover，他要整张静着看才 `fit:contain`（`fit:cover` 不要和 `crop*` 同传）。照片必填 `durationInFrames`：默认 **4s（120f）**，开场/收尾 5s，竖图上摇约 8s（见 [preferences.md](preferences.md)「照片时长」）。运镜先用 `scripts/pan_still.sh` 做成 16:9 再 push 替掉静帧。
7. 别人讲话的那一切 `muted:true`（落盘成 `decibelAdjustment:-60`）；**本人讲话留**。
8. 改过画幅之后：`inspect_item` 每段 16:9 视频，`cropLeft/cropRight/cropTop/cropBottom` **归零**——`fit=cover` 的时间线更新不清 4:3 留下的侧裁，视频会带黑边。
9. 照片切入切出：相邻项 `builtin:tr-cross-dissolve` 约 **15f**，写明 `outgoingItemType` / `incomingItemType`。溶解要源片余量：`sourceStart=0` 的进点或用满片长的出点 **0 余量**不要硬上（会整批回滚），那几刀硬切。交叉溶解**不能**把 cover 裁掉的字「缓」出来。
10. `preview_timeline views:["viewer"]` 分段看。`viewerFrameCount` 被拒 >9 就改 ≤9 并拆区间；某段 SIGABRT 就缩区间、跳过超大源帧。
11. **画面切定之前不要 `submit_music`、不要烧结尾字**（他点名的片头日标题可在开场镜上完后立刻烧，见 D）。

## B. LUT：挂上 ≠ 套上

- 官方 cube（路径见 [insta360-color.md](insta360-color.md)）**单独** `push_asset`，不要和媒体打一包。`edit_item` 用 `type=pixel-effect` + `targetItemId` **只挂 `VID_`**（不要写成 `type=effect`）。照片不套。
- `inspect_asset` 的 `properties.lut` 为 null 或 `desktopRegistered` 为 false = 空壳，拆掉重推。
- `propertyOverrides.lut` 写 cube 路径 + `enabled:true` **仍可能不进 `local_export`**。**验收只看导出 mp4 的口播帧**（`-ss` 放 `-i` 后）：仍灰闷就没套上，不要发这版。9 格 viewer 拼图和 `attachedEffects` 都不算验收。
- **`lut3d` 兜底**：自定义 cube 烘不进导出时，用同一颗官方 cube 做 `lut3d=file=…:interp=tetrahedral:enable='between(n,start,end-1)+…'`，enable **只覆盖原始 `VID_` 的时间线帧区间**。静帧摇镜 mp4（已是 sRGB）和字幕不套。
- `VID_` 已挂官方 I-Log cube 后，**不要再叠库里的索尼/佳能 Log LUT**。

## C. 静帧进库

- 进库前读 JPG 的 EXIF `Orientation`；不是 1 就 `ImageOps.exif_transpose` 另存 jpeg 再 `push_asset`（必要时 `deletes+adds` 换资产）。**ChatCut 不读方向标记**，竖图会横着躺。
- 宽超约 8K 的全景：中心 16:9 缩到 **≤3840×2160** 再 push，否则 viewer 仍帧会把 native host 打崩。
- 竖图铺满：`width=1920`、`height` 按比例、`crop*=0`、用 `top` 负值把人挪进 1080 窗，**每改一次 `top` 就 viewer 认头**。不要 pad 黑边；不要把 `builtin:zoom` / `__chatcutReframeCurve` 当竖图上摇（窗会停在脸上还切头顶）。
- 海报/大字被 16:9 cover 切掉：淡入淡出救不了。源里字不全→换拍摄时间附近更全的一张；源里字全→这张 `fit:contain`（允许这张有黑边），不要为铺满切标题。

## D. 片头日标题 / 结尾字

- 透明 PNG（1920×1080）`push_asset` 后铺画面轨**上面**的轨，**不要当 captions**。`adds` 的 `type` 必须是 **`image`**（写成 `video` 会整批拒绝：`Asset … is image, not video`）。新建轨默认 `order:0` 会垫在画面下面字看不见——把字幕轨 `order` 设成 **`1`**（只接受 `0…视频轨数-1`）。手札 `Hannotate.ttc` index=0，字要大。
- 字只盖开场静帧，进口播（脸）前退掉。他要乐先出来再切口播：开场静帧约 **8s**。
- 叠完不要只信 9 格 viewer（第一格常在标题入点之前，会误判没字）：对导出在标题窗口里抽一帧认头。
- 位置（片头放天空不盖合影脸/牌匾、结尾字放天上不放下沿）：见 [preferences.md](preferences.md)「字体与字幕」。结尾字**先报再烧**。

## E. BGM 时长同步

- 生成曲短于成片：**不要把 audio 项拉过源片时长**（`inspect_asset.duration` 微秒 ÷ fps 为上限）。同一 Music 轨上**首尾相接**第二段（`fromFrame` = 第一段 `endExclusive`），淡出接淡入；指定 `trackId` 时不要和已有项重叠（会拒）。
- 加镜后已铺的音乐项不会跟着变长，尾部空出无乐段：补到新的 `durationFrames`（仍不拉过源片），或说明乐停在哪一秒。**只把开场静帧拉长时**：第一段床的 `durationFrames` 跟到新开场终点，后面每段的 `startFrame` **和 `sourceIn` 一起**加同样的帧数——只改 `startFrame` 会让乐在切口倒回，口播底下的 −22dB 段也会错位。
- 音量：默认 `volume` 0.72。他说乐太大/某秒被盖住：整段床约 **−12dB**，再把音乐项在口播镜起止帧 `split_item`，那几段约 **−22dB**。不要停在 0.55。
- 淡入淡出字段是 **`fadeInDurationFrames` / `fadeOutDurationFrames`**（inspect 里就是这两个）。`updates` 写 `fadeIn` / `fade` / `fadeInFrames` 会被拒，轨上会硬切。**不要用短淡入淡出往黑里淡**（12 帧就是他说「突兀」的那种）；过渡用叠化或硬切。推近/拉远可 `builtin:effect-zoom` 的 `slow-push`/`slow-pull`，但那不是摇。
- 他报预览秒数要删：`split_item` 按那条成片的时间线帧切，`ripple` 删掉；画面短于音乐时把音乐收到画面终点，避免尾部黑帧。

## F. 低清预览 / 导出

- 他要「预览发给我」且要听/看调色：`local_export` h264 30fps，**不要只丢 viewer 拼图**（无声、不保证烘 LUT）。`outputPath` 用**相对路径**（落在系统 Videos/ChatCut；绝对路径会弹保存框卡住无人值守）。返回的 path 只是**排队**：体积稳定后再抽帧验色，然后才 `MEDIA:`。
- 导出常不写 SAR/DAR，手机会把正常像素压扁。发送前必须 SAR `1:1`、DAR `16:9`、`yuv420p`；他要 1080p 就重编 `scale=1920:1080,setsar=1,setdar=16/9,format=yuv420p`，用码率压进 Discord，**不要降到 720p**。不要只因抽帧比例正常就判播放正常。详见 [delivery.md](delivery.md)。
- 「高清传夸克」：ChatCut **1080p** 本地导出（带垫乐）→ 确认调色已烘进（B 节验收 / `lut3d` 兜底）→ 按 [delivery.md](delivery.md)「夸克无损归档」走。

## G. Relink（MCP 没有 Relink）

照片被分进 `00_待删除`/`01_待复核`/`02_优秀`/`03_普通` 或改名后会断链。让用户在 Desktop 素材库空白处右键 **Relink N Missing Media**，选一个仍用**原文件名**的夹。

- Relink 认**完整原文件名**。只加前缀的 `[prefix]__IMG_….jpg`，原名在 `__` **后面**——直接选整理后的根目录对不上这几张。
- 还剩 N 张 missing：先找 `__` 后的基名，按原名**拷**进一个小夹（不要 symlink），再 Relink 那一夹。
- 素材库里**已从成片拿掉**的静帧也算进 N。对全部静帧，不只对时间线。
- 断链后让用户 Relink，**不要 `push_asset` 再铺一遍时间线**。

## H. Antigravity 派活（他点名「指挥 Antigravity / 让 agy 用 ChatCut」）

Hermes **只预检 + 写任务书**，不要自己当剪辑手铺时间线。加载 `antigravity-cli`。

**预检清单**：ChatCut.app 开着、`agy mcp list` 正常、`permissions.allow` 含 `mcp(chatcut_desktop/*)`、素材夹已挂。

- 把**绝对路径**写进 prompt；**任务书必须同时锁定静帧绝对路径 + `VID_` 路径**，禁止只 push 视频（用户纠正过「不能只放视频」）。只导入 `02_优秀`+`03_普通` 的 `VID_`（不要 LRV、不要 `00_待删除`）。
- 已有同名空项目就 `target_project`，不要再 `create_project`。若正在跑一份只堆视频的 `agy -p`：**先停掉**再 `--new-project` 重派，不要 `--continue`。
- 无头模式任务书写死**只用 ChatCut MCP**：`permissions.allow` 只有 MCP 时，一调 RunCommand 会被直接拒绝并退出。
- 用脚本 `exec agy`，**不要 `$(cat)` 加重定向**——壳结束会推一条 exit 为空的完成通知，本体还在或已另死。
- `--print-timeout` 到点是半截；验证用 `read_project` / 时间线，**不要信 agy stdout**。

## I. 不要清单

- 不要整夹 `push_asset`；不要用网上别人的 LUT；不要在 ChatCut 里对照片套 I-Log cube。
- 相似两段楼梯（走上/跑）他说只要后一段就删前一段；碑刻突兀就拿掉（更多取舍见 [preferences.md](preferences.md)「镜头取舍」）。
