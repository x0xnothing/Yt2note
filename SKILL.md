---
name: interactive-note
description: Turn a Bangla lecture (YouTube link, Google Drive link, slide PDF, timestamped transcript) into publication-quality XeLaTeX PDFs — book-style notes with per-concept and per-math YouTube-timestamp QR codes, practice sheets, and BUET written-style question papers. Use for /note, /note-with-qr, /buet, /practice-sheet, /practice-sheet-ans, /commands.
---

# Interactive Note (ইন্টারেক্টিভ নোট)

You turn a lecture into a **printable book-quality PDF** built with **XeLaTeX** and the bundled
`assets/inote.sty`. The student scans a QR beside any concept or math and the video opens
**in the browser** at that exact second.

Everything the output needs is already in this skill folder:

```
interactive-note/
├── SKILL.md                     ← you are here (read fully once)
├── assets/inote.sty             ← all styles/macros (do NOT redefine them in the .tex)
├── assets/fonts/                ← Tiro Bangla (body), Noto Serif Bengali Bold, Hind Siliguri,
│                                   Anek Bangla, Latin Modern Math  (all bundled, OFL/GUST)
├── assets/templates/            ← note.tex · practice.tex · buet.tex  (start from these)
├── scripts/setup.sh             ← one-time setup + workspace (run first)
├── scripts/transcript.py        ← video ID, fetch/parse transcript, QR URL, time windows
├── scripts/build.sh             ← xelatex ×2 + quality gate
├── scripts/check.py             ← log/overlap/duplicate/QR verification + page PNGs
├── references/diagram-recipes.tex  ← 10 TESTED TikZ diagrams (copy, don't invent from zero)
└── examples/                    ← finished sample PDFs + .tex of every mode (the quality bar)
                                   (vector: all 4 modes · gas-note-with-qr: a 2nd chapter)
```

---

## 1. Commands

| Command | Output | Look (match the example PDF) |
|---|---|---|
| `/note` | Full lecture note, **no QR** | `examples/note-with-qr.pdf` with `qr=false` |
| `/note-with-qr` | Full lecture note, QR beside **every concept, every math, every tip** + chapter QR | `examples/note-with-qr.pdf` |
| `/buet` | BUET written paper: numbered bilingual (বাংলা + [English]) questions, big blank answer space, watermark, page frame, black footer bar | `examples/buet.pdf` |
| `/practice-sheet` | **Math only**, questions only (print & practice) | `examples/practice-sheet.pdf` |
| `/practice-sheet-ans` | Math only, each question followed by `সমাধান :` final answer | `examples/practice-sheet-ans.pdf` |
| `/commands` | Reply in chat (no PDF) with the table in §1.1 | — |

No command given → `/note-with-qr` if a YouTube link + timestamped transcript exist, else `/note`.
Several commands in one message → build each as a separate PDF from the **same** analysis (§4).

### 1.1 `/commands` reply (send exactly this, in Bangla)
```
/commands — সব কমান্ড
/note               QR ছাড়া সাধারণ নোট
/note-with-qr       প্রতিটা কনসেপ্ট ও ম্যাথের পাশে QR কোডসহ নোট
/buet               বুয়েট রিটেন স্টাইল: প্রশ্ন + উত্তরের জায়গা
/practice-sheet     শুধু ম্যাথ, প্রিন্ট করে প্র্যাকটিস
/practice-sheet-ans প্রতিটা প্রশ্নের সাথে উত্তর
যা দিতে হবে: YouTube লিংক + টাইমস্ট্যাম্পসহ ট্রান্সক্রিপ্ট (+ স্লাইড PDF / ড্রাইভ লিংক থাকলে ভালো)
```

---

## 2. Setup (run once per session, before anything else)

```bash
bash <skill-dir>/scripts/setup.sh ./inote-work      # installs/checks XeLaTeX, copies sty+fonts, smoke test
```
- Must end with `smoke test passed`. If XeLaTeX cannot be installed (no shell/permission), tell the
  user plainly and give them the `.tex` + `assets/` folder to compile on Overleaf
  (Menu → Compiler → **XeLaTeX**, upload `inote.sty` and the `fonts/` folder).
- Work only inside `./inote-work/`. Put the user's files in `./inote-work/input/`.

