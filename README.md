# personal-vlog-cut

> 剪个人爬山 / 旅行 / 明信片 vlog 的 agent skill（v2.5.5）：看素材先分析、粗剪、按秒数重剪、生成与混垫乐、烧手札字幕、写小红书文案、发 Discord、传夸克归档。
>
> **本仓库是脱敏公开版**：执行规则与本地使用版完全一致，仅地名与家人称谓做了泛化；带真实案例的踩坑实录留在本地，不公开。

## 这是什么

一套给 Hermes Agent 用的个人旅行短 vlog 剪辑工作流。目标是**一张明信片**：2–3 分钟、留得住现场声、结尾停在一个具体画面——不是 20 分钟旅拍，不加旁白，不喊口号。

核心工作方式：

- **先讲分析，再开剪**：清单 → 抽帧看画面 → 写明证据盲区 → 预选表
- **看画面，不看注释**：用户报的秒数以他看到的成片为准，改前先抽帧认画面
- **偏好零丢失**：每条用户纠正都有落点，149 条规则映射表见 CHANGELOG.md
- **每条规则只写一处**：SKILL.md 只放流程和高频默认值，细节在 references/
- **会改变声音的修改一律出 A/B 两版**给用户听了再定，不自己拍板

## 目录结构

- `SKILL.md` — 流程总览与最高频默认值（入口）
- `CHANGELOG.md` — 版本记录、冲突裁决（C1–C5）、规则映射核对表
- `references/` — 分主题细则：审美偏好 / 先讲分析 / 素材来源 / 调色判定 / ffmpeg 配方 / ChatCut / 重剪 / 交付 / 借感觉 / 回归验证
- `scripts/` — 七个可执行脚本（见下）

## 脚本

| 脚本 | 用途 |
|---|---|
| `gen_bgm_guitar.py` | 木吉他 BGM，SoundFont 采样渲染（依赖 fluidsynth 与 FluidR3_GM.sf2，音色文件不在仓库内，见 references/third-party.md）；**当前默认 BGM** |
| `gen_bgm.py` | 生成原创垫乐 v3：`--seed` 必填（同 seed 可复现）；`--preset default\|plain\|lively`（合成指弹风）；只用大调/挂留和弦，内置音阶自检；旧 v2 在 `scripts/legacy/` |
| `pan_still.sh` | 静帧 → 16:9 1080p 运镜 mp4：横摇锁 y 只移 x、竖摇从下往上、EXIF 方向校正、余量不足自动退 static；static 默认 cover（裁满），--fit contain 可选；--max-speed 限速（默认 10px/帧） |
| `mix_bgm.sh` | 原声 + 垫乐 sidechain 混音（末尾 `alimiter` 防削波），输出归档母版 `vN_bgm.mp4` |
| `mute_segment.sh` | 单切静音：`apad` 到视频时长，音画时长差 ≤ 1 帧 |
| `export_discord.sh` | 按片长自动算码率，two-pass 压到约 9MB，超 10MB 自动降码率重试 2 次、1080p、非 ASCII 文件名确定性改写（残留 ASCII + cksum 哈希）；超限输出改名 _OVERLIMIT |
| `check_delivery.sh` | 交付前体检（SAR/DAR/色深/峰值等逐项 PASS/FAIL）+ 均匀抽 6 帧接触表 |

所有脚本都有 `--help`；出错返回非零并打印原因，不静默出空文件。

## 依赖

- `ffmpeg` / `ffprobe`
- Python 3 + numpy（`gen_bgm.py`，优先用带 numpy 的解释器，找不到会报错）
- fluidsynth 2.x + FluidR3_GM.sf2（MIT，约 141MB，不入库；用环境变量 PVC_SF2 指定路径，见 references/third-party.md）——`gen_bgm_guitar.py` 需要
- Pillow（`pan_still.sh` 的 EXIF 校正；没有也能跑，脚本会尝试 `uv run --with pillow`）
- macOS 手札字体 `Hannotate.ttc`（烧字幕用；找不到会报错停下，**不回退黑体**）

## 测试

改过 `scripts/` 后按 `references/testing.md` 跑回归：全部用 ffmpeg 合成素材（`testsrc2` / `sine` / `anullsrc`）在临时目录验证，不碰真实素材、移动硬盘、网盘。

- 判定值以 testing.md 开头的**金标准表**为准（BGM 脚本 sha256、WAV/MIDI 的 MD5 写死全文）；本地仓与公开仓 commit hash 不同，测试一律不引用 hash。
- 当前验证点：T1–T14（平移平滑度与限速、cover/contain、two-pass 与超限改名、热信号限幅、卫生扫描、金标准比对、参数校验等），含负例。
