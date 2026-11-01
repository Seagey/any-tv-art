#!/bin/bash
# Promises check: every command, file and link the docs promise must exist. Run before publishing.
#
#   scripts/check-promises.sh
#
# Checks every Markdown file in the repo for:
#   1. `anytvart <command>`: the command is one of cli.py's subcommands
#   2. relative links [..](path): the file exists (placeholder images listed in ALLOW are skipped)
#   3. the word "Releases": a GitHub release must exist before the docs may promise a download
# Exit code 0 means every promise is kept.

set -u
cd "$(dirname "$0")/.." || exit 2
FOUND=0
note() { echo "  $*"; FOUND=$((FOUND + 1)); }
ALLOW="docs/images/preview.png"

CMDS=$(grep -oE 'add_parser\("[a-z-]+"' anytvart/cli.py | sed -E 's/add_parser\("//; s/"//' | sort -u)
echo "== commands"
for md in $(git ls-files '*.md'); do
  for c in $(grep -oE '`anytvart [a-z-]+' "$md" | sed 's/`anytvart //' | sort -u); do
    echo "$CMDS" | grep -qx "$c" || note "$md: anytvart $c is not a command"
  done
done

echo "== links"
for md in $(git ls-files '*.md'); do
  dir=$(dirname "$md")
  for link in $(grep -oE '\]\([^)#: ]+' "$md" | sed 's/^](//'); do
    case "$link" in http*|mailto*) continue ;; esac
    target="$dir/$link"
    [ -e "$target" ] && continue
    echo " $ALLOW " | grep -q " ${target#./} " && continue
    note "$md: link $link does not exist"
  done
done

echo "== releases"
if git ls-files '*.md' | xargs grep -l "Releases" > /dev/null 2>&1; then
  REMOTE=$(git remote get-url origin 2> /dev/null | sed -E 's#.*github.com[:/]##; s#\.git$##')
  if [ -z "$REMOTE" ] || ! gh release view --repo "$REMOTE" > /dev/null 2>&1; then
    note "the docs mention Releases but there is no GitHub release yet"
  fi
fi

echo
echo "findings: $FOUND"
[ "$FOUND" = 0 ]
