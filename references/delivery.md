# delivery.md —— Discord 发送 / 接触表 / 夸克归档

> **什么时候读我**：要 `MEDIA:` 发成片、发缩略图/接触表、被说「压扁了」「传不上来」、或要把成片无损归档到夸克时。

## 基本验收

- 发出去的验收是**频道里能点的成片链接**，不是只报本地路径。
- 成片用 Discord `MEDIA:/absolute/path`。先说时长和用了哪几段，别写制作解说。
- 他要 Insta360 Studio 剪：加载 `insta360-studio`，算换手（见 [insta360-color.md](insta360-color.md)）。

## 压缩规格（Discord 版）

- **1920×1080**、`setsar=1,setdar=16/9,format=yuv420p`、`-movflags +faststart`、文件名**只用 ASCII**。
- 目标 **8–10MB**：按片长自动算视频码率（~550k video / 80k audio；片长超 3 分钟就把码率降到仍落在 10MB 内）。**不要再用 1100k 当 Discord 码率**（2 分钟左右会到十几 MB，传输几分钟后**空失败**——日志里 Failed to send media 没有错误字）。
- 直接用 `scripts/export_discord.sh`（自动算码率 + 调 `scripts/check_delivery.sh --discord`）。发不过来**不要拿原文件再传一遍**。
- 交付前体检逐项（分辨率、SAR/DAR、yuv420p、profile、音轨、音画时长差、大小、峰值）：`scripts/check_delivery.sh`，接触表抽帧**必须看一眼**（LUT 口播帧、标题窗口、结尾字）。

## 压扁排查

- 先分清**整片**扁还是**只有照片**扁。
- 整片扁且 SAR/DAR 为 N/A：导出没写像素比，手机会压扁。`MEDIA:` 前必须 `1:1` + `16:9` + `yuv420p`。他要 1080p 就 `scale=1920:1080,setsar=1,setdar=16/9,format=yuv420p`，用码率压到 8–10MB，**不要降到 720p**。
- 只有照片扁、视频正常：4:3 被拉宽，不要只重编 SAR；处理见 [chatcut.md](chatcut.md)「静帧进库」/ [recut.md](recut.md)。
- `yuv444` / High 4:4:4 手机播不了。

## 缩略图 / 接触表上传

- 预选缩略图 / 接触表 JPG：`MEDIA:` 常不上屏（他会说看不到图）。**不要再 `MEDIA:` 同一文件一遍**。
- 压成 **ASCII 路径**后用 Bot API `multipart/form-data` 上传到**当前 thread**（`--noproxy '*'`），看返回里有没有 `attachments`。

## 夸克无损归档（加载 `quark-netdisk-ops`）

- 上传**带垫乐、未压 Discord 的** `vN_bgm.mp4`（改名 `YYYYMMDD_地名_成片.mp4`），**不要 `_dc`、不要灰片导出**。ChatCut 线先确认调色已烘进（见 [chatcut.md](chatcut.md)「LUT」）。
- 步骤：`search --search-type dir` 日期前缀 → 同轮 `browse --all`（browse **没有** `--stdout-only`）→ `upload --parent-fid` 用**这一轮**的夹 fid → 再 search 文件名核对 size、只有一份。
- 当天夹不在、他要放到以前 vlog 同一处：按已有日期夹的**父目录**，新建 `YYYYMMDD 地名` 再挪进去，**不要留在「来自：Hermes」**。
