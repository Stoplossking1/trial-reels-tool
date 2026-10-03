"""Transcript with word times, safe cut points measured from the audio, and sentences (design 1.3)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path

import httpx
import numpy as np

from . import config as C
from . import media
from .errors import InputRejected, RunFailed

SENTENCE_END = re.compile(r"[.?!]['\"]?$")


@dataclass
class Word:
    text: str
    start: float
    end: float
    safe_start: float = 0.0
    safe_end: float = 0.0


@dataclass
class Transcript:
    words: list[Word]
    provider: str = ""
    cost_usd: float = 0.0
    sentences: list[tuple[int, int]] = field(default_factory=list)  # inclusive word index ranges

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    def sentence_text(self, i: int) -> str:
        a, b = self.sentences[i]
        return " ".join(w.text for w in self.words[a : b + 1])

    def to_json(self) -> dict:
        return {"provider": self.provider, "cost_usd": self.cost_usd,
                "words": [asdict(w) for w in self.words], "sentences": self.sentences}

    @classmethod
    def from_json(cls, d: dict) -> "Transcript":
        t = cls([Word(**w) for w in d["words"]], d.get("provider", "file"), d.get("cost_usd", 0.0))
        t.sentences = [tuple(s) for s in d.get("sentences") or []] or split_sentences(t.words)
        return t

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_json(), indent=1))

    @classmethod
    def load(cls, path: str | Path) -> "Transcript":
        return cls.from_json(json.loads(Path(path).read_text()))


def split_sentences(words: list[Word]) -> list[tuple[int, int]]:
    out, start = [], 0
    for i, w in enumerate(words):
        gap = words[i + 1].start - w.end if i + 1 < len(words) else 0
        if SENTENCE_END.search(w.text) or gap > 1.0 or i == len(words) - 1:
            out.append((start, i))
            start = i + 1
    return out


def refine_bounds(words: list[Word], audio_path: str | Path) -> None:
    """Push each word's edges outward to the nearest quiet stretch, so cuts never clip speech.

    Speech-to-text word times can be ~150 ms off; the audio energy is the truth.
    """
    db = media.frame_db(media.load_audio(audio_path))
    thr = media.quiet_threshold(db)
    quiet = db < thr
    run = max(1, int(round(C.QUIET_RUN_S / media.FRAME_S)))
    n = len(quiet)
    dur = n * media.FRAME_S

    def back(t: float, limit: float) -> float:
        i = min(n - 1, int(t / media.FRAME_S))
        lo = max(0, int(limit / media.FRAME_S))
        count = 0
        while i >= lo:
            count = count + 1 if quiet[i] else 0
            if count >= run:
                return (i + count) * media.FRAME_S  # end of the quiet run = where sound begins
            i -= 1
        return max(limit, t - 0.1)

    def fwd(t: float, limit: float) -> float:
        i = max(0, int(t / media.FRAME_S))
        hi = min(n, int(limit / media.FRAME_S))
        count = 0
        while i < hi:
            count = count + 1 if quiet[i] else 0
            if count >= run:
                return (i - count + 1) * media.FRAME_S  # start of the quiet run = where sound ends
            i += 1
        return min(limit, t + 0.1)

    for k, w in enumerate(words):
        prev_end = words[k - 1].end if k else 0.0
        nxt = words[k + 1].start if k + 1 < len(words) else dur
        w.safe_start = round(min(w.start, back(w.start, max(prev_end, w.start - 0.4))), 3)
        w.safe_end = round(max(w.end, fwd(w.end, min(nxt, w.end + 0.4))), 3)


def speech_seconds(words: list[Word]) -> float:
    return sum(max(0.0, w.end - w.start) for w in words)


# ---------------------------------------------------------------- providers

DEEPGRAM_USD_PER_MIN = 0.0043  # nova-3 pre-recorded list price; recorded per run in cost


def transcribe_deepgram(video: str | Path, workdir: Path, api_key: str) -> Transcript:
    wav = media.write_wav(video, workdir / "audio16k.wav")
    with open(wav, "rb") as fh:
        r = httpx.post(
            "https://api.deepgram.com/v1/listen",
            params={"model": "nova-3", "smart_format": "true", "punctuate": "true"},
            headers={"Authorization": f"Token {api_key}", "Content-Type": "audio/wav"},
            content=fh.read(),
            timeout=300,
        )
    if r.status_code != 200:
        raise RunFailed(f"transcription failed: {r.status_code} {r.text[:300]}")
    alt = r.json()["results"]["channels"][0]["alternatives"][0]
    words = [Word(w.get("punctuated_word") or w["word"], float(w["start"]), float(w["end"]))
             for w in alt.get("words", [])]
    dur_min = float(r.json().get("metadata", {}).get("duration", 0)) / 60
    return Transcript(words, "deepgram:nova-3", round(dur_min * DEEPGRAM_USD_PER_MIN, 5))


def transcribe(video: str | Path, workdir: Path) -> Transcript:
    """Run the paid speech-to-text API, then measure safe cut points from the audio."""
    if media.is_silent(video):
        raise InputRejected("silent", "We can't hear anyone talking in this video. The tool needs a spoken video.")
    key = media.env("DEEPGRAM_API_KEY")
    if not key:
        raise RunFailed("DEEPGRAM_API_KEY is not set. Set it, or pass --transcript with a transcript JSON file.")
    t = transcribe_deepgram(video, workdir, key)
    return finish(t, video)


def finish(t: Transcript, video: str | Path) -> Transcript:
    if speech_seconds(t.words) < 2.0:
        raise InputRejected("silent", "We can't hear anyone talking in this video. The tool needs a spoken video.")
    if not all(w.safe_end for w in t.words):
        refine_bounds(t.words, video)
    t.sentences = t.sentences or split_sentences(t.words)
    return t


def apply_fixes(t: Transcript, fixed_text: list[str]) -> Transcript:
    """The user fixed misheard words on the transcript screen: text changes, times stay."""
    if len(fixed_text) != len(t.words):
        raise ValueError("fixed transcript must have the same number of words")
    for w, txt in zip(t.words, fixed_text):
        w.text = txt
    t.sentences = split_sentences(t.words)
    return t


def first_sentence_end(t: Transcript) -> float:
    a, b = t.sentences[0]
    return t.words[b].end


def words_between(t: Transcript, t0: float, t1: float) -> list[int]:
    return [i for i, w in enumerate(t.words) if w.end > t0 and w.start < t1]


def in_word(t: Transcript, s: float) -> bool:
    return any(w.safe_start <= s <= w.safe_end for w in t.words)


def as_array(t: Transcript) -> np.ndarray:
    return np.array([[w.start, w.end] for w in t.words])
