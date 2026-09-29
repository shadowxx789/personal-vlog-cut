#!/usr/bin/env bash
# mute_segment.sh — 单切片静音：音频换静音并 apad 到视频时长（裁决 C4）
set -euo pipefail

usage() {
  cat <<'USAGE'
用法: mute_segment.sh INPUT.mp4 OUTPUT.mp4

把单个切片的现场声换成静音（BGM 在混音阶段才垫，这里不管）：
  - 音频换成 anullsrc 并 apad 到视频流时长（不是旧的 -shortest，那会每切短十几毫秒
    导致接上有声段后音画不同步）。
  - 输出后自动校验：音视频时长差 ≤ 1 帧（30fps ≈ 0.033s），超过即 FAIL 并退非零。
  - 出错返回非零，不静默出空文件。
USAGE
}

case "${1:-}" in -h|--help) usage; exit 0;; esac
[ $# -ge 2 ] || { echo "mute_segment.sh: 缺参数" >&2; usage >&2; exit 2; }
IN="$1"; OUT="$2"
[ -f "$IN" ] || { echo "mute_segment.sh: 输入不存在: $IN" >&2; exit 1; }

FFMPEG="$(command -v ffmpeg)"; FFPROBE="$(command -v ffprobe)"
VDUR="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$IN")"
[ -n "$VDUR" ] && [ "$VDUR" != "N/A" ] || VDUR="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$IN")"
awk "BEGIN{exit !($VDUR>0)}" || { echo "mute_segment.sh: 取不到视频时长" >&2; exit 1; }

"$FFMPEG" -y -v error -i "$IN" -f lavfi -i anullsrc=r=48000:cl=stereo \
  -map 0:v -map 1:a -c:v copy -c:a aac -ar 48000 -b:a 128k -af apad -t "$VDUR" "$OUT" \
  || { echo "mute_segment.sh: 编码失败" >&2; rm -f "$OUT"; exit 1; }
[ -s "$OUT" ] || { echo "mute_segment.sh: 输出为空" >&2; exit 1; }

ADUR="$("$FFPROBE" -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$OUT")"
VD2="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT")"
DIFF="$(awk "BEGIN{d=$ADUR-$VD2; if(d<0)d=-d; printf \"%.4f\", d}")"
echo "mute_segment.sh: video ${VD2}s / audio ${ADUR}s / diff ${DIFF}s"
awk "BEGIN{exit !($DIFF <= 0.0334)}" \
  && echo "mute_segment.sh: PASS（音画时长差 ≤ 1 帧）" \
  || { echo "mute_segment.sh: FAIL（音画时长差 ${DIFF}s > 1 帧）" >&2; exit 1; }
