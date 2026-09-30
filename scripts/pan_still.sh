#!/usr/bin/env bash
# pan_still.sh — 静帧图 → 16:9 1920×1080 30fps yuv420p SAR 1:1 运镜 mp4
# 横摇锁 y 只移 x（裁决 C5）；竖摇从下往上；禁止 zoompan。
set -euo pipefail

usage() {
  cat <<'USAGE'
用法: pan_still.sh [选项] INPUT_IMAGE [OUTPUT.mp4]

把一张照片做成 16:9 1920×1080 30fps yuv420p、SAR 1:1 的 mp4。

选项:
  --mode static|hpan|vpan|auto   默认 auto（按画幅判断）
  --fit cover|contain             static 模式适配，默认 cover（裁满无黑边）
  --dur  秒                       默认 static/hpan=4、vpan=8；开场/收尾可手动 5
  --hold 秒                       竖摇起点停留，默认 0.8
  --dir  left|right|up            横摇方向（默认 right）/ 竖摇 up
  --anchor-y 0..1                 横摇锁定的 y 比例，默认 0.5
  --max-speed PX                  每帧最大平移像素，默认 10（必须 > 0；超限时只平移中间一段）
  -h, --help                      本帮助

规则:
  - 先做 EXIF 方向校正；宽超约 8K 的全景先缩小。
  - 横摇 y 固定在 anchor-y，只移 x；宽度余量 < 1920 的 10% 时自动退回 static 并提示。
  - 竖摇 scale=1920:-2，y 从下往上，起点停 hold 秒，顶上留一点余量。
  - 禁止 zoompan（1080p 小数变焦像整片在晃）。
  - --fit contain：画面里的字/主体被裁掉时用（用户偏好"字不全时 contain"）。
  - 结束后自动抽出首帧/尾帧 jpg 并打印路径（认人认头用）。
  - 出错返回非零，不会静默出空文件。
USAGE
}

MODE="auto"; DUR=""; HOLD="0.8"; DIR=""; ANCHOR="0.5"; FIT="cover"; MAXSPD="10"
POS=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0;;
    --mode) MODE="$2"; shift 2;;
    --dur) DUR="$2"; shift 2;;
    --hold) HOLD="$2"; shift 2;;
    --dir) DIR="$2"; shift 2;;
    --anchor-y) ANCHOR="$2"; shift 2;;
    --fit) FIT="$2"; shift 2;;
    --max-speed) MAXSPD="$2"; shift 2;;
    -*) echo "pan_still.sh: 未知参数 $1" >&2; usage >&2; exit 2;;
    *) POS+=("$1"); shift;;
  esac
done

[ ${#POS[@]} -ge 1 ] || { echo "pan_still.sh: 缺 INPUT_IMAGE" >&2; usage >&2; exit 2; }
IN="${POS[0]}"
OUT="${POS[1]:-}"
[ -f "$IN" ] || { echo "pan_still.sh: 输入不存在: $IN" >&2; exit 1; }
case "$MODE" in static|hpan|vpan|auto) ;; *) echo "pan_still.sh: 非法 --mode $MODE" >&2; exit 2;; esac
case "$FIT" in cover|contain) ;; *) echo "pan_still.sh: 非法 --fit ${FIT}（只支持 cover|contain）" >&2; exit 2;; esac
awk "BEGIN{exit !($MAXSPD>0)}" 2>/dev/null || { echo "pan_still.sh: 非法 --max-speed ${MAXSPD}（必须 > 0）" >&2; exit 2; }
awk "BEGIN{exit !($ANCHOR>=0 && $ANCHOR<=1)}" 2>/dev/null || { echo "pan_still.sh: 非法 --anchor-y ${ANCHOR}（必须 0..1）" >&2; exit 2; }
if [ -n "$DUR" ]; then
  awk "BEGIN{exit !($DUR>0)}" 2>/dev/null || { echo "pan_still.sh: 非法 --dur ${DUR}（必须 > 0）" >&2; exit 2; }
fi

FFMPEG="$(command -v ffmpeg || true)"; FFPROBE="$(command -v ffprobe || true)"
[ -n "$FFMPEG" ] && [ -n "$FFPROBE" ] || { echo "pan_still.sh: 需要 ffmpeg/ffprobe" >&2; exit 1; }

WORK="$(mktemp -d /tmp/pan_still.XXXXXX)"; trap 'rm -rf "$WORK"' EXIT

