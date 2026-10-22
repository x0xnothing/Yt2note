#!/usr/bin/env python3
"""
Interactive Note — transcript helper.

  python3 transcript.py id     <youtube-url>              -> prints the 11-char video ID
  python3 transcript.py fetch  <youtube-url> [-o out.tsv] -> downloads transcript (bn, en, any)
  python3 transcript.py parse  <pasted.txt>  [-o out.tsv] -> normalises a pasted/exported transcript
  python3 transcript.py link   <youtube-url> <time>       -> QR target URL (time: 754 | 12:34 | 1:02:03)
  python3 transcript.py window <file.tsv> <from> <to>     -> print lines in a time window

Output TSV: one line per caption ->  <seconds>\t<mm:ss>\t<text>
Every QR in the note must be built from these seconds — never guess a time.
"""
import re, sys, json, argparse, html

YT_ID = re.compile(r'(?:v=|/shorts/|/live/|/embed/|youtu\.be/|/v/)([A-Za-z0-9_-]{11})')

def video_id(url: str) -> str:
    url = url.strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', url):
        return url
    m = YT_ID.search(url)
    if not m:
        sys.exit(f"ERROR: could not find a YouTube video ID in: {url}")
    return m.group(1)

def to_sec(t: str) -> int:
    t = t.strip().strip('[]()').replace(',', '.').split('.')[0]
    parts = [int(p) for p in t.split(':')]
    s = 0
    for p in parts:
        s = s * 60 + p
    return s

def mmss(s: int) -> str:
    h, r = divmod(int(s), 3600); m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

def qr_url(vid: str, sec: int) -> str:
    # noapp=1 -> opens in the browser, not the YouTube app
    return f"https://www.youtube.com/watch?v={vid}&t={int(sec)}s&noapp=1"

def write(rows, out):
    rows = [(int(s), re.sub(r'\s+', ' ', html.unescape(t)).strip()) for s, t in rows]
    rows = [r for r in rows if r[1]]
    rows.sort(key=lambda r: r[0])
    lines = [f"{s}\t{mmss(s)}\t{t}" for s, t in rows]
    data = "\n".join(lines) + "\n"
    if out:
        open(out, 'w', encoding='utf-8').write(data)
        print(f"wrote {len(rows)} lines -> {out}  (duration ~{mmss(rows[-1][0]) if rows else '0'})")
    else:
        sys.stdout.write(data)

# ------------------------------------------------------------------ fetch
def fetch(url, out):
    vid = video_id(url)
    langs = ['bn', 'en', 'en-US', 'hi']
    # 1) youtube-transcript-api (new >=1.0 API, then old API)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi as Y
        try:
            api = Y()
            try:
                fetched = api.fetch(vid, languages=langs)
            except Exception:
                tl = api.list(vid)
                fetched = next(iter(tl)).fetch()
            rows = [(s.start, s.text) for s in fetched]
        except TypeError:
            try:
                data = Y.get_transcript(vid, languages=langs)
            except Exception:
                tl = Y.list_transcripts(vid)
                data = next(iter(tl)).fetch()
            rows = [(d['start'], d['text']) for d in data]
        if rows:
            return write(rows, out)
    except Exception as e:
        print(f"[transcript-api] failed: {type(e).__name__}: {e}", file=sys.stderr)
    # 2) yt-dlp auto/manual subtitles
    try:
        import subprocess, tempfile, glob, os
        d = tempfile.mkdtemp()
        subprocess.run(['yt-dlp', '--skip-download', '--write-subs', '--write-auto-subs',
                        '--sub-langs', 'bn.*,en.*', '--sub-format', 'vtt',
                        '-o', f'{d}/%(id)s.%(ext)s', f'https://www.youtube.com/watch?v={vid}'],
                       check=True, capture_output=True, timeout=180)
        files = sorted(glob.glob(f'{d}/*.vtt'), key=lambda f: ('.bn' not in f, f))
        if files:
            return write(parse_text(open(files[0], encoding='utf-8').read()), out)
    except Exception as e:
        print(f"[yt-dlp] failed: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit("NO_TRANSCRIPT: ask the user to paste a timestamped transcript "
             "(e.g. youtubetotranscript.com with 'Timestamp ON') or upload a .txt/.srt file.")

# ------------------------------------------------------------------ parse
TS = r'(?:\d{1,2}:)?\d{1,2}:\d{2}(?:[.,]\d{1,3})?'
def parse_text(txt: str):
    rows, seen = [], set()
    lines = [l.rstrip() for l in txt.replace('\r', '').split('\n')]
    pending = None
    for line in lines:
        l = line.strip()
        if not l or l.upper() == 'WEBVTT' or l.isdigit() or l.startswith(('Kind:', 'Language:', 'NOTE')):
            continue
        m = re.match(rf'^({TS})\s*-->\s*({TS})', l)            # SRT / VTT cue line
        if m:
            pending = to_sec(m.group(1)); continue
        m = re.match(rf'^[\[(]?({TS})[\])]?\s*[-–:|]?\s*(.*)$', l)  # "12:34 text" / "[12:34] text"
        if m:
            sec = to_sec(m.group(1))
            if m.group(2):
                rows.append((sec, m.group(2))); pending = None
            else:
                pending = sec                                   # timestamp alone on its line
            continue
        l = re.sub(r'<[^>]+>', '', l)                           # vtt inline tags
        if pending is not None:
            rows.append((pending, l)); pending = None
        elif rows:
            rows[-1] = (rows[-1][0], rows[-1][1] + ' ' + l)     # continuation line
    out = []
    for s, t in rows:                                           # drop rolling-caption repeats
        key = (t.strip())
        if key in seen: continue
        seen.add(key); out.append((s, t))
    if not out:
        sys.exit("ERROR: no timestamps found. The transcript MUST have timestamps for QR codes.")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['id', 'fetch', 'parse', 'link', 'window'])
    ap.add_argument('arg'); ap.add_argument('extra', nargs='*')
    ap.add_argument('-o', '--out')
    a = ap.parse_args()
    if a.cmd == 'id':      print(video_id(a.arg))
    elif a.cmd == 'fetch': fetch(a.arg, a.out)
    elif a.cmd == 'parse': write(parse_text(open(a.arg, encoding='utf-8', errors='ignore').read()), a.out)
    elif a.cmd == 'link':  print(qr_url(video_id(a.arg), to_sec(a.extra[0])))
    elif a.cmd == 'window':
        lo, hi = to_sec(a.extra[0]), to_sec(a.extra[1])
        for line in open(a.arg, encoding='utf-8'):
            s = int(line.split('\t', 1)[0])
            if lo <= s <= hi: sys.stdout.write(line)

if __name__ == '__main__':
    main()
