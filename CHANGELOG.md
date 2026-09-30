# CHANGELOG

## v2.5.1 (2026-09-30)
- testing.md 口径修订：T1 改用整幅 dx 判据（8-bit 量化下窄窗零差值≠重复帧）；T5 上限改为 T4×0.95（固定 80k 音频下 ×0.9 码率只缩约 7.5% 总大小）。
- check_delivery.sh：修复 bash 3.2 把全角字符吞进变量名的问题（只在 FAIL 分支触发，会导致报告崩溃而不是报 FAIL）；新增负例 T8。
- export_discord.sh：3 次都超限时把输出改名为 *_OVERLIMIT，避免被误当交付件发出。
- testing.md：对照改为金标准 sha256/MD5 表，不再引用 commit hash（本地仓与公开仓 hash 不同）。
## v2.5.0 (2026-09-29)
- pan_still.sh：静帧输入补 -framerate 30（原 25fps 读图、30fps 输出，每 5 帧重复 1 帧，平移会顿）；static 默认改为 cover（原 contain 会加黑边），新增 --fit cover|contain。
- export_discord.sh：单遍 ABR → two-pass；超 10MB 自动 ×0.9 降码率重试，最多 2 次，仍超限则报错退出；新增测试用环境变量 PVC_DISCORD_LIMIT_BYTES。
- mix_bgm.sh：alimiter 0.95 → 0.89（≈−1 dBFS，给 AAC 峰值回弹留余量）。只影响瞬时峰值，不改变音色和响度，用户同意不出 A/B（"有问题可以音量小一点"）。
- 跨平台：stat -f %z → wc -c。
- 文档同步：testing.md（v2.5.0 验证点）、ffmpeg-recipes.md、preferences.md、SKILL.md §5、README。
## v2.4.2 (2026-09-29)
- 文档一致性清理：默认 BGM 已改为木吉他，合成器 v3 在 preferences/SKILL/ffmpeg-recipes/README 中统一标为"备用，非默认"。
- 修正抢旁白时的补救顺序：先换备选命令，再降 2 dB（原先建议换 finger/plain，与稀疏方向相反）。
- 换调规则：每天只换 seed，调固定 D（用户选定；换调需另出试听件）。
- SKILL.md 的默认命令指引从 §5 脚本表移到 §2 默认偏好。
- README：脚本数改为 7，补上 fluidsynth/sf2 依赖。
## v2.4.1 (2026-09-29)
- 用户试听选定：默认 BGM = 木吉他尼龙弦 sparse（88 BPM）；安静场景备选 = sparse 80 BPM / density 0.6 / reverb 0.5。
- 纯文档改动：preferences.md、SKILL.md 流程措辞、ffmpeg-recipes.md、版本号。代码未动。
## v2.4.0 (2026-09-29)
- gen_bgm_guitar.py v1.1.0：新增 --pattern sparse（稀疏指弹，每小节 2–5 个音）。mix/finger/strum 输出不变（回归 j）。
- 起因：用户试听 v2.3.0，尼龙弦最好，但太密、太热闹。
- 待用户：试听三个尼龙弦稀疏候选，并在 preferences.md 填"当前默认"。
## v2.3.0 (2026-09-29)
- 撤回 Karplus-Strong 合成的 acoustic 预设（用户试听判定不可用）。scripts/gen_bgm.py 恢复为 457e704（v3.0.0）原文件，default/plain/lively 输出不变。
- 新增 scripts/gen_bgm_guitar.py v1.0.0：程序作曲 → MIDI → fluidsynth + FluidR3_GM 采样渲染。
  - D 调开放和弦，Travis 指弹/轻扫交替，每 8 小节"喘口气"，结尾 A→D。
  - 自检：无小三度，含大三度或 sus4，全部音在调内。
  - 选项：--pattern、--guitar、--print-chords、--midi-out。