# 选一个带 Pillow 的 python（EXIF 方向校正用）
PY=""
for cand in "${PVC_PYTHON:-}" python3 /opt/homebrew/bin/python3.11 /usr/local/bin/python3; do
  [ -n "$cand" ] || continue
  P="$(command -v "$cand" 2>/dev/null || true)"; [ -n "$P" ] || continue
  if "$P" -c "import PIL" >/dev/null 2>&1; then PY="$P"; break; fi
done
UV="$(command -v uv || echo "$HOME/.hermes/bin/uv")"
if [ -z "$PY" ] && [ -x "$UV" ]; then PY="$UV run --with pillow python"; fi
[ -n "$PY" ] || { echo "pan_still.sh: 找不到带 Pillow 的 python（EXIF 校正需要）" >&2; exit 1; }

# 1) EXIF 方向校正（+ 首步落地为 png；打不开的图先走 sips 转换）
FIXED="$WORK/fixed.png"
if ! $PY - "$IN" "$FIXED" <<'PYEOF'
import sys
from PIL import Image, ImageOps
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src)
im = ImageOps.exif_transpose(im)
if im.mode not in ("RGB", "RGBA", "L"):
    im = im.convert("RGB")
im.save(dst)
PYEOF
then
  if command -v sips >/dev/null 2>&1; then
    sips -s format png "$IN" --out "$WORK/heic.png" >/dev/null 2>&1 \
      || { echo "pan_still.sh: sips 转换失败: $IN" >&2; exit 1; }
    $PY - "$WORK/heic.png" "$FIXED" <<'PYEOF' || { echo "pan_still.sh: EXIF 校正失败" >&2; exit 1; }
import sys
from PIL import Image, ImageOps
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src)
im = ImageOps.exif_transpose(im)
if im.mode not in ("RGB", "RGBA", "L"):
    im = im.convert("RGB")
im.save(dst)
PYEOF
  else
    echo "pan_still.sh: 打不开图片 ${IN}（HEIC 需要 macOS sips 或 pillow-heif）" >&2; exit 1
  fi
fi

# 2) 宽超约 8K 先缩
DIM="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$FIXED")"
W="${DIM%,*}"; H="${DIM#*,}"
SRC="$FIXED"
if [ "$W" -gt 8000 ]; then
  SRC="$WORK/small.png"
  "$FFMPEG" -y -v error -i "$FIXED" -vf "scale=8000:-2" "$SRC"
  DIM="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$SRC")"
  W="${DIM%,*}"; H="${DIM#*,}"
  echo "pan_still.sh: 全景 $W 宽，已先缩到 8000 以内"
fi

MARGIN_MIN=192   # 1920 的 10%
case "$FIT" in
  cover)   STATIC_VF="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,format=yuv420p";;
  contain) STATIC_VF="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p";;
esac
VF=""; DUR_SET=1; [ -n "$DUR" ] || DUR_SET=0

if [ "$MODE" = "auto" ]; then
  if [ "$H" -gt "$W" ]; then MODE="vpan"; else MODE="hpan"; fi
  # 几乎正好 16:9 的图没有余量，直接 static
  if [ $(( W * 9 )) -ge $(( H * 16 * 97 / 100 )) ] && [ $(( W * 9 )) -le $(( H * 16 * 103 / 100 )) ]; then
    MODE="static"
    echo "pan_still.sh: 图已接近 16:9，无运镜余量 → static"
  fi
fi

