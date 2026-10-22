#!/usr/bin/env bash
# Build + check:   bash scripts/build.sh path/to/file.tex [path/to/transcript.tsv]
# Runs xelatex twice (needed for tikz overlays, footers, QR positions), then check.py.
set -u
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEX="$1"; TSV="${2:-}"
DIR="$(cd "$(dirname "$TEX")" && pwd)"; NAME="$(basename "$TEX" .tex)"
cd "$DIR"
[ -f inote.sty ] || cp "$SKILL_DIR/assets/inote.sty" .
[ -d fonts ]     || cp -r "$SKILL_DIR/assets/fonts" fonts
for i in 1 2; do
  xelatex -interaction=nonstopmode -halt-on-error "$NAME.tex" > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "xelatex FAILED (pass $i). First error:"
    grep -n -A4 "^!" "$NAME.log" | head -20
    exit 1
  fi
done
if grep -q "Rerun to get\|may have changed" "$NAME.log"; then
  xelatex -interaction=nonstopmode "$NAME.tex" > /dev/null 2>&1
fi
echo "Built: $DIR/$NAME.pdf"
if [ -n "$TSV" ]; then python3 "$SKILL_DIR/scripts/check.py" "$NAME.tex" --tsv "$TSV"
else python3 "$SKILL_DIR/scripts/check.py" "$NAME.tex"; fi
