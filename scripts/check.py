#!/usr/bin/env python3
"""
Interactive Note — quality gate. Run after every build:
    python3 check.py note.tex            (the .pdf and .log must exist next to it)
Exit code 0 = PASS, 1 = FAIL. It:
  1. scans the .log for errors, missing glyphs, overfull boxes (layout overlap)
  2. checks the .tex for duplicate content (same question/formula twice)
  3. checks every QR timestamp exists in the transcript (if --tsv given) and is unique
  4. decodes the QR codes in the PDF (OpenCV) and verifies the URL format
  5. renders every page to PNG in <name>_pages/ — you MUST look at each PNG
"""
import re, sys, os, subprocess, argparse, glob, collections

ap = argparse.ArgumentParser()
ap.add_argument('tex'); ap.add_argument('--tsv', help='transcript.tsv to validate timestamps')
ap.add_argument('--dpi', type=int, default=110); ap.add_argument('--no-qr', action='store_true')
a = ap.parse_args()
base = os.path.splitext(a.tex)[0]
tex = open(a.tex, encoding='utf-8').read()
log = open(base + '.log', encoding='utf-8', errors='ignore').read() if os.path.exists(base + '.log') else ''
fails, warns = [], []

# ---------------------------------------------------------------- 1. log
if not os.path.exists(base + '.pdf'):
    fails.append('PDF not produced')
for m in re.finditer(r'^! (.*)$', log, re.M):
    fails.append('LaTeX error: ' + m.group(1))
miss = collections.Counter(re.findall(r'Missing character: There is no (\S+) \((U\+[0-9A-F]+)\)', log))
for (ch, cp), n in miss.items():
    fails.append(f'Missing glyph {ch} {cp} x{n} — replace it (use a TikZ/math symbol or another font)')
for m in re.finditer(r'Overfull \\hbox \(([\d.]+)pt too wide\)[^\n]*lines (\d+)--(\d+)', log):
    pt = float(m.group(1))
    (fails if pt > 4 else warns).append(f'Overfull hbox {pt}pt at tex lines {m.group(2)}-{m.group(3)}'
                                        + (' (text runs into margin/QR — fix)' if pt > 4 else ''))
for m in re.finditer(r'Overfull \\vbox \(([\d.]+)pt too high\)', log):
    if float(m.group(1)) > 2:
        fails.append(f'Overfull vbox {m.group(1)}pt (content taller than page/box)')
if re.search(r'Rerun to get|Label\(s\) may have changed', log):
    warns.append('Needs one more xelatex run')

# ---------------------------------------------------------------- 2. duplicates
body = tex.split('\\begin{document}', 1)[-1]
def norm(s): return re.sub(r'\s+', '', s)
items = re.findall(r'\\(?:problem|cq|bq)(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}', body)
dup = [k for k, v in collections.Counter(norm(i) for i in items if len(i) > 25).items() if v > 1]
for d in dup:
    fails.append('Duplicate question: ' + d[:70] + '…')
paras = [norm(p) for p in re.split(r'\n\s*\n', body) if len(p.strip()) > 120]
for k, v in collections.Counter(paras).items():
    if v > 1: fails.append('Duplicate paragraph: ' + k[:70] + '…')

