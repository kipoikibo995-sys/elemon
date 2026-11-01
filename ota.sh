#!/bin/sh
# Elemon's in-device update (OTA) for the TrimUI Brick. The game runs "check" and "get" in the background from
# Cài đặt -> Cập nhật and reads .ota/state; launch.sh runs "apply" before the game starts and "after" when it ends.
#
#   check  the newest version's list (ota.txt on the "ota" branch) against files.txt here -> .ota/get.txt, .ota/del.txt
#   get    each changed file from the release's tag on GitHub into .ota/moi/, its SHA-256 checked; then .ota/ready
#   apply  (launch.sh, game not running) the old files into .ota/cu/, the new ones in; .ota/trial until the game says
#          it started (.ota/ok, written by the game)
#   after  (launch.sh, game ended) a trial run that never said so: everything put back from .ota/cu/
#
# Lists are lines "<sha256> <size> <path>" (paths only [A-Za-z0-9._/-], checked by scripts/pack_brick.py), headed by "#version vX.Y" and "#ref <git tag>". The save (Saves/elemon)
# is never touched; buttons.txt is the player's and is never replaced. A broken download leaves the game as it was.

REPO="kipoikibo995-sys/elemon"
RAW="https://raw.githubusercontent.com/$REPO"
KEEP="buttons.txt"

cd "$(dirname "$0")" || exit 1
APP="$(pwd)"
OTA="$APP/.ota"
CA="$APP/cacert.pem"
mkdir -p "$OTA"
# the newest list is ota.txt at the head of the "ota" branch (scripts/push_ota.py); each file is read from the
# version's own tag, so a release made while a download runs changes nothing. .ota/branch picks another (tests)
BRANCH="$(cat "$OTA/branch" 2>/dev/null || echo ota)"
LIST_URL="$RAW/$BRANCH/ota.txt"

state() { printf '%s\n' "$@" > "$OTA/state.tmp" && mv "$OTA/state.tmp" "$OTA/state"; }
fetch() { curl -sSfL --cacert "$CA" --connect-timeout 15 --retry 2 -m "${3:-600}" -o "$2" "$1"; }
ver_of() { sed -n 's/^#version //p' "$1" | head -1; }

check() {
    state "status=checking"
    rm -f "$OTA/ota.txt" "$OTA/get.txt" "$OTA/del.txt" "$OTA/ready"
    if ! fetch "$LIST_URL" "$OTA/ota.txt.part" 120; then
        state "status=error" "msg=Không kết nối được máy chủ. Kiểm tra wifi rồi thử lại."; return 1
    fi
    mv "$OTA/ota.txt.part" "$OTA/ota.txt"
    new="$(ver_of "$OTA/ota.txt")"
    have="$(ver_of "$APP/files.txt")"
    if [ -z "$new" ] || [ -z "$(sed -n 's/^#ref //p' "$OTA/ota.txt")" ]; then
        state "status=error" "msg=Danh sách cập nhật bị hỏng, thử lại sau."; return 1
    fi
    # changed or new files (not the player's own), then files the new version no longer has
    awk -v keep=" $KEEP " 'FNR == NR { if ($1 !~ /^#/) old[$3] = $1; next }
        $1 !~ /^#/ && old[$3] != $1 && index(keep, " " $3 " ") == 0' "$APP/files.txt" "$OTA/ota.txt" > "$OTA/get.txt"
    awk -v keep=" $KEEP " 'FNR == NR { if ($1 !~ /^#/) now[$3] = 1; next }
        $1 !~ /^#/ && !($3 in now) && index(keep, " " $3 " ") == 0 { print $3 }' "$OTA/ota.txt" "$APP/files.txt" > "$OTA/del.txt"
    n=$(wc -l < "$OTA/get.txt"); bytes=$(awk '{ s += $2 } END { print s + 0 }' "$OTA/get.txt")
    if [ "$n" -eq 0 ] && [ ! -s "$OTA/del.txt" ]; then
        state "status=same" "version=$have"; return 0
    fi
    state "status=new" "version=$new" "have=$have" "files=$n" "bytes=$bytes"
}