case "$MODE" in
  static)
    [ "$DUR_SET" = 1 ] || DUR=4
    VF="$STATIC_VF"
    ;;
  hpan)
    [ "$DUR_SET" = 1 ] || DUR=4
    case "$DIR" in left|right) ;; "") DIR="right";; *) echo "pan_still.sh: WARN --dir ${DIR} 与 hpan 不匹配，改用默认 right" >&2; DIR="right";; esac
    W1=$(awk "BEGIN{printf \"%d\", $W*1080/$H}")
    SCALE="scale=-2:1080"
    if [ "$W1" -lt 1920 ]; then
      SCALE="scale=2400:-2"; W1=2400
    fi
    MARGIN=$(( W1 - 1920 ))
    if [ "$MARGIN" -lt "$MARGIN_MIN" ]; then
      echo "pan_still.sh: 横摇余量只有 ${MARGIN}px（< 1920 的 10%）→ 退回 static"
      MODE="static"; [ "$DUR_SET" = 1 ] || DUR=4
      VF="$STATIC_VF"
    else
      TRAVEL="$(awk "BEGIN{m=$MARGIN; c=$DUR*30*$MAXSPD; printf \"%d\", (m<c?m:c)}")"
      if [ "$TRAVEL" -lt "$MARGIN" ]; then
        FULLDUR="$(awk "BEGIN{printf \"%.1f\", $MARGIN/(30*$MAXSPD)}")"
        echo "pan_still.sh: 余量 ${MARGIN}px 超过限速，只平移中间 ${TRAVEL}px（--max-speed ${MAXSPD}）；全程扫完需 --dur ${FULLDUR}"
      fi
      if [ "$DIR" = "left" ]; then X="(in_w-1920-$TRAVEL)/2+$TRAVEL*(1-t/$DUR)"
      else X="(in_w-1920-$TRAVEL)/2+$TRAVEL*t/$DUR"; fi
      VF="$SCALE,crop=1920:1080:'$X':'(in_h-1080)*$ANCHOR',setsar=1,fps=30,format=yuv420p"
    fi
    ;;
  vpan)
    [ "$DUR_SET" = 1 ] || DUR=8
    awk "BEGIN{exit !($HOLD < $DUR)}" 2>/dev/null || { echo "pan_still.sh: --hold ${HOLD}s 必须小于实际 DUR ${DUR}s" >&2; exit 2; }
    case "$DIR" in up) ;; "") DIR="up";; *) echo "pan_still.sh: WARN --dir ${DIR} 与 vpan 不匹配，改用默认 up" >&2; DIR="up";; esac
    H1=$(awk "BEGIN{printf \"%d\", $H*1920/$W}")
    VMARGIN=$(( H1 - 1080 ))
    if [ "$VMARGIN" -lt 108 ]; then
      echo "pan_still.sh: 竖摇余量只有 ${VMARGIN}px → 退回 static"
      MODE="static"; [ "$DUR_SET" = 1 ] || DUR=4
      VF="$STATIC_VF"
    else
      # y 从下往上；起点停 HOLD 秒；顶上留 5% 余量；限速时只从底部上移一段
      VTRAVEL="$(awk "BEGIN{m=$VMARGIN*0.95; c=($DUR-$HOLD)*30*$MAXSPD; printf \"%d\", (m<c?m:c)}")"
      if [ "$VTRAVEL" -lt $(( VMARGIN * 95 / 100 )) ]; then
        VFULLDUR="$(awk "BEGIN{printf \"%.1f\", $VMARGIN*0.95/(30*$MAXSPD)+$HOLD}")"
        echo "pan_still.sh: 余量 ${VMARGIN}px 超过限速，只从底部上移 ${VTRAVEL}px（--max-speed ${MAXSPD}）；全程扫完需 --dur ${VFULLDUR}"
      fi
      Y="(in_h-1080)-$VTRAVEL*min(1\,max(0\,(t-$HOLD)/($DUR-$HOLD)))"
      VF="scale=1920:-2,crop=1920:1080:0:'$Y',setsar=1,fps=30,format=yuv420p"
    fi
    ;;
esac

if [ -z "$OUT" ]; then
  base="$(basename "$IN")"; base="${base%.*}"
  OUT="$(dirname "$IN")/${base}_${MODE}.mp4"
fi
mkdir -p "$(dirname "$OUT")"

"$FFMPEG" -y -v error -framerate 30 -loop 1 -i "$SRC" -t "$DUR" -vf "$VF" \
  -c:v libx264 -preset fast -crf 18 -an "$OUT" \
  || { echo "pan_still.sh: 编码失败" >&2; rm -f "$OUT"; exit 1; }
[ -s "$OUT" ] || { echo "pan_still.sh: 输出为空" >&2; exit 1; }

FIRST="${OUT%.mp4}_first.jpg"; LAST="${OUT%.mp4}_last.jpg"
"$FFMPEG" -y -v error -i "$OUT" -frames:v 1 "$FIRST"
"$FFMPEG" -y -v error -sseof -0.2 -i "$OUT" -frames:v 1 "$LAST"

echo "pan_still.sh: mode=$MODE dur=${DUR}s dir=${DIR:-static} anchor-y=$ANCHOR"
echo "pan_still.sh: wrote $OUT"
echo "pan_still.sh: first-frame $FIRST"
echo "pan_still.sh: last-frame  $LAST"