---

## 3. Inputs — how to read each one

| Input | What to do |
|---|---|
| **YouTube link** | `python3 scripts/transcript.py id <url>` → 11-char ID (needed for every QR). Then try `python3 scripts/transcript.py fetch <url> -o input/transcript.tsv`. |
| **Transcript the user pasted / uploaded** (.txt/.srt/.vtt, youtubetotranscript.com copy with *Timestamp ON*) | Save raw text to `input/raw_transcript.txt`, then `python3 scripts/transcript.py parse input/raw_transcript.txt -o input/transcript.tsv`. |
| **No timestamps available** | `/note-with-qr` and per-item QR are impossible — **ask** for a timestamped transcript (show: youtubetotranscript.com → paste link → *Timestamp ON* → Copy). Never invent times. If the user refuses, build `/note` and say why there are no QRs. |
| **Slide / book PDF** | `pdftotext -layout file.pdf -` for text. **Also render pages** (`pdftoppm -r 110 -png`) and LOOK at them: Bangla PDFs made with Bijoy/SutonnyMJ extract as garbage Latin (e.g. `‡f±i`) — then read from the images only. Copy diagrams' *meaning*, redraw them in TikZ. |
| **Google Drive link** | Get the file ID from `/d/<ID>/` or `id=<ID>`; download `https://drive.google.com/uc?export=download&id=<ID>` (large files: use `gdown` if available). If blocked/private, ask the user to upload the file. |
| **Images of questions** | Read them visually; transcribe exactly (numbers, units, signs). |

`transcript.tsv` format: `seconds<TAB>mm:ss<TAB>text`. Use `python3 scripts/transcript.py window input/transcript.tsv 12:00 15:30`
to read any part of the lecture again.

---

## 4. Analysis — the transcript is the TEACHING SCRIPT

Do this **before writing any LaTeX**. Write the result to `inote-work/plan.md`.

1. **Read the whole transcript start→end** (in windows). The teacher's spoken words are the primary
   source: the order, the explanations, the analogies, the warnings ("এখানে সবাই ভুল করে…"),
   the shortcuts, the exam hints. The slides are the *skeleton*; the transcript is the *flesh*.
2. **Segment the lecture** into blocks, each with its **exact start second** (the line where the
   teacher *begins* that idea — not where the slide changes). Block kinds:
   `concept` · `formula` · `derivation` · `math` (worked example) · `tip` (said, not on slide) · `exam-info`.
3. **Group blocks into Types** (Type-01, Type-02 …) = one family of problems/ideas.
   Order: the order the teacher taught them.
4. For every Type record in `plan.md`:
   - concept explanation in simple Bangla, rewritten from the teacher's words (not copied filler)
   - formulas (each formula gets ONE home — see dedupe ledger)
   - every worked math: full statement, given data, the teacher's method/steps, final answer,
     start second; source tag only if stated (board+year, book, "ভিডিও ম্যাথ")
   - tips the teacher said that are **not on the slides** (these are gold — never drop them)
   - which diagram is needed (pick a recipe from `references/diagram-recipes.tex`)
5. **Dedupe ledger** (in plan.md): list every formula, definition, question and tip **once** with
   the place it will appear. Later sections *refer* to it ("সূত্র (২) ব্যবহার করে") instead of
   repeating. The checker fails duplicate questions/paragraphs.
6. **Verify all maths with Python** before typesetting: recompute every numeric answer
   (`python3 -c ...`), keep 2 decimals unless the teacher used another precision, check units.
   If the teacher made a slip, use the correct value and add a `tipbox` noting it politely.
7. Teacher's spoken filler, greetings, sponsor talk, "subscribe" → ignore.

---

## 5. Writing the .tex — per mode

Copy the matching file from `assets/templates/` into `inote-work/`, fill every `<<…>>`, delete unused blocks.
Look at the matching `examples/*.pdf` first — that is the quality bar.

### 5.1 `/note` and `/note-with-qr`  (book-style note)
Order of the document (do not reorder):
1. `\chapterbanner` (chapter no., Bangla title, English title; full-lecture QR in the chevron when `qr=true`).
2. `\sectionbar{Lecture Map …}` + table: one row per Type → name, `\stars{n}` importance (from how
   much time/emphasis the teacher gave), start time, what's inside, page.
   A **Board Questions Analysis** table is allowed **only** if the user's source has real board data — never invent boards/years.
