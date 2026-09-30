#!/usr/bin/env bash
# mix_bgm.sh — 原声 + 垫乐 sidechain 混音，输出归档母版 vN_bgm.mp4
set -euo pipefail

usage() {
  cat <<'USAGE'
用法: mix_bgm.sh VIDEO BGM.wav [OUT.mp4]

把垫乐垫在原声下面（不换声轨）：
  原声 volume=1.18；BGM highpass=140 / lowpass=10000 / volume=0.72 /
  淡入 2.6s / 淡出 4.3s（FADE_START=片长−4.5 自动算）；
  sidechaincompress=threshold=0.04:ratio=4.5:attack=150:release=800:makeup=1:knee=8；
  amix normalize=0；末尾 alimiter=limit=0.89（防削波，给 AAC 峰值回弹留余量）。

规则:
  - 输入必须是没垫过 BGM 的 vN.mp4；文件名含 _bgm 直接报错。
  - BGM 比片长短时自动 acrossfade 接同一条（禁止 apad 补静音）。
  - 视频 -c:v copy，音频 aac 160k；默认输出 vN_bgm.mp4（归档母版）。
  - 出错返回非零，不静默出空文件。
USAGE
}

case "${1:-}" in -h|--help) usage; exit 0;; esac
[ $# -ge 2 ] || { echo "mix_bgm.sh: 缺参数" >&2; usage >&2; exit 2; }
VID="$1"; BGM="$2"; OUT="${3:-}"

[ -f "$VID" ] || { echo "mix_bgm.sh: 视频不存在: $VID" >&2; exit 1; }
[ -f "$BGM" ] || { echo "mix_bgm.sh: BGM 不存在: $BGM" >&2; exit 1; }
case "$(basename "$VID")" in
  *_bgm*) echo "mix_bgm.sh: 输入文件名含 _bgm（已经垫过 BGM），拒绝再垫一层。请从未垫过的 vN.mp4 混。" >&2; exit 1;;
esac

FFMPEG="$(command -v ffmpeg)"; FFPROBE="$(command -v ffprobe)"
WORK="$(mktemp -d /tmp/mix_bgm.XXXXXX)"; trap 'rm -rf "$WORK"' EXIT

D="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$VID")"
L="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$BGM")"
[ -n "$D" ] && [ -n "$L" ] || { echo "mix_bgm.sh: ffprobe 取不到时长" >&2; exit 1; }
awk "BEGIN{exit !($D>0 && $L>0)}" || { echo "mix_bgm.sh: 时长非法 D=$D L=$L" >&2; exit 1; }
ACOUNT="$("$FFPROBE" -v error -select_streams a -show_entries stream=index -of csv=p=0 "$VID" | wc -l | tr -d ' ')"
[ "$ACOUNT" -ge 1 ] || { echo "mix_bgm.sh: 视频没有音轨。先用 mute_segment.sh 补静音轨。" >&2; exit 1; }
awk "BEGIN{exit !($D >= 7)}" 2>/dev/null || { echo "mix_bgm.sh: 片长只有 ${D}s（< 7s；淡入 2.6s + 淡出 4.3s 会叠在一起），拒绝混音。" >&2; exit 1; }

LONG="$BGM"
if awk "BEGIN{exit !($L < $D)}"; then
  awk "BEGIN{exit !($L >= 8)}" || { echo "mix_bgm.sh: BGM 只有 ${L}s，acrossfade 需要 ≥8s" >&2; exit 1; }
  N="$(awk "BEGIN{printf \"%d\", int(($D+8)/$L)+1}")"
  ARGS=(); FILT=""
  for i in $(seq 0 $((N-1))); do ARGS+=(-i "$BGM"); done
  prev="[0:a]"
  for i in $(seq 1 $((N-1))); do
    out="[lx$i]"
    FILT="${FILT}${prev}[$i:a]acrossfade=d=8:c1=tri:c2=tri${out};"
    prev="$out"
  done
  FILT="${FILT}${prev}atrim=0:$D,asetpts=PTS-STARTPTS[lx]"
  "$FFMPEG" -y -v error "${ARGS[@]}" -filter_complex "$FILT" -map "[lx]" "$WORK/bgm_long.wav" \
    || { echo "mix_bgm.sh: BGM 接长失败" >&2; exit 1; }
  LONG="$WORK/bgm_long.wav"
  echo "mix_bgm.sh: BGM ${L}s < 片长 ${D}s，已 acrossfade 接成 $N 段并裁到片长"
fi

FADE_START="$(awk "BEGIN{printf \"%.3f\", $D-4.5}")"
if [ -z "$OUT" ]; then
  base="$(basename "$VID")"; base="${base%.*}"
  OUT="$(dirname "$VID")/${base}_bgm.mp4"
fi

"$FFMPEG" -y -v error -i "$VID" -i "$LONG" \
  -filter_complex "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume=1.18[orig];\
[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,highpass=f=140,lowpass=f=10000,volume=0.72,afade=t=in:st=0:d=2.6,afade=t=out:st=${FADE_START}:d=4.3[bgm];\
[orig]asplit[orig1][sc];\
[bgm][sc]sidechaincompress=threshold=0.04:ratio=4.5:attack=150:release=800:makeup=1:knee=8[ducked];\
[orig1][ducked]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.89[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -ar 48000 -b:a 160k "$OUT" \
  || { echo "mix_bgm.sh: 混音失败" >&2; rm -f "$OUT"; exit 1; }
[ -s "$OUT" ] || { echo "mix_bgm.sh: 输出为空" >&2; exit 1; }

AV="$("$FFPROBE" -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$OUT")"
VV="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$OUT")"
echo "mix_bgm.sh: wrote $OUT  (video ${VV}s / audio ${AV}s, fade-out@${FADE_START}s)"
