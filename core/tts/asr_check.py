"""Whisper line-by-line check: python core/tts/asr_check.py lines.json voices_dir [--lang en] [--model base.en]
Compares each line's text with its transcription (0.6 s of silence is padded on both sides first; short lines are misheard without it) and
writes per-word timestamps to voices_dir/words.json (for lip sync and line breaks).
A line in lines.json may carry an "asr" field that overrides the expected text (proper names, onomatopoeia, a word Whisper always hears as another).
--lang  English by default ('en'). Requires an exact word-by-word match after dropping punctuation
        and case (whole numbers 0–999 are turned into words on both sides, so "forty" and "40" match; larger numbers, years, ordinals like 3rd and
        numbers with punctuation (3.5, 1:30, 1,000, 40%) are not, so write the expected transcription in the "asr" field).
Model: --model (or the WHISPER_MODEL environment variable; default: base.en).
      If the default mishears a line that sounds right to you, check again with a larger model (base.en → small.en).
Exit codes: 0 all lines pass; 1 some lines differ; 2 the check could not run (model failed to load, etc.).
"""
import sys, json, re, os, argparse

_ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
_TENS = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()


def num_words(n):
    """0–999 → list of words for the English reading: 40 → ['forty'], 105 → ['one', 'hundred', 'five']"""
    out = []
    if n >= 100: out += [_ONES[n // 100], 'hundred']; n %= 100
    if n >= 20: out.append(_TENS[n // 10]); n %= 10
    if n or not out: out.append(_ONES[n])   # whole hundreds (100, 200…) don't get a trailing zero; 0 itself is read as zero
    return out


_SENTENCE_PUNCT = '.,;:!?"()[]{}\u2026\u201c\u201d\u2018\u2019'   # punctuation at either end of a word


def _is_formatted_number(raw):
    """Numbers written with punctuation between digits: decimals 3.5, times 1:30, dates 12/25, thousands separators 1,000, and percentages such as 40%.
    With the punctuation removed they would look like a different number (3.5 → 35), so they can't be converted to a reading."""
    core = raw.strip(_SENTENCE_PUNCT)
    return bool(re.search(r'\d[.,:/]\d', core) or ('%' in core and re.search(r'\d', core)))


def norm_en(s):
    """Word list for English comparison: lowercase, punctuation removed; integers 0–999 replaced by their reading; the 'and' in 'hundred and' isn't counted."""
    out = []
    for raw in s.lower().replace("'", '').replace('-', ' ').split():
        w = re.sub(r"[^a-z0-9]", '', raw)
        if not w: continue
        if re.fullmatch(r'0|[1-9]\d{0,2}', w) and not _is_formatted_number(raw): out += num_words(int(w))
        elif w == 'and' and out and out[-1] == 'hundred': pass
        else: out.append(w)
    return out


def compare(want, got):
    """Returns (passed or not, why it failed)"""
    a, b = norm_en(want), norm_en(got)
    return a == b, ''


def load_model(name):
    try: from faster_whisper import WhisperModel
    except ImportError: sys.exit('asr_check.py: faster-whisper is missing: install the voice tier')
    try:
        return WhisperModel(name, device='cpu', compute_type='int8')
    except Exception as e:
        msg = f'{type(e).__name__}: {e}'
        print(f"asr_check.py: cannot load the whisper model '{name}'.\n  {msg[:300]}", file=sys.stderr)
        if not os.path.isdir(name):
            print("  The model is downloaded from huggingface.co on first use. If offline, download the model once and pass --model /path/to/model-dir", file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('lines'); ap.add_argument('voices_dir')
    ap.add_argument('--lang', default='en'); ap.add_argument('--model'); ap.add_argument('--threshold', type=float, default=0.92)
    a = ap.parse_args()
    lines = json.load(open(a.lines, encoding='utf-8'))
    want = {L['id']: L.get('asr', L['text']) for L in lines}
    lang = 'en'
    name = a.model or os.environ.get('WHISPER_MODEL') or 'base.en'
    import numpy as np, soundfile as sf, soxr
    m = load_model(name)
    bad, words = 0, {}
    for L in lines:
        y, sr = sf.read(os.path.join(a.voices_dir, f"{L['id']}.wav"))
        if y.ndim > 1: y = y.mean(1)
        y = soxr.resample(y, sr, 16000, quality='HQ'); pad = np.zeros(int(.6 * 16000))
        segs, _ = m.transcribe(np.concatenate([pad, y, pad]).astype(np.float32), beam_size=5, language=lang, word_timestamps=True)
        tail = (len(y) + len(pad)) / 16000 - .5
        segs = [s for s in segs if not (s.no_speech_prob > .5 and s.start > tail)]; got = ' '.join(s.text.strip() for s in segs)
        words[L['id']] = [(w.word.strip(), round(w.start - .6, 3), round(w.end - .6, 3)) for s in segs for w in s.words]
        ok, why = compare(want[L['id']], got); bad += not ok
        print(('OK  ' if ok else 'DIFF'), L['id'], '|', want[L['id']], '→', got, f'   ({why})' if why else '')
    json.dump(words, open(os.path.join(a.voices_dir, 'words.json'), 'w', encoding='utf-8'), indent=0, ensure_ascii=False)
    print('mismatches:', bad, f'(lang={lang}, model={name})')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
