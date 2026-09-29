#!/usr/bin/env bash
# check_delivery.sh — 交付前体检：逐项 PASS/FAIL + 抽 6 帧接触表
set -euo pipefail

usage() {
  cat <<'USAGE'
用法: check_delivery.sh FILE [--discord] [--end-text-approved yes|no]

逐项体检（任一 FAIL 退出非零）：
  - 分辨率 1920×1080、SAR 1:1、DAR 16:9、pix_fmt yuv420p（拒绝 4:4:4）
  - profile 不是 High 4:4:4、有音轨、音视频时长差 ≤ 1 帧（30fps ≈ 0.033s）
  - 音频峰值不过 0 dBFS（volumedetect max_volume）
  - --discord：文件 ≤ 10MB 且文件名 ASCII
另：按片长均匀抽 6 帧拼接触表 jpg（打印路径）——必须看一眼，尤其 LUT 口播帧、
标题窗口、结尾字。--end-text-approved no 时提醒结尾叠字需人工确认。
USAGE
}

case "${1:-}" in -h|--help) usage; exit 0;; esac
[ $# -ge 1 ] || { echo "check_delivery.sh: 缺 FILE" >&2; usage >&2; exit 2; }
FILE="$1"; shift
DISCORD=0; END_APPROVED="yes"
while [ $# -gt 0 ]; do
  case "$1" in
    --discord) DISCORD=1; shift;;
    --end-text-approved) END_APPROVED="$2"; shift 2;;
    *) echo "check_delivery.sh: 未知参数 $1" >&2; exit 2;;
  esac
done
[ -f "$FILE" ] || { echo "check_delivery.sh: 文件不存在: $FILE" >&2; exit 1; }

FFMPEG="$(command -v ffmpeg)"; FFPROBE="$(command -v ffprobe)"
FAILS=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAILS=$((FAILS+1)); }

W="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=width -of csv=p=0 "$FILE")"
H="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$FILE")"
SAR="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=sample_aspect_ratio -of csv=p=0 "$FILE")"
DAR="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=display_aspect_ratio -of csv=p=0 "$FILE")"
PIX="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=pix_fmt -of csv=p=0 "$FILE")"
PROF="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=profile -of csv=p=0 "$FILE")"
VDUR="$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$FILE")"
ACOUNT="$("$FFPROBE" -v error -select_streams a -show_entries stream=index -of csv=p=0 "$FILE" | wc -l | tr -d ' ')"

[ "$W" = "1920" ] && [ "$H" = "1080" ] && pass "分辨率 1920×1080" || fail "分辨率 ${W}×${H}（要求 1920×1080）"
[ "$SAR" = "1:1" ] && pass "SAR 1:1" || fail "SAR=$SAR（要求 1:1）"
[ "$DAR" = "16:9" ] && pass "DAR 16:9" || fail "DAR=$DAR（要求 16:9）"
[ "$PIX" = "yuv420p" ] && pass "pix_fmt yuv420p" || fail "pix_fmt=$PIX（拒绝 4:4:4，要求 yuv420p）"
case "$PROF" in *4:4:4*) fail "profile=$PROF（High 4:4:4 手机播不了）";; *) pass "profile $PROF";; esac
[ "$ACOUNT" -ge 1 ] && pass "有音轨（${ACOUNT} 条）" || fail "没有音轨"

if [ "$ACOUNT" -ge 1 ]; then
  ADUR="$("$FFPROBE" -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$FILE")"
  DIFF="$(awk "BEGIN{d=$ADUR-$VDUR; if(d<0)d=-d; printf \"%.4f\", d}")"
  awk "BEGIN{exit !($DIFF<=0.0334)}" && pass "音画时长差 ${DIFF}s ≤ 1 帧" || fail "音画时长差 ${DIFF}s > 1 帧"
  MAXV="$("$FFMPEG" -i "$FILE" -af volumedetect -f null - 2>&1 | sed -n 's/.*max_volume: \([-0-9.]*\) dB.*/\1/p' | head -1)"
  [ -n "$MAXV" ] || MAXV="?"
  awk "BEGIN{exit !($MAXV<=0)}" && pass "峰值 ${MAXV} dB ≤ 0 dBFS" || fail "峰值 ${MAXV} dB 过 0 dBFS"
fi

if [ "$DISCORD" = 1 ]; then
  SIZE="$(wc -c < "$FILE" | tr -d ' ')"
  [ "$SIZE" -le $((10*1024*1024)) ] && pass "大小 $((SIZE/1024/1024))MB ≤ 10MB" || fail "大小 $((SIZE/1024/1024))MB > 10MB"
  base="$(basename "$FILE")"
  ascii_base="$(printf '%s' "$base" | LC_ALL=C tr -cd 'A-Za-z0-9._-')"
  [ "$ascii_base" = "$base" ] && pass "文件名 ASCII" || fail "文件名非 ASCII：$base"
fi

# 接触表：均匀抽 6 帧
SHEET="$(dirname "$FILE")/$(basename "$FILE")_sheet.jpg"
WORK="$(mktemp -d /tmp/check_delivery.XXXXXX)"; trap 'rm -rf "$WORK"' EXIT
for i in 0 1 2 3 4 5; do
  TS="$(awk "BEGIN{printf \"%.3f\", ($VDUR)*(($i)+0.5)/6}")"
  "$FFMPEG" -y -v error -ss "$TS" -i "$FILE" -frames:v 1 -vf "scale=480:-2" "$WORK/f_$i.jpg" || true
done
"$FFMPEG" -y -v error -framerate 1 -i "$WORK/f_%d.jpg" -filter_complex "tile=3x2" -frames:v 1 "$SHEET" 2>/dev/null \
  && echo "接触表：$SHEET —— 必须看一眼（LUT 口播帧、标题窗口、结尾字）" \
  || echo "接触表生成失败（不影响体检结果）"

if [ "$END_APPROVED" = "no" ]; then
  echo "提醒：结尾字未获确认（--end-text-approved no）。若接触表里结尾有叠字，必须先报给 用户 点头再烧。"
fi

if [ "$FAILS" -eq 0 ]; then
  echo "check_delivery.sh: 全部 PASS"
else
  echo "check_delivery.sh: $FAILS 项 FAIL" >&2
  exit 1
fi
