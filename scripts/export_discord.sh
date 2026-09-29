#!/usr/bin/env bash
# export_discord.sh — 压 Discord 发送版（1080p、约 9MB、ASCII 名），自动体检
set -euo pipefail

usage() {
  cat <<'USAGE'
用法: export_discord.sh INPUT.mp4 [OUTPUT.mp4]

Discord 发送版：
  - 保持 1920×1080，setsar=1 / setdar=16/9 / yuv420p，-movflags +faststart。
  - 按片长自动算视频码率，目标文件约 9MB（音频 80k，按 ~5% 容器开销估）。
  - libx264 two-pass 编码；输出 ≥ 上限时视频码率 ×0.9 重编（两遍重跑），最多重试 2 次。
  - 上限默认 10MB，可用环境变量 PVC_DISCORD_LIMIT_BYTES 覆盖（测试用）。
  - 算出的视频码率 < 350k 时警告「画质会明显下降」，但不降分辨率。
  - 文件名强制 ASCII（非 ASCII 自动转写并提示）。
  - 输出后自动调用 check_delivery.sh --discord。

注意：字幕先烧进高码率母版 vN_sub.mp4（见 ffmpeg-recipes.md），本脚本只出 Discord 版。
USAGE
}

case "${1:-}" in -h|--help) usage; exit 0;; esac
[ $# -ge 1 ] || { echo "export_discord.sh: 缺 INPUT" >&2; usage >&2; exit 2; }
IN="$1"; OUT="${2:-}"
[ -f "$IN" ] || { echo "export_discord.sh: 输入不存在: $IN" >&2; exit 1; }

FFMPEG="$(command -v ffmpeg)"; FFPROBE="$(command -v ffprobe)"
DIR="$(cd "$(dirname "$0")" && pwd)"

D="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$IN")"
awk "BEGIN{exit !($D>0)}" || { echo "export_discord.sh: 取不到片长" >&2; exit 1; }

if [ -z "$OUT" ]; then
  base="$(basename "$IN")"; base="${base%.*}"
  OUT="$(dirname "$IN")/${base}_dc.mp4"
fi
# 文件名强制 ASCII
outdir="$(dirname "$OUT")"; outbase="$(basename "$OUT")"
ascii_base="$(printf '%s' "$outbase" | LC_ALL=C tr -cd 'A-Za-z0-9._-')"
if [ -z "$ascii_base" ]; then ascii_base="export.mp4"; fi
if [ "$ascii_base" != "$outbase" ]; then
  echo "export_discord.sh: 文件名非 ASCII，已改用 $ascii_base"
  OUT="$outdir/$ascii_base"
fi

# 目标约 9MB：总码率 kbps = 9*1024*8*0.95/D；视频 = 总 − 80（音频）
LIMIT_BYTES="${PVC_DISCORD_LIMIT_BYTES:-$((10*1024*1024))}"
VBPS="$(awk "BEGIN{v=9*1024*8*0.95/$D-80; printf \"%d\", (v<50?50:v)}")"
PASSDIR="$(mktemp -d /tmp/export_discord.XXXXXX)"; trap 'rm -rf "$PASSDIR"' EXIT

attempt=0
while :; do
  attempt=$((attempt+1))
  MAXRATE="$(awk "BEGIN{printf \"%d\", $VBPS*125/100}")"
  BUFSIZE="$(awk "BEGIN{printf \"%d\", $VBPS*2}")"
  if [ "$VBPS" -lt 350 ]; then
    echo "export_discord.sh: 警告：片长 ${D}s 只能给 ${VBPS}k 视频码率（<350k），画质会明显下降；不降分辨率。" >&2
  fi

  "$FFMPEG" -y -v error -i "$IN" \
    -vf "scale=1920:1080,setsar=1,setdar=16/9,format=yuv420p" \
    -c:v libx264 -preset medium -b:v "${VBPS}k" -maxrate "${MAXRATE}k" -bufsize "${BUFSIZE}k" \
    -pass 1 -passlogfile "$PASSDIR/pl" -an -f null /dev/null \
    || { echo "export_discord.sh: pass 1 编码失败" >&2; rm -f "$OUT"; exit 1; }
  "$FFMPEG" -y -v error -i "$IN" \
    -vf "scale=1920:1080,setsar=1,setdar=16/9,format=yuv420p" \
    -c:v libx264 -preset medium -b:v "${VBPS}k" -maxrate "${MAXRATE}k" -bufsize "${BUFSIZE}k" \
    -pass 2 -passlogfile "$PASSDIR/pl" \
    -c:a aac -b:a 80k -ar 48000 -movflags +faststart "$OUT" \
    || { echo "export_discord.sh: pass 2 编码失败" >&2; rm -f "$OUT"; exit 1; }
  [ -s "$OUT" ] || { echo "export_discord.sh: 输出为空" >&2; exit 1; }

  SIZE="$(wc -c < "$OUT" | tr -d ' ')"
  echo "export_discord.sh: 尝试 ${attempt}：video ${VBPS}k，大小 $((SIZE/1024))KB（上限 $((LIMIT_BYTES/1024/1024))MB）"
  if [ "$SIZE" -lt "$LIMIT_BYTES" ]; then break; fi
  if [ "$attempt" -ge 3 ]; then
    echo "export_discord.sh: 尝试 3 次仍超过上限（每次的码率和大小见上），输出保留但不可用。" >&2
    exit 1
  fi
  VBPS="$(awk "BEGIN{printf \"%d\", int($VBPS*0.9)}")"
done

echo "export_discord.sh: wrote $OUT  (${D}s, video ${VBPS}k, $((SIZE/1024/1024))MB)"

"$DIR/check_delivery.sh" "$OUT" --discord
