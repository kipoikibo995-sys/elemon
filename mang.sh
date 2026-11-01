#!/bin/sh
# Elemon online (Đấu trường: đấu với đội của người khác): một yêu cầu tới máy chủ, chạy ngầm. r36s/jsrt.c (__cv.net)
# ghi thân yêu cầu vào .mang/<id>.req rồi chạy  sh ./mang.sh <GET|POST> <đường dẫn> <id>  trên một luồng riêng;
# game đọc .mang/<id>.st (ghi sau cùng) để biết xong chưa, rồi .mang/<id>.res.
#   .st: "ok <mã HTTP>"   máy chủ đã trả lời (thân trả lời trong .res, kể cả khi mã >= 400)
#        "net"            không kết nối được (không wifi, máy chủ không trả lời)
#        "url"            chưa có địa chỉ máy chủ (mang-url.txt trống)
# Địa chỉ máy chủ: dòng đầu của mang-url.txt cạnh game (HUONG_DAN trong server/elemon-online), vd
#   https://elemon-online.<tên-bạn>.workers.dev
# Có curl thì dùng curl (với cacert.pem của game), không thì wget, như ota.sh.

cd "$(dirname "$0")" || exit 1
M=.mang
mkdir -p "$M"
METHOD="$1"; ID="$(printf %s "$3" | tr -cd 'a-z0-9')"
P="$(printf %s "$2" | tr -cd 'A-Za-z0-9/_.?=&-')"
[ -n "$ID" ] || exit 2
REQ="$M/$ID.req"; RES="$M/$ID.res"; ST="$M/$ID.st"
done_() { printf '%s\n' "$1" > "$ST.tmp" && mv "$ST.tmp" "$ST"; rm -f "$REQ"; }
rm -f "$RES" "$ST"

BASE="$(head -n 1 mang-url.txt 2>/dev/null | tr -cd 'A-Za-z0-9:/._-')"
BASE="${BASE%/}"
case "$BASE" in http://*|https://*) ;; *) done_ url; exit 0 ;; esac
URL="$BASE$P"
CA=""; [ -f cacert.pem ] && CA="--cacert cacert.pem"

if command -v curl >/dev/null 2>&1; then
    if [ "$METHOD" = POST ]; then
        code="$(curl -sS $CA --connect-timeout 8 -m 20 -o "$RES" -w '%{http_code}' -H 'Content-Type: application/json' --data-binary "@$REQ" "$URL")"
    else
        code="$(curl -sS $CA --connect-timeout 8 -m 20 -o "$RES" -w '%{http_code}' "$URL")"
    fi
    case "$code" in [1-5][0-9][0-9]) done_ "ok $code" ;; *) done_ net ;; esac
else                                               # a handheld without curl
    if [ "$METHOD" = POST ]; then
        wget -q -T 15 -O "$RES" --header='Content-Type: application/json' --post-file="$REQ" "$URL"
    else
        wget -q -T 15 -O "$RES" "$URL"
    fi
    r=$?
    # wget: 0 trả lời 2xx, 8 máy chủ trả lỗi (thân có thể mất), còn lại là mạng
    if [ $r -eq 0 ]; then done_ "ok 200"; elif [ $r -eq 8 ]; then done_ "ok 400"; else done_ net; fi
fi
