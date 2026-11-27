#!/usr/bin/env bash
# Usage: boost [count] [note...]
#   boost              -> 10 commits
#   boost 25           -> 25 commits
#   boost 5 fixed nav  -> 5 commits, first one logs "fixed nav" in today's devlog notes
set -euo pipefail
REPO="$HOME/devlog"
N="${1:-10}"; shift || true
NOTE="$*"
[[ "$N" =~ ^[0-9]+$ ]] && (( N >= 1 && N <= 200 )) || { echo "Count must be 1-200"; exit 1; }

cd "$REPO"
git pull --rebase -q
DAY=$(date +%F)
FILE="notes/$DAY.md"
mkdir -p notes

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
