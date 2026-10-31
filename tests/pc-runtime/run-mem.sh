# run-mem.sh <game dir> <script> <name> <save fixture dir> [extra probe js...]: RSS every 0.25 s with the probe's lines
set -e
S="$(cd "$(dirname "$0")" && pwd)"   # this folder: probes and scripts here; out-*, log-*, save-* written here too
D=$1; SCRIPT=$2; NAME=$3; FIX=$4; shift 4
G=$S/g-$NAME; rm -rf "$G" "$S/save-$NAME" "$S/out-$NAME"; mkdir -p "$G" "$S/save-$NAME" "$S/out-$NAME"
for e in "$D"/*; do n=$(basename "$e"); [ "$n" = js ] || ln -s "$e" "$G/$n"; done
cp -r "$D/js" "$G/js"; cp "$S/probe-mem.js" "$S/probe-tail.js" "$G/js/"
sed -i "1a js/probe-mem.js" "$G/js/load.txt"; echo js/probe-tail.js >> "$G/js/load.txt"
for f in $JSOVER; do cp "$f" "$G/js/"; done
for x in "$@"; do cp "$S/$x" "$G/js/"; echo "js/$x" >> "$G/js/load.txt"; done
[ -n "$FIX" ] && cp "$FIX"/*.json "$S/save-$NAME/"
cd /mnt/d/INDIEGAME/HoLua
HOLUA_TEST=1 HOLUA_SAVE_DIR=$S/save-$NAME ${BIN:-build/qjs-host/holua-game-test} "$G" "$S/out-$NAME" ${EVERY:-100000} "$S/$SCRIPT" > "$S/log-$NAME.txt" 2>&1 &
PID=$!
: > "$S/rss-$NAME.txt"
while kill -0 $PID 2>/dev/null; do
  r=$(awk '/VmRSS/{print $2}' /proc/$PID/status 2>/dev/null || true)
  t=$(awk '{printf "%.0f", $1*1000}' /proc/uptime)
  [ -n "$r" ] && echo "$t $r" >> "$S/rss-$NAME.txt"
  sleep 0.25
done
wait $PID || true
python3 $S/analyse.py "$S/log-$NAME.txt" "$S/rss-$NAME.txt"; tail -1 "$S/log-$NAME.txt"
