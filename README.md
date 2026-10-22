# yt2note — Interactive Note Skill

**YouTube লেকচার থেকে বইয়ের মতো প্রিন্ট-কোয়ালিটি নোট** — প্রতিটা কনসেপ্ট, ম্যাথ আর টিপসের পাশে QR কোড। স্ক্যান করলেই ব্রাউজারে ভিডিওটা ঠিক ওই মুহূর্ত থেকে চালু হবে।

`yt2note` is an AI-agent skill that turns a Bangla lecture (YouTube link + timestamped transcript, slides optional) into a **publication-quality XeLaTeX PDF**: a book-style note where every concept, worked math and tip carries a small QR code that opens the video **at that exact second** — no app, no embed, straight in the browser.

---

## ✨ Features

- 📖 **Book-quality output** — real typeset PDF (XeLaTeX), not a transcript dump: chapter structure, worked solutions, tip boxes, TikZ diagrams
- 🔗 **Per-concept QR codes** — every concept, math problem and tip links to its exact video timestamp (`?t=SECONDS`)
- 🧾 **5 output modes** — full note, QR note, BUET written-style paper, practice sheet, practice sheet with answers
- ✅ **Built-in QA gate** — `scripts/check.py` verifies the build log, text overlaps, duplicate labels and decodes every QR to confirm the URL + timestamp are valid
- 🔤 **Fonts bundled** — Tiro Bangla (body), Noto Serif Bengali, Hind Siliguri, Anek Bangla, Latin Modern Math
- 🎓 **Made for HSC / admission students** — Bangla-first, exam-style presentation

## 🎬 Demo — finished examples

Every style below is a finished sample built with this skill (PDF + its `.tex` source, in [`examples/`](examples/)):

| Demo | Style | Files |
|---|---|---|
| Vector chapter — full QR note | `/note-with-qr` | [note-with-qr.pdf](examples/note-with-qr.pdf) · [source](examples/note-with-qr.tex) |
| Gas chapter — full QR note | `/note-with-qr` | [gas-note-with-qr.pdf](examples/gas-note-with-qr.pdf) · [source](examples/gas-note-with-qr.tex) |
| BUET written-style paper | `/buet` | [buet.pdf](examples/buet.pdf) · [source](examples/buet.tex) |
| Practice sheet (questions only) | `/practice-sheet` | [practice-sheet.pdf](examples/practice-sheet.pdf) · [source](examples/practice-sheet.tex) |
| Practice sheet with answers | `/practice-sheet-ans` | [practice-sheet-ans.pdf](examples/practice-sheet-ans.pdf) · [source](examples/practice-sheet-ans.tex) |
| TikZ diagram recipes | reference | [diagram-recipes.pdf](examples/diagram-recipes.pdf) · [source](references/diagram-recipes.tex) |

## 📸 Example pages

| | |
|---|---|
| ![QR note — concepts, tips & worked math with timestamp QR codes](docs/demo-note-with-qr-p2.jpg) | ![QR note — chapter opening page](docs/demo-note-with-qr-p1.jpg) |
| **`/note-with-qr`** — concept boxes, teacher tips & worked math; প্রতিটার পাশে exact-timestamp QR | **`/note-with-qr`** — chapter opening page |
| ![BUET written-style paper](docs/demo-buet-p1.jpg) | ![Practice sheet](docs/demo-practice-sheet-p1.jpg) |
| **`/buet`** — bilingual questions, উত্তরের জন্য ফাঁকা জায়গা | **`/practice-sheet`** — math only, print & practice |

## ⌨️ Commands

| Command | What you get |
|---|---|
| `/note` | Full lecture note, no QR |
| `/note-with-qr` | Note with a QR beside every concept, math & tip |
| `/buet` | BUET written style: bilingual (বাংলা + English) questions, blank answer space |
| `/practice-sheet` | Math only — print & practice |
| `/practice-sheet-ans` | Math only, each question followed by its answer |
| `/commands` | List of all commands |

## 🚀 Install

- **Claude** — Settings → Capabilities → Skills → *Upload skill* → upload this repo as a ZIP.
- **Any file/code-capable AI agent** — give it this repo and say: *"Read `SKILL.md` and work exactly that way."*

## 📥 What to provide

1. **YouTube video link**
2. **Timestamped transcript** — paste the link at youtubetotranscript.com → **Timestamp ON** → Copy → save as a `.txt` file (not needed if your agent can fetch it itself)
3. **Slides PDF / Drive link** *(optional — makes a better note)*

Example: send `/note-with-qr` + the video link + `transcript.txt` + `slides.pdf`.

## 📁 Repository structure

```
yt2note/
├── SKILL.md                  ← the full skill instructions (agents: read this first)
├── assets/
│   ├── inote.sty             ← all styles & macros
│   ├── fonts/                ← Tiro Bangla · Noto Serif Bengali · Hind Siliguri · Anek Bangla · Latin Modern Math
│   └── templates/            ← note.tex · practice.tex · buet.tex
├── scripts/
│   ├── setup.sh              ← one-time setup + smoke test
│   ├── transcript.py         ← video ID, transcript fetch/parse, QR URLs
│   ├── build.sh              ← XeLaTeX ×2 + quality gate
│   └── check.py              ← log / overlap / QR verification
├── references/
│   └── diagram-recipes.tex   ← 10 tested TikZ diagrams
└── examples/                 ← finished sample PDFs + sources (the quality bar)
```

## 📄 Fonts & licenses

Fonts are bundled under their own licenses: **SIL Open Font License** (Tiro Bangla, Noto Serif Bengali, Hind Siliguri, Anek Bangla) and the **GUST Font License** (Latin Modern Math) — see [`assets/fonts/`](assets/fonts/).
