#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Interactive Note — one-time setup + workspace creation
#   bash scripts/setup.sh [WORKDIR]      (WORKDIR default: ./inote-work)
# Safe to run many times. Fonts are bundled in assets/fonts (no download).
# ---------------------------------------------------------------------------
set -u
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${1:-./inote-work}"
ok(){ printf "  [OK]  %s\n" "$*"; }; warn(){ printf "  [!!]  %s\n" "$*"; }
need(){ command -v "$1" >/dev/null 2>&1; }
SUDO=""; if [ "$(id -u)" != "0" ] && need sudo; then SUDO="sudo"; fi

echo "== 1. XeLaTeX"
if ! need xelatex; then
  if need apt-get; then
    $SUDO apt-get update -y >/dev/null && $SUDO apt-get install -y --no-install-recommends \
      texlive-xetex texlive-latex-extra texlive-pictures texlive-science \
      texlive-fonts-recommended lmodern poppler-utils >/dev/null && ok "TeX Live installed"
  elif need brew; then brew install --cask mactex-no-gui
  else warn "Install TeX Live (Linux/Mac) or MiKTeX (Windows) manually, then re-run."; fi
fi
need xelatex && ok "$(xelatex --version | head -1)" || { warn "xelatex still missing — STOP"; exit 1; }

echo "== 2. LaTeX packages"
MISSING=""
for p in fontspec unicode-math tcolorbox tikz pgfplots circuitikz qrcode multicol tabularray \
         enumitem fancyhdr eso-pic needspace ragged2e siunitx hyperref xparse etoolbox; do
  kpsewhich "$p.sty" >/dev/null || MISSING="$MISSING $p"
done
kpsewhich latinmodern-math.otf >/dev/null || MISSING="$MISSING lm-math"
if [ -n "$MISSING" ]; then
  warn "missing:$MISSING  -> trying tlmgr"
  need tlmgr && $SUDO tlmgr install $MISSING >/dev/null 2>&1
  [ -n "$(command -v apt-get)" ] && $SUDO apt-get install -y texlive-latex-extra texlive-pictures texlive-science >/dev/null 2>&1
fi
for p in $MISSING; do kpsewhich "$p.sty" >/dev/null || [ "$p" = lm-math ] || warn "still missing: $p"; done
ok "packages checked"

echo "== 3. Helper tools (optional but recommended)"
PIP="pip install -q"; $PIP --help >/dev/null 2>&1 || PIP="pip3 install -q"
py_has(){ python3 -c "import $1" >/dev/null 2>&1; }
pipi(){ $PIP "$@" >/dev/null 2>&1 || $PIP --break-system-packages "$@" >/dev/null 2>&1; }
py_has youtube_transcript_api || pipi youtube-transcript-api
py_has cv2 || pipi opencv-python-headless
py_has fitz || pipi pymupdf
need yt-dlp || pipi yt-dlp
need pdftoppm && ok "pdftoppm (page render)" || warn "pdftoppm missing (apt install poppler-utils) — check.py will try PyMuPDF"
py_has youtube_transcript_api && ok "youtube-transcript-api" || warn "youtube-transcript-api unavailable -> ask user for transcript"
py_has cv2 && ok "opencv (QR verification)" || warn "opencv unavailable -> QR decode test skipped"

echo "== 4. Workspace: $WORK"
mkdir -p "$WORK"
cp -f "$SKILL_DIR/assets/inote.sty" "$WORK/"
rm -rf "$WORK/fonts"; cp -r "$SKILL_DIR/assets/fonts" "$WORK/fonts"
mkdir -p "$WORK/input"
ok "copied inote.sty + fonts/  (put source files in $WORK/input)"

echo "== 5. Smoke test"
cat > "$WORK/_smoke.tex" <<'EOF'
\documentclass[11pt]{article}
\usepackage{inote}
\inotesetup{mode=note,qr=true,video=abcdefghijk,brand={Test},subject={Smoke}}
\begin{document}বাংলা লেখা ঠিক আছে — ক্ষ্ম স্ত্র ন্ত্র। $R=\sqrt{P^2+Q^2}$ \tqr{75}\end{document}
EOF
( cd "$WORK" && xelatex -interaction=nonstopmode -halt-on-error _smoke.tex >/dev/null 2>&1 )
if [ -f "$WORK/_smoke.pdf" ] && ! grep -q "Missing character" "$WORK/_smoke.log"; then
  ok "smoke test passed"; rm -f "$WORK"/_smoke.*
else warn "smoke test FAILED — read $WORK/_smoke.log"; exit 1; fi
echo "Setup complete."