get() {
    [ -f "$OTA/get.txt" ] || check || return 1
    ref="$(sed -n 's/^#ref //p' "$OTA/ota.txt")"
    total=$(wc -l < "$OTA/get.txt"); bytes=$(awk '{ s += $2 } END { print s + 0 }' "$OTA/get.txt")
    free=$(df -k "$APP" | awk 'NR == 2 { print $4 * 1024 }')
    if [ "$free" -lt $((bytes * 2 + 50000000)) ]; then
        state "status=error" "msg=Thẻ nhớ không đủ chỗ: cần $((bytes * 2 / 1048576 + 50)) MB trống."; return 1
    fi
    done=0; got=0
    while read -r sum size path; do
        dst="$OTA/moi/$path"
        if ! [ -f "$dst" ] || [ "$(sha256sum "$dst" | cut -d' ' -f1)" != "$sum" ]; then   # not already fetched
            state "status=dl" "done=$done" "total=$total" "got=$got" "bytes=$bytes" "file=$path"
            mkdir -p "$(dirname "$dst")"
            if ! fetch "$RAW/$ref/$path" "$dst.part" || [ "$(sha256sum "$dst.part" | cut -d' ' -f1)" != "$sum" ]; then
                rm -f "$dst.part"
                state "status=error" "msg=Tải hỏng ở $path. Bản đang chơi giữ nguyên; thử lại để tải tiếp."; return 1
            fi
            mv "$dst.part" "$dst"
        fi
        done=$((done + 1)); got=$((got + size))
    done < "$OTA/get.txt"
    cp "$OTA/ota.txt" "$OTA/ready"
    state "status=ready" "version=$(ver_of "$OTA/ota.txt")" "total=$total" "bytes=$bytes"
}

# moving each file is undone the same way, so an apply cut off by the power is finished (or undone) on the next start
apply() {
    [ -f "$OTA/ready" ] || return 0
    echo "ota: installing $(ver_of "$OTA/ready")"
    mkdir -p "$OTA/cu"
    : >> "$OTA/cu/new.txt"
    while read -r sum size path; do
        [ -e "$OTA/moi/$path" ] || continue
        mkdir -p "$(dirname "$APP/$path")" "$(dirname "$OTA/cu/$path")"
        if [ -e "$APP/$path" ]; then [ -e "$OTA/cu/$path" ] || mv "$APP/$path" "$OTA/cu/$path"
        else echo "$path" >> "$OTA/cu/new.txt"; fi
        mv "$OTA/moi/$path" "$APP/$path"
    done < "$OTA/get.txt"
    while read -r path; do
        [ -e "$APP/$path" ] || continue
        mkdir -p "$(dirname "$OTA/cu/$path")"; mv "$APP/$path" "$OTA/cu/$path"
    done < "$OTA/del.txt"
    chmod +x "$APP/elemon" "$APP/launch.sh" "$APP/ota.sh" 2>/dev/null
    [ -e "$OTA/cu/files.txt" ] || cp "$APP/files.txt" "$OTA/cu/files.txt"
    cp "$OTA/ready" "$APP/files.txt"
    cp "$OTA/get.txt" "$OTA/cu/get.txt"; cp "$OTA/del.txt" "$OTA/cu/del.txt"
    ver_of "$OTA/ready" > "$OTA/trial"
    rm -rf "$OTA/moi" "$OTA/ready" "$OTA/ok" "$OTA/get.txt" "$OTA/del.txt" "$OTA/ota.txt"
    state "status=installed" "version=$(cat "$OTA/trial")"
}

rollback() {
    echo "ota: the new version did not start, putting $(ver_of "$OTA/cu/files.txt") back"
    while read -r sum size path; do
        if [ -e "$OTA/cu/$path" ]; then mv -f "$OTA/cu/$path" "$APP/$path"; fi
    done < "$OTA/cu/get.txt"
    while read -r path; do rm -f "$APP/$path"; done < "$OTA/cu/new.txt"
    while read -r path; do [ -e "$OTA/cu/$path" ] && mv -f "$OTA/cu/$path" "$APP/$path"; done < "$OTA/cu/del.txt"
    mv -f "$OTA/cu/files.txt" "$APP/files.txt"
    chmod +x "$APP/elemon" "$APP/launch.sh" "$APP/ota.sh" 2>/dev/null
    rm -rf "$OTA/cu" "$OTA/trial" "$OTA/ok"
    : > "$OTA/rolled"                              # launch.sh opens the old version again
    state "status=error" "msg=Bản mới không chạy được nên đã quay về bản cũ."
}

after() {
    [ -f "$OTA/trial" ] || return 0
    if [ -f "$OTA/ok" ]; then                      # it started: the old files are no longer needed
        echo "ota: $(cat "$OTA/trial") started fine"
        rm -rf "$OTA/cu" "$OTA/trial" "$OTA/ok"
    else
        rollback
    fi
}

case "$1" in
    check) check ;;
    get) get ;;
    apply) apply ;;
    after) after ;;
    *) echo "usage: $0 check|get|apply|after"; exit 2 ;;
esac