# ---------------------------------------------------------------- 3. timestamps
qr_on = re.search(r'qr\s*=\s*true', tex) is not None
vid = re.search(r'video\s*=\s*\{?([A-Za-z0-9_-]{11})\}?', tex)
times = [int(x) for x in re.findall(r'\\(?:withqr|tqr)(?:\[[^\]]*\])?\{(\d+)\}', body)]
times += [int(x) for x in re.findall(r'\}\[(\d{1,5})\]', body)]   # \cq{..}[sec], \bq{..}{..}[sec], tipbox[sec]
if qr_on:
    if not vid: fails.append('qr=true but no valid 11-char video=ID in \\inotesetup')
    c = collections.Counter(times)
    for t, n in c.items():
        if n > 1: warns.append(f'Same QR time {t}s used {n}x — each concept/math should point to its own moment')
    if a.tsv and os.path.exists(a.tsv):
        ts = sorted(int(l.split('\t')[0]) for l in open(a.tsv, encoding='utf-8') if l.strip())
        last = ts[-1] if ts else 0
        for t in sorted(set(times)):
            near = min(ts, key=lambda x: abs(x - t)) if ts else None
            if t > last + 30: fails.append(f'QR time {t}s is after the video end ({last}s)')
            elif near is not None and abs(near - t) > 20:
                warns.append(f'QR time {t}s is {abs(near-t)}s away from any transcript line — check it')
    elif not a.tsv:
        warns.append('No --tsv given: timestamps not cross-checked against the transcript')

# ---------------------------------------------------------------- 4/5. render + QR decode
pages_dir = base + '_pages'
os.makedirs(pages_dir, exist_ok=True)
for f in glob.glob(pages_dir + '/*.png'): os.remove(f)
rendered = False
try:
    subprocess.run(['pdftoppm', '-r', str(a.dpi), '-png', base + '.pdf', pages_dir + '/page'],
                   check=True, capture_output=True); rendered = True
except Exception:
    try:
        import fitz
        doc = fitz.open(base + '.pdf')
        for i, p in enumerate(doc, 1):
            p.get_pixmap(dpi=a.dpi).save(f'{pages_dir}/page-{i:02d}.png')
        rendered = True
    except Exception as e:
        warns.append(f'Could not render pages ({e}) — open the PDF and inspect manually')
pages = sorted(glob.glob(pages_dir + '/*.png'))

if qr_on and vid and not a.no_qr:
    try:
        import cv2, tempfile
        tmp = tempfile.mkdtemp(); det = cv2.QRCodeDetector(); found = set()
        def scan(img):
            out = set()
            ok, vals, _, _ = det.detectAndDecodeMulti(img)
            if ok: out |= {v for v in vals if v}
            ok, pts = det.detectMulti(img)
            if ok:
                for q in pts:                       # re-decode every detected code on its own
                    x0, y0 = q.min(0).astype(int); x1, y1 = q.max(0).astype(int)
                    m = int((x1 - x0) * .25)
                    t, _, _ = det.detectAndDecode(img[max(0, y0-m):y1+m, max(0, x0-m):x1+m])
                    if t: out.add(t)
            return out
        for dpi in (200, 300, 400):                 # union over resolutions
            subprocess.run(['pdftoppm', '-r', str(dpi), '-png', base + '.pdf', f'{tmp}/q{dpi}'],
                           check=True, capture_output=True)
            for f in sorted(glob.glob(f'{tmp}/q{dpi}-*.png')):
                found |= scan(cv2.imread(f))
        found = sorted(found)
        pat = re.compile(r'^https://www\.youtube\.com/watch\?v=' + re.escape(vid.group(1))
                         + r'(&t=\d+s)?&noapp=1$')
        bad = [u for u in found if not pat.match(u)]
        for u in bad: fails.append('Bad QR URL: ' + u)
        print(f'QR decoded: {len(found)} (expected {len(times)}{' + 1 chapter QR' if "\\chapterbanner" in body else ''}); all URLs valid: {not bad}')
        if len(found) < len(set(times)):
            warns.append('Fewer QR codes decoded than expected — QR may be too small/overlapped')
    except Exception as e:
        warns.append(f'QR decode skipped ({type(e).__name__}) — install opencv-python-headless')

# ---------------------------------------------------------------- report
print(f'Pages: {len(pages)}  ->  {pages_dir}/')
for w in warns: print('  WARN ', w)
for f in fails: print('  FAIL ', f)
print('RESULT:', 'FAIL' if fails else 'PASS', '— now LOOK at every page PNG (overlap, orphan headings, diagram labels).')
sys.exit(1 if fails else 0)