- 新依赖：fluidsynth 2.x、FluidR3_GM.sf2（MIT，不入库，PVC_SF2 指定），见 references/third-party.md。
- 文档同步：preferences.md、testing.md、SKILL.md §5、README.md、ffmpeg-recipes.md。
- 待用户：试听 guitar-mix/finger/nylon，并在 preferences.md 填"当前默认"。
- gen_bgm_guitar.py：--sf2 显式指定时不再回退到 PVC_SF2/默认路径（回归 h 发现）。
## v2.2.0（2026-09-29）

新增第四个 BGM 预设 `acoustic`（木吉他）。gen_bgm.py 升到 v3.1.0。

- 音色：Karplus-Strong 物理弦模型（噪声+三角激励、拨弦位置梳状滤波、频率相关衰减、±2 音分微走音）+ 木箱共鸣（约 100/200/400/600/1050Hz 共鸣峰，左右略不同）。
- 演奏：真实开放和弦把位（D、D6、G、Gadd9、A、Asus4，按 capo 思路移调）；A 段 Travis 指弹，B 段轻扫弦（下 · 下上 · 上下上），喘口气段捏弦后让它响；每根弦同一时间只响一个音，同弦再拨或换和弦就闷掉。
- 新参数：`--instrument synth|guitar`、`--strum/--no-strum`；`--seed` 要求 ≥ 0。
- **default / plain / lively 输出与 v3.0.0 逐字节相同**（回归已比对 md5）。
- 文档同步：preferences.md、testing.md、SKILL.md（§5 + version）、README.md（清掉 v2 描述）、ffmpeg-recipes.md。

### 待 用户 决定
- 默认预设：在 default / plain / lively / acoustic 中选定。
## v2.1.0（2026-09-29）

BGM 生成器换成 v3（指弹拨弦 + 短贝斯 + 稀疏钟琴 + 很轻的沙锤 + 小房间混响）。v2 原样移到 `scripts/legacy/gen_bgm_v2.py`，只供 `--style quiet` 转调使用。

### v2 弃用原因（试听被评价为阴郁）

- (a) `pluck_base = 62 + root_pc`：拨弦比主调高一个全音（D 调弹成 E 五声，G# 撞 IV 和弦的 G）。
- (b) 垫子是 D2/A1 纯正弦密集三和弦，低音区发糊发闷。
- (c) 和弦形状随机抽到 power/sus4，约一半小节没有三度。
- (d) 10s 一个和弦、无律动、无混响、每小节淡到 0。

### 变更

- 新增 `--preset default|plain|lively`；单独给的参数会覆盖预设。
- 内置两道自检（失败就非零退出、不出文件）：和弦不得含小三度且必须有大三度/挂四；所有音必须在主调大调音阶内。
- `--print-chords` 改成只作曲不渲染，输出 **MIDI 整数**（v2 输出 Hz），测试断言已同步更新。
- 删掉 `--bar-gap`、`--bass` 参数（v3 不再使用长垫）。
- 文档同步：preferences.md「BGM 口味」、testing.md「gen_bgm.py 验证点 / 试听件」、SKILL.md §5、ffmpeg-recipes.md「垫乐」。

### 待 用户 决定

- 默认预设：试听 default / plain / lively 后选定。
## v2.0.0（2026-09-28）

重构：规则按主题拆进 `references/`，每条只写一处；命令统一 1080p；脚本从旧模板目录迁到 `scripts/` 并修 3 个 BGM bug；冲突按 用户 裁决改（C1–C5）。旧版整体备份在 `../personal-vlog-cut.bak-20260928/`。

### 裁决（用户 2026-09-28 任务书）