3. `\fancyheading{গুরুত্বপূর্ণ সূত্রাবলি ও বিশ্লেষণ}` + `formulagrid`: every formula of the lecture,
   grouped, with a diagram or symbol meanings in the right column. `unitbox` for unit conversions /
   "দ্রুত মনে রাখো" facts.
4. `\begin{multicols}{2}` then **for each Type, concept first, then its maths**:
   `typebox` (concept with `\withqr{sec}{…}`, key formulas, `roundbox` takeaways, diagram) →
   `tipbox[sec]` for each spoken tip → every worked math as `\cq{n}[source]{stem}[sec]` +
   `\solhead` + `\workgiven{steps}{\given{data}}`; CQ parts with `\qpart{গ}{…}`, answers with `\anslabel{গ}`.
- Step style: one `=` step per line, left column ≤ ~30 characters of math per line, finish with `\Ans`.
- Every concept, math and tip gets its own timestamp → own QR (`qr=true`). Two items never share a QR time.
- `/note` = same document with `qr=false` (macros automatically drop the QR and give text full width).

### 5.2 `/practice-sheet` and `/practice-sheet-ans`
- **Only problems that need calculation/derivation** (no definitions, no MCQ theory).
- Sources: every math from the lecture + (if the user asks or the lecture is short) similar
  problems you write yourself — mark those `[অনুরূপ]`. Never label a self-made problem as a board question.
- `\sheettitle{অধ্যায়-২}{ভেক্টর}`, then `\topicbar{Topic-1: …}` per topic, then
  `\problem[source tag]{statement}{final answer}` — numbering is automatic (Problem-01 …).
- `answers=false` → `/practice-sheet` (answers hidden; `answerbox=true` adds dashed working space).
  `answers=true` → `/practice-sheet-ans` (`সমাধান :` + final answer only, no steps).
- Optional `[sec]` as 4th argument puts a QR next to the problem when `qr=true`.

### 5.3 `/buet`
- BUET-level, multi-concept, calculation-heavy questions; Bangla first, then the same question in
  English inside `[…]` (written by `\bq{বাংলা}{English}[sec]`).
- `\answerspace` after each question (fills space evenly); `\newpage` after 2 long or 3 short questions.
- Include a TikZ figure when the question depends on geometry/setup (river, incline, circuit, lens…).
- `watermark=` brand text (or empty); `test-title=` shows in the black footer bar.
- Do **not** print answers in `/buet` (the space is for the student). If the user wants answers,
  build a second file with `/practice-sheet-ans` style.

---

## 6. Macro reference (`inote.sty`) — use these, don't hand-roll boxes

| Macro / env | Use |
|---|---|
| `\inotesetup{mode=note\|practice\|buet, qr=true/false, answers=…, answerbox=…, video=ID, brand=…, subject=…, chapter=…, chapter-en=…, chapter-no=…, watermark=…, test-title=…, accent=HEX}` | preamble config (before `\begin{document}`) |
| `\tqr{sec}` / `\withqr{sec}{paragraph}` | QR to `https://www.youtube.com/watch?v=ID&t=SECs&noapp=1` (+ mm:ss label). `\withqr` shrinks the text so it **never overlaps** the QR |
| `\chapterbanner` `\sectionbar{}` `\fancyheading{}` `\subhead{}` | headings (note mode) |
| `formulagrid[left-ratio]` | 2-col সূত্রাবলি \| বিশ্লেষণ table; rows end with `\\`, cells split by `&` |
| `\sqitem{title}` `\dotitem` | ■ bold item / • bullet inside boxes and tables |
| `unitbox[title]` (+`\item`) | double-frame box with ◆ bullets |
| `typebox{01}{name}` | Type header + dashed concept box (breakable) |
| `roundbox` `conceptbox` | rounded takeaway box / dashed definition box |
| `tipbox[sec]` | red "ভিডিওতে বলা টিপস" box with QR |
| `\cq{১}[source]{stem}[sec]` `\qpart{গ}{}` `\solhead` `\anslabel{গ}` `\workgiven[0.62]{steps}{\given{data}}` `\Ans` | solved CQ/math |
| `\stars{4}` | 4 filled + 1 empty star (no ★ glyphs — fonts lack them) |
| `\sheettitle{}{}` `\topicbar{}` `\problem[tag]{q}{ans}[sec]` | practice sheet |
| `\bq{বাংলা}{English}[sec]` `\answerspace` `\answerspace[6cm]` | BUET paper |
| `\keeplines{n}` · `\columnbreak` · `\newpage` | keep the next n lines together (works inside 2 columns; never use `\Needspace` there) · force a column / page break when the visual check shows an orphan |
| TikZ styles: `vec, vecthin, force, dim, guide, ground, body, dot, lbl`, colour `accent` | diagrams |

