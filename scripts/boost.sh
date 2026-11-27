#!/usr/bin/env bash
# Usage: boost [count] [note...]
#   boost              -> 10 commits
#   boost 25           -> 25 commits
#   boost 5 fixed nav  -> 5 commits, first one logs "fixed nav" in today's devlog notes
set -euo pipefail
REPO="$HOME/devlog"
N="${1:-10}"; shift || true
NOTE="$*"
MAX_PER_DAY=10
[[ "$N" =~ ^[0-9]+$ ]] && (( N >= 1 )) || { echo "Count must be a positive number"; exit 1; }

cd "$REPO"
git pull --rebase -q
DAY=$(date +%F)
FILE="notes/$DAY.md"
mkdir -p notes

# Daily cap: count today's boost commits already made
DONE=$(git log --since="$DAY 00:00" --format=%s | grep -cE "^(check-in|note:) " || true)
LEFT=$(( MAX_PER_DAY - DONE ))
(( LEFT > 0 )) || { echo "Daily limit reached ($MAX_PER_DAY). Try again tomorrow."; exit 0; }
(( N > LEFT )) && { echo "Only $LEFT left today (limit $MAX_PER_DAY); making $LEFT."; N=$LEFT; }

for ((i = 1; i <= N; i++)); do
  if (( i == 1 )) && [[ -n "$NOTE" ]]; then
    echo "- $(date +%H:%M) $NOTE" >> "$FILE"
    msg="note: $NOTE"
  else
    echo "- $(date +%H:%M:%S) check-in #$i" >> "$FILE"
    msg="check-in $DAY #$i"
  fi
  git add "$FILE"
  git commit -q -m "$msg"
done

git push -q && echo "Pushed $N commit(s) to devlog."