- **C1 结尾字位置**：放天空/画面上方空处，不居中、不放下沿（旧 `recut-and-bgm.md` 的「居中」作废）。开头三句仍画面中下；片头日标题放天空、避开脸和牌匾。
- **C2 字幕码率链**：字幕先烧高码率母版 `vN_sub.mp4`，再 `export_discord.sh` 另出 Discord 版（约 550k 按片长算）。「一次编进 Discord 版 + 1100k」作废。
- **C3 分辨率**：所有命令 1920×1080；720p 只在「LRV 仅供查看」上下文。
- **C4 单段静音**：`apad` 到视频时长（`mute_segment.sh`），`anullsrc + -shortest` 作废。
- **C5 横图慢移**：锁 y 只移 x（`pan_still.sh`），x/y 同移作废。

### 修掉的 bug（脚本）

- `gen_bgm.py`：seed 真正生效（旧 `RandomState(41)` 从未被用）；小调走向清除（旧 `[47,54,57,62]` 是 Bm7，与 "No minor" 矛盾）；bright 去掉 IIR 一阶低通逐样本循环与厚低音（「呜呜」来源），按 `--bass` 开关默认关；输出改 48kHz 与混音链一致（旧 44.1k）；quiet 里的 Dm（`[38,50,53,57]`）一并换成大调走向（新发现，见下）。
- 其余脚本新增：`--help`、非零退出、不静默出空文件、交付体检 `check_delivery.sh`。

### 事件细节（从正文下沉，正文只留原则）

- **「某村 / 某镇」**：clip 时长加总会漂，把 54 秒的「某村」算成「某镇」；复用 `14.mp4` 当「某镇」，文件里其实是「某村」。→ 原则：报秒数对 `_dc.mp4` 抽帧（seek 后置）；复用 `NN.mp4` 先抽帧认画面。
- **「女巫眼球」**：地球仪/怪物件无关特写曾因「有画面」被留下。→ 原则：无关特写丢掉。
- **「甲地名 / 乙地名」**：地名用了素材文件夹里的「乙地名」，实际是「甲地名」。→ 原则：地名以用户说的为准。
- **「家人A，然后家人B」**：结尾合照被按文件时间重排，顺序错了。→ 原则：合照听他指定的两张和顺序。

### 规则映射核对（旧 → 新，防丢）

状态：保留 = 原样搬；合并 = 多条并一处；改写 = 表述改、语义不变；按裁决修改 = 按 C1–C5 或 bug 修复改。