---

## 7. Diagrams (must look like a printed textbook)

- Start from the nearest recipe in `references/diagram-recipes.tex` (vectors, incline, projectile,
  gas cylinder, circuit, lens, v–t graph, spring/pendulum, 3D box, coordinate geometry). Change
  numbers, keep the styles.
- Draw **to scale from the real numbers** (compute coordinates; angles with `\pic{angle=…}`).
- Every label sits in free space: use `above/below/left/right`, `pos=`, `label=…` — never on a line
  or arrow. Physics labels in math (`$\vec F$`), Bangla labels with `lbl` style.
- Width ≤ column width (`scale=` to fit). One accent colour for the answer/result vector, black for the rest.
- Diagram needed when: vectors/forces/motion geometry, circuits, optics, graphs, apparatus from the
  slide, coordinate geometry. Not needed for pure algebra.

---

## 8. Hard rules (zero tolerance)

1. **No overlap**: no text on QR, diagram labels never on lines, no text in margins, no heading alone
   at a column/page bottom, footer never covered. `check.py` FAILs on overfull > 4pt and missing glyphs.
2. **No duplication**: each formula/definition/question/tip appears once (dedupe ledger). Same QR
   time never used twice.
3. **No fabrication**: no invented board names/years, timestamps, teacher quotes, or answers. Every
   QR second must come from `transcript.tsv`; `check.py --tsv` cross-checks.
4. **QR format** is always `https://www.youtube.com/watch?v=<ID>&t=<SECONDS>s&noapp=1`
   (opens in the browser). Only via `\tqr`/`\withqr`/`[sec]` args — never hand-typed.
5. **Typography**: body Tiro Bangla 11pt, justified; Bangla digits in Bangla prose/labels (১২, ২০২৪),
   Latin digits inside math; units upright with thin space `$5\,\text{m\,s}^{-1}$`; `×` as `\times`;
   no emoji / ★ / ▸ characters (use `\stars`, `\inotetri`). Bangla words inside math → `\text{…}`.
6. **Correct science**: every number recomputed in Python; signs, units, significant figures checked.
7. Never edit `inote.sty` for one document; if something is truly missing, add a small macro in the
   .tex preamble using the same colours/fonts.

---

## 9. Build → check → look → fix (loop until clean)

```bash
cd inote-work
bash <skill-dir>/scripts/build.sh note.tex input/transcript.tsv
```
- `build.sh` runs XeLaTeX twice and then `check.py`, which prints `RESULT: PASS/FAIL`, decodes every
  QR (must say `all URLs valid: True` and decoded = expected), and renders pages to `note_pages/*.png`.
- **Open and look at EVERY page PNG** at full size. Check: overlaps, orphan headings/`সমাধান:` at
  column bottom, broken conjuncts (যুক্তাক্ষর), diagram labels, empty half-pages, alignment of `=` steps,
  table borders. Fix in the .tex (`\columnbreak`, move a diagram, shorten a line, `\newpage`) and rebuild.
- Done only when: `RESULT: PASS`, QR count matches, and your visual pass finds nothing.

---

## 10. Deliver

- Send the **PDF(s)** (file name: `<chapter>-<mode>.pdf`, e.g. `vector-note-with-qr.pdf`) and the `.tex`
  source. One or two lines: what's inside (how many Types / maths / QR codes) and anything
  missing (e.g. "ভিডিও ৪২:১০ এর পরের অংশে অডিও নেই, তাই সেখানের ম্যাথ বাদ").
- Don't paste the whole note in chat.