| # | 旧规则摘要 | 新位置 | 状态 |
|---|---|---|---|
| R001 | 「就用今天的素材」≠素材已在磁盘 | footage-sources.md「等素材」 | 保留 |
| R002 | 没给路径/网盘/频道文件就停，等他丢 | footage-sources.md「等素材」 | 保留 |
| R003 | 不扫 Downloads/Desktop/Movies/Photos/Discord 历史猜山 | footage-sources.md「等素材」 | 保留 |
| R004 | 移动硬盘：先 /Volumes 再精确路径探测，不 listdir 整卷根 | footage-sources.md「移动硬盘探测」 | 保留 |
| R005 | exists≠已读；列举卡住就停，不反复打盘，报证据盲区 | footage-sources.md「移动硬盘探测」 | 保留 |
| R006 | 中途被告知「素材还没给你」立刻停搜 | footage-sources.md「等素材」 | 保留 |
| R007 | 时长 2–3 分钟；钉死表上限 4 分钟不删镜头 | preferences.md「时长」 | 保留 |
| R008 | 不配旁白≠静音；自带说话/脚步/风必留 | preferences.md「默认偏好」 | 保留 |
| R009 | 明说某段不要原声：只静那几切，BGM 留 | preferences.md「默认偏好」 | 保留 |
| R010 | 杂音含别人讲话；本人讲话必留；开场「mean 很响」是他在说话 | preferences.md + recut.md「静音动刀前」 | 改写（mean→mean_volume） |
| R011 | 报「噼里啪啦」静占那几秒的那一切；−4dB 尖峰是麦擦不是脚步 | recut.md「静音动刀前」 | 保留 |
| R012 | 他说「照片」可能指成片里的视频段，先对画面再静音 | recut.md「静音动刀前」 | 保留 |
| R013 | 晃太快的不要进（杖头乱甩/近距手/快切台阶） | preferences.md「镜头取舍」 | 保留 |
| R014 | 下山收不要 12s 一刀切走，至少约 20s | preferences.md「镜头取舍」 | 保留 |
| R015 | 本人讲话段多留；4K 对不准不拿走路空镜充数 | preferences.md「镜头取舍」 | 保留 |
| R016 | 开场第二镜不要脸部特写 | preferences.md「镜头取舍」 | 保留 |
| R017 | 不要地理论文/机身参数/摄影哲学/感谢大自然 | preferences.md「文案」 | 保留 |
| R018 | 地名听用户的，不用文件夹/文件名 | preferences.md「镜头取舍」 | 保留 |
| R019 | Discord 短句短段、结论先行 | preferences.md「默认偏好」 | 保留 |
| R020 | 「帮我写个文案」默认小红书：标题+两三句+#地名 #爬山 | SKILL.md §6 + preferences.md「文案」 | 保留 |
| R021 | 话题标签不上屏 | preferences.md「字体与字幕」 | 保留 |
| R022 | 开头三句 1–6.5s 叠开场、画面中下、手札体 | preferences.md「字体与字幕」 | 保留 |
| R023 | 禁止 Heiti/STHeiti/黑体；手札 Hannotate.ttc index=0 | preferences.md「字体与字幕」 | 保留 |
| R024 | 字体 find /System/Library/AssetsV2，不硬编码哈希；找不到报错不回退黑体 | preferences.md「字体与字幕」 | 保留 |
| R025 | 片头日标题：手札、大、可直烧、放天空不盖脸/牌匾 | preferences.md「字体与字幕」 | 保留 |
| R026 | 片头 PNG 铺视频轨上面、type=image、order:1、9 格 viewer 不算、导出抽帧认头 | chatcut.md「D 片头日标题」 | 保留 |
| R027 | 结尾字先报再烧；「按惯例加下山了」=点头；气质像「下山了」 | preferences.md「结尾字流程」 | 保留 |
| R028 | 结尾字位置「居中」 | preferences.md「字体与字幕」 | 按裁决修改（C1→放天空/上方空处） |
| R029 | 字只叠开场路/景，进下一镜（尤其脸）前退掉 | preferences.md「字体与字幕」 | 保留 |
| R030 | 「先讲分析」只交付判断不开剪 | analysis-first.md | 保留 |
| R031 | 清单：张数/段数/时长/时段 | analysis-first.md | 保留 |
| R032 | 照片抽代表帧接触表；LRV 抽 1fps；百张不宣称全看 | analysis-first.md | 保留 |
| R033 | 没看成的长视频写证据盲区，禁止脑补 | analysis-first.md | 保留 |
| R034 | 一天两地按两段明信片 | analysis-first.md | 保留 |
| R035 | 02_优秀先吃、03_普通补主题、00_待删除不进 | analysis-first.md | 保留 |
| R036 | 空车/空镜与已有人同项目不留两张 | analysis-first.md | 保留 |
| R037 | 预选表时长用区间（照片×4–5s+稳的几秒） | analysis-first.md | 保留 |
| R038 | 表估 <2:30 补 2–3 张不重复主题照片，不用空镜凑秒 | analysis-first.md | 保留 |
| R039 | 「先剪一般看看」：超限先交，说清哪两段没进 | analysis-first.md | 保留 |
| R040 | 点名网盘加载 quark-netdisk-ops | footage-sources.md「夸克」+ SKILL.md §10 | 保留 |
| R041 | search 只吐照片，必须 browse 再判断有无视频 | footage-sources.md「夸克」 | 保留 |
| R042 | 整句夹名 search dir 0 条：只用日期前缀；用用户的地名说话 | footage-sources.md「夸克」 | 保留 |
| R043 | download 50MB 上限；改拉 LRV；LRV 也超限不重试 | footage-sources.md「夸克」 | 保留 |
| R044 | 不拿搜索预览 JPG 开剪/不说「只有照片」 | footage-sources.md「夸克」 | 保留 |
| R045 | 成片只从 VID_ 下刀，LRV 只看内容 | footage-sources.md「LRV/VID」 | 保留 |
| R046 | 延时 VID 常 ~2s/60 帧，先 ffprobe | footage-sources.md「LRV/VID」 | 保留 |
| R047 | 色彩先抽帧；bt709 不判正片；正片不二次还原 | insta360-color.md | 保留 |
| R048 | I-Log 官方 cube 路径；只挂 VID_；照片不套 log | insta360-color.md | 保留 |
| R049 | 没 Studio 才轻 eq+暖；没官方 cube 不乱套别人 LUT | insta360-color.md | 保留 |
| R050 | 说录了正片就按已烘好，除非帧打脸 | insta360-color.md | 保留 |
| R051 | Studio：判定完立刻进时间线/导出；空工程=没剪完 | insta360-color.md | 保留 |
| R052 | Studio 里 JPG 不能裁、广角 MP4 不能变焦 | insta360-color.md | 保留 |
| R053 | 4K50 HEVC input-seek 漂移：晚段 -ss 放 -i 后 | ffmpeg-recipes.md「4K50 seek」 | 保留 |
| R054 | 抽完段看 VID 首帧再 concat；LRV 对上≠VID 同一幅 | footage-sources.md「LRV/VID」 | 保留 |
| R055 | Antigravity：只预检+任务书，静帧+VID 绝对路径，不能只放视频 | chatcut.md「H 派活」 | 保留 |
| R056 | 无头模式只用 ChatCut MCP；RunCommand 会被拒 | chatcut.md「H 派活」 | 保留 |
| R057 | 用脚本 exec agy，不用 $(cat) 加重定向（壳结束推空 exit） | chatcut.md「H 派活」 | 改写（删零宽字符） |
| R058 | --print-timeout 到点是半截，以 read_project 为准；不信 agy stdout | chatcut.md「H 派活」 | 保留 |
| R059 | 已有同名空项目 target_project；只堆视频的 agy 先停再 --new-project | chatcut.md「H 派活」 | 保留 |
| R060 | 没点名 Antigravity 走 Desktop MCP，不改跑 ffmpeg concat | SKILL.md §8 + chatcut.md | 保留 |
| R061 | 先锁 1920×1080/16:9 画幅再上第一张照片 | chatcut.md「A2」 | 保留 |
| R062 | 照片扁=4:3 拉宽；不拉伸不中心裁；contain/按内容摇 | chatcut.md「C」+ delivery.md | 合并 |
| R063 | 说淡入淡出突兀：不用短 fade 往黑淡，用叠化/硬切；slow-push 不是摇 | chatcut.md「E」 | 保留 |
| R064 | 静帧运镜按画面定方向速度；脸近景不动、宽景横摇、竖构图下往上 8s | preferences.md「照片时长」+ recut.md | 合并 |
| R065 | 4:3 横摇先放大到宽>1920、锁 y 移 x；scale=-2:1080 空流 | ffmpeg-recipes.md「横图慢移」+ pan_still.sh | 按裁决修改（C5） |
| R066 | 运镜做完抽首尾帧认人 | recut.md + pan_still.sh（自动抽） | 合并 |
| R067 | ChatCut 导出常不写 SAR；1080p 不改 720p；MEDIA 前 setsar/setdar/yuv420p | delivery.md | 合并 |
| R068 | Discord 压到 8–10MB 用码率不降分辨率 | delivery.md | 保留 |
| R069 | LUT 单独 push、type=pixel-effect、挂上≠套上、空壳判据 | chatcut.md「B」 | 保留 |
| R070 | 验收只看导出 mp4 口播帧；9 格 viewer/attachedEffects 不算 | chatcut.md「B」 | 保留 |
| R071 | lut3d 兜底：enable 只盖 VID_ 帧区间；静帧/字幕不套 | chatcut.md「B」 | 保留 |
| R072 | JPG 进库前 EXIF 转置（ChatCut 不读方向） | chatcut.md「C」 | 保留 |
| R073 | 超大全景先缩 ≤3840×2160 再 push（viewer 打崩 native host） | chatcut.md「C」 | 保留 |
| R074 | 竖图 top 挪人、每改认头、不 letterbox、不拿 zoom 曲线当上摇 | chatcut.md「C」 | 保留 |
| R075 | 照片默认 4s/开场收尾 5s/开场特例 8s；0.5s 交叉溶解 | preferences.md「照片时长」+ chatcut.md「A6」 | 合并 |
| R076 | 字不全 contain 或换更全一张，不靠淡入淡出缓字 | preferences.md + chatcut.md「C」 | 合并 |
| R077 | VID_ 挂官方 cube 后不叠索尼/佳能 Log LUT | insta360-color.md + chatcut.md「B」 | 合并 |
| R078 | 相似两段（走上/跑、正面/背影）说只要一段就删另一段 | preferences.md + chatcut.md「I」 | 合并 |
| R079 | Relink 流程：完整原文件名、__ 后基名、拷小夹、已删源也占 N | chatcut.md「G」 | 保留 |
| R080 | 「高清传夸克」：1080p 带垫乐导出、cube 烘验、YYYYMMDD_地名_成片 | chatcut.md「F」+ delivery.md | 合并 |
| R081 | 借感觉先问清、只借 2–3 条、丢片长/旁白/升华 | linksphotograph.md + SKILL.md §4 | 保留 |
| R082 | 剪辑配方五步（开夺→走→小意外→山顶→下山收） | SKILL.md §4 | 改写（「开夺」→「开场」） |
| R083 | Recut 看画面不看注释 | recut.md | 保留 |
| R084 | 报秒数对 _dc.mp4 抽帧、seek 放 -i 后 | recut.md | 保留 |
| R085 | 复用 NN.mp4 先抽帧（编号≠内容） | recut.md | 保留 |
| R086 | 「方向不对就别放」：不硬 rotate 进片 | recut.md | 保留 |
| R087 | 结尾合照听指定两张和顺序；「最后有没有好合照」≠时间轴最后一张 | preferences.md「镜头取舍」 | 保留 |
| R088 | 古镇生活气息；招牌特写不要就拿掉 | preferences.md「镜头取舍」 | 保留 |
| R089 | 无关特写丢掉（盆栽花/女巫眼球）；碑刻突兀拿掉；花虫可停顿 | preferences.md「镜头取舍」 | 保留 |
| R090 | 放慢阶梯 0.65–0.7→0.5→0.4，setpts 不插帧 | preferences.md「放慢倍率阶梯」 | 保留 |
| R091 | 两段同压缩倍率用同一 setpts，之后可分开 | preferences.md「放慢倍率阶梯」 | 保留 |
| R092 | 竖摇太快→8s+停 0.8s，crop+t，不用 zoompan on/d | recut.md + ffmpeg-recipes.md「竖图上摇」 | 合并 |
| R093 | 1080p 不要 zoompan | recut.md + ffmpeg-recipes.md「通用红线」 | 保留 |
| R094 | 只改点名的那几张：crop 钉顶不整片 letterbox | recut.md | 保留 |
| R095 | deshake rx/ry 必须 16 的倍数，后 crop 回画幅 | recut.md + ffmpeg-recipes.md「手持防抖」 | 合并 |
| R096 | anullsrc+-shortest 每切短十几毫秒不同步→apad | ffmpeg-recipes.md + mute_segment.sh | 按裁决修改（C4） |
| R097 | 同条 VID 多切按文件名拍摄时间+片内秒数排 | recut.md | 保留 |
| R098 | 「不要局限于这个时间」可超 2–3 分钟 | recut.md + preferences.md | 合并 |
| R099 | 按旧成片用原片重剪，不借机重做结构 | recut.md | 保留 |
| R100 | 复盘只重编被改的切，其余 copy concat | recut.md | 保留 |
| R101 | Discord 丢照片按地理/叙事插入，不堆片尾 | recut.md | 保留 |
| R102 | 点名碑/路名要在照片里找那个字 | recut.md | 保留 |
| R103 | 「坐在石头上要运镜」用成片原镜抽帧，不另找像的 | recut.md | 保留 |
| R104 | 「大门口自拍」收尾要有人站门/殿前 | recut.md | 保留 |
| R105 | 后半段少：下午镜按 4s 插下山前，不拿上午走路镜充 | recut.md | 保留 |
| R106 | 按拍摄时间铺：文件名时分秒重排，删光 V1 再 alignTo:track-end | recut.md + chatcut.md「A6」 | 合并 |
| R107 | 报秒数区间删段：切开 ripple 删；尾巴删掉；音乐收到画面终点 | recut.md + chatcut.md「E」 | 合并 |
| R108 | BGM 垫在声下不换声轨；照片段乐清楚是预期 | preferences.md「BGM 口味」 | 保留 |
| R109 | 淡入 ~2.6s 淡出 ~4.3s（FADE_START 由片长算） | preferences.md + mix_bgm.sh | 合并 |
| R110 | 原创器乐、不拆商业曲 | preferences.md「BGM 口味」 | 保留 |
| R111 | bright 模板口味：大调、10s 小节一两拨、不 0.5s ostinato | preferences.md「BGM 口味」+ gen_bgm.py | 合并 |
| R112 | quiet 模板被评「诡异」，只在要发闷时用 | preferences.md「BGM 口味」+ gen_bgm.py --help | 保留 |
| R113 | 呜呜不好听：不要 IIR、薄垫、音高抬高 | preferences.md + gen_bgm.py | 按裁决修改（bug3 去 IIR/厚低音） |
| R114 | volume 0.72；整床 −12dB；口播段 −22dB；不停 0.55 | preferences.md + chatcut.md「E」 | 合并 |
| R115 | 只从没垫过的 vN.mp4 混；_bgm 上不叠第二层 | preferences.md + mix_bgm.sh（校验报错） | 合并 |
| R116 | 加镜后音乐 durationFrames 收到源片时长；开场加长时 sourceIn 同移 | chatcut.md「E」 | 保留 |
| R117 | 每天换 seed 和调，不复用上趟 wav | preferences.md + gen_bgm.py | 保留（seed bug 修复） |
| R118 | BGM 短于成片：acrossfade 接同条，禁 apad | ffmpeg-recipes.md + mix_bgm.sh | 保留 |
| R119 | sidechain 链参数（1.18/highpass140/lowpass10000/0.72/压缩参数） | mix_bgm.sh | 保留 |
| R120 | amix normalize=0 后补 alimiter=limit=0.95 | mix_bgm.sh | 改写（新增防削波） |
| R121 | 生成夏日垫乐的旧模板（gen_summer_bright / gen_summer 两个 py） | scripts/gen_bgm.py | 合并（旧模板目录删除） |
| R122 | 片上字幕 Pillow 透明 PNG + enable=；不用 fade+setpts 挪 PNG | ffmpeg-recipes.md「片上字幕」 | 保留 |
| R123 | 叠字命令一次编进 Discord 版、-b:v 1100k | ffmpeg-recipes.md「片上字幕」 | 按裁决修改（C2→先烧 vN_sub.mp4 母版） |
| R124 | overlay alpha 嵌套逗号写 -filter_complex_script | ffmpeg-recipes.md「通用红线」 | 保留 |
| R125 | 手机延时放慢命令（fps=30+setpts、补静音轨） | ffmpeg-recipes.md「放慢」 | 按裁决修改（C3/C4） |
| R126 | 竖图上摇命令（zoompan d 不是变量） | ffmpeg-recipes.md「竖图上摇」 | 按裁决修改（C3→1080p） |
| R127 | 横图慢移命令 x/y 同移 | pan_still.sh + ffmpeg-recipes.md | 按裁决修改（C5） |
| R128 | 单段静音命令（anullsrc+-shortest） | mute_segment.sh | 按裁决修改（C4） |
| R129 | concat 用 filter 同一时钟；copy-concat DTS 以 re-encode 为准 | ffmpeg-recipes.md「concat」+ recut.md | 合并 |
| R130 | 发出去验收是频道链接不是本地路径 | delivery.md | 保留 |
| R131 | MEDIA 成片先说时长和用了哪几段 | delivery.md | 保留 |
| R132 | 接触表 MEDIA 不上屏→ASCII 路径 Bot API multipart 上传当前 thread | delivery.md | 保留 |
| R133 | 1100k 十几 MB 空失败→8–10MB、ASCII 名、别重传原文件 | delivery.md | 按裁决修改（C2） |
| R134 | 压扁排查：整片 vs 只照片；yuv444/High4:4:4 手机播不了 | delivery.md | 保留 |
| R135 | 无损归档夸克步骤（search dir→browse --all→upload→核对） | delivery.md | 保留 |
| R136 | 归档传 vN_bgm.mp4 不传 _dc；当天夹不在就新建 YYYYMMDD 地名 | delivery.md | 保留 |
| R137 | 要 Studio 剪就加载 insta360-studio，算换手不用 ffmpeg 充数 | SKILL.md §8/§10 + insta360-color.md | 保留 |
| R138 | 4K50 seek 早段可 input-seek | ffmpeg-recipes.md「4K50 seek」 | 保留 |
| R139 | linksphotograph.md 全部（Borrow/Do not borrow/full grammar） | linksphotograph.md | 保留 |
| R140 | chatcut-postcard 步骤顺序表 11 步 | chatcut.md「A」 | 保留 |
| R141 | fit:cover 不和 crop* 同传；crop* 归零清侧裁 | chatcut.md「A6/A8」 | 保留 |
| R142 | tr-cross-dissolve 15f、0 余量硬切、outgoingItemType/incomingItemType | chatcut.md「A9」 | 保留 |
| R143 | preview_timeline viewerFrameCount ≤9、SIGABRT 缩区间 | chatcut.md「A10」 | 保留 |
| R144 | muted:true→decibelAdjustment:-60 | chatcut.md「A7」 | 保留 |
| R145 | 低清预览 local_export 相对路径、返回是排队、体积稳定再抽帧 | chatcut.md「F」 | 保留 |
| R146 | 海报/大字被 cover 切掉的处理 | chatcut.md「C」 | 保留 |
| R147 | Music 轨首尾相接、不重叠、fadeInDurationFrames 字段名 | chatcut.md「E」 | 保留 |
| R148 | 不要清单（整夹 push、别人 LUT、照片套 log） | chatcut.md「I」 | 保留 |
| R149 | frontmatter name/description/version | SKILL.md | 改写（任务书指定文案） |

统计：共 **149** 条（程序化点数）。保留 114、合并 20、改写 5、按裁决修改 10。**丢失 0**（无「新位置」的行 0 条）。

### 新发现、待 用户 决定（本文没裁）

1. **quiet 模板里有一条 Dm 走向**（`[38,50,53,57]`）——「不要小调」规则字面上只针对默认 bright，但任务书 4.1 说候选走向只用 I/IV/V。已按大调走向实现（听感会比旧 quiet 亮一点点）。若想保留旧 quiet 的阴郁感，说一声我改回。
2. **旧 bright 的拨弦音表含 B（midi 71）**，D 大调五声无碍；只是旧注释写「D/G-ish」而实际走向含 A——无冲突，已按 D 大调实现。
3. **亮度/响度**：旧模板峰值归一到 0.22，新版规格「峰值约 −3 dBFS（0.7）」。新版更响，是按任务书 4.1 执行的；A/B 试听时请留意整体电平。
