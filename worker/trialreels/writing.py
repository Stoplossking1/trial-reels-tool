"""Hooks (R4) and post captions (R7). The model writes; code decides what is allowed.

Two writers share the same checks:
  * Claude (default when ANTHROPIC credentials are available)
  * an offline writer that only cuts sentences out of the transcript (tests, no-key runs)
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from pydantic import BaseModel, Field

from . import config as C
from .transcript import Transcript

PATTERNS = {
    "number_first": "Opens with a number said in the video (\"3 apps I cancelled\").",
    "problem_first": "Opens with the threat, mistake or problem (\"You're losing clients by doing this\").",
    "how_to": "A short \"how to\" (\"How to clone any app in a day\").",
    "named_thing": "Names a specific person, company or thing from the video (\"A Turkish studio did this\").",
    "question": "A direct question to the viewer (\"Still paying for Canva?\").",
}

NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
NUMBER_WORDS.update({"thirty": "30", "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
                     "eighty": "80", "ninety": "90", "hundred": "100", "thousand": "1000",
                     "million": "1000000", "billion": "1000000000", "half": "half", "double": "double"})
SMALL_WORDS = {"i", "i'm", "i've", "i'd", "i'll", "a", "an", "the", "and", "or", "to", "of", "in", "on", "is",
               "it", "my", "you", "your", "this", "that", "how", "why", "what", "when", "who", "stop", "don't"}
STARTERS = SMALL_WORDS | set("""
how why what when where who which stop never always don't dont you're your you'll here this these those
i'm i've my most everyone nobody everybody every all no yes if just only one before after the a an
start quit try do does did can can't cannot should shouldn't would is are was were it's there's
""".split())
DASHES = "—–"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower().replace("’", "'")
    return re.sub(r"[^\w%$'\s.]", " ", s)


def _tokens(s: str) -> list[str]:
    return [t.strip(".'") for t in _norm(s).split() if t.strip(".'")]


def _numbers(s: str) -> set[str]:
    out = set()
    for t in _tokens(s):
        t = t.replace(",", "").rstrip("%").lstrip("$")
        if re.fullmatch(r"\d+(\.\d+)?k?", t):
            out.add(t)
        elif t in NUMBER_WORDS:
            out.add(NUMBER_WORDS[t])
    return out


def key(s: str) -> str:
    return " ".join(_tokens(s))


# ---------------------------------------------------------------- checks


@dataclass
class Hook:
    text: str
    pattern: str
    source_quote: str = ""


def hook_problems(h: Hook, t: Transcript, own: bool = False) -> list[str]:
    """Empty list = allowed. Fit on screen is checked later with the real font (plan.py)."""
    p = []
    words = h.text.split()
    if not words:
        return ["empty"]
    if len(words) > C.HOOK_MAX_WORDS:
        p.append(f"{len(words)} words (max {C.HOOK_MAX_WORDS})")
    if "\n" in h.text:
        p.append("line breaks are added by layout, not by the writer")
    if own:
        return p  # the user's own words: no "from the video" check (design 1.5)
    if h.pattern not in PATTERNS:
        p.append(f"unknown pattern {h.pattern!r}")
    said = _numbers(t.text)
    for n in _numbers(h.text) - said:
        p.append(f"number {n} is not said in the video")
    vocab = set(_tokens(t.text))
    for k, w in enumerate(words):
        bare = w.strip(".,!?:;\"'()")
        low = bare.lower()
        said = low in vocab or (low.endswith("'s") and low[:-2] in vocab)
        # Every capitalised word is a possible name. The first word is capitalised anyway, so it must be
        # said in the video or be a common opener ("How", "Stop", "Your", ...).
        if bare[:1].isupper() and not said and low not in SMALL_WORDS and not (k == 0 and low in STARTERS):
            p.append(f"name {bare!r} is not said in the video")
    if h.source_quote and key(h.source_quote) not in key(t.text):
        p.append("source quote is not in the transcript")
    return p


def caption_problems(c: str, t: Transcript) -> list[str]:
    p = []
    if "\n" in c:
        p.append("more than one line")
    if c != c.lower():
        p.append("not lower case")
    if "#" in c:
        p.append("has a hashtag")
    if len(EMOJI.findall(c)) > 1:
        p.append("more than one emoji")
    if any(d in c for d in DASHES):
        p.append("has a long dash")
    if not 10 <= len(c) <= 150:
        p.append("length must be 10-150 characters")
    for n in _numbers(c) - _numbers(t.text):
        p.append(f"number {n} is not said in the video")
    return p


def pick_hooks(cands: list[Hook], n: int, t: Transcript, own_hook: str | None = None) -> tuple[list[Hook], list[str]]:
    """Keep allowed, distinct hooks; spread patterns before repeating one. Returns (hooks, rejection notes)."""
    notes, kept, seen = [], [], set()
    if own_hook:
        h = Hook(own_hook.strip(), "own")
        probs = hook_problems(h, t, own=True)
        if probs:
            notes.append(f"your hook: {'; '.join(probs)}")
        else:
            kept.append(h)
            seen.add(key(h.text))
    good = []
    for h in cands:
        h = Hook(h.text.strip().rstrip(".").strip(), h.pattern, h.source_quote)  # no full stop on screen
        probs = hook_problems(h, t)
        if probs:
            notes.append(f"{h.text!r}: {'; '.join(probs)}")
        elif key(h.text) not in seen:
            seen.add(key(h.text))
            good.append(h)
    used = {h.pattern for h in kept}
    for h in good:  # first pass: one per pattern
        if len(kept) < n and h.pattern not in used:
            kept.append(h)
            used.add(h.pattern)
    for h in good:
        if len(kept) < n and h not in kept:
            kept.append(h)
    return kept, notes


def pick_captions(cands: list[str], n: int, t: Transcript) -> list[str]:
    out, seen = [], set()
    for c in cands:
        c = " ".join(c.split())
        if not caption_problems(c, t) and key(c) not in seen:
            seen.add(key(c))
            out.append(c)
    return out[:n]


# ---------------------------------------------------------------- offline writer


PROBLEM_WORDS = {"stop", "never", "mistake", "wrong", "problem", "don't", "dont", "losing", "lose", "worst",
                 "killing", "waste", "wasting", "fail", "broke", "scam", "nobody", "why"}


def offline_hooks(t: Transcript) -> list[Hook]:
    out = []
    for i in range(len(t.sentences)):
        ws = t.sentence_text(i).split()
        if len(ws) < 3:
            continue
        text = " ".join(ws[: C.HOOK_MAX_WORDS]).rstrip(",;:")
        if len(ws) > C.HOOK_MAX_WORDS:
            text = text.rstrip(".!")
        toks = set(_tokens(text))
        if text.endswith("?"):
            pat = "question"
        elif _numbers(text):
            pat = "number_first"
        elif toks & {"how"}:
            pat = "how_to"
        elif toks & PROBLEM_WORDS:
            pat = "problem_first"
        elif any(w[:1].isupper() and w.lower() not in SMALL_WORDS for w in text.split()[1:]):
            pat = "named_thing"
        else:
            continue
        out.append(Hook(text[0].upper() + text[1:], pat, text))
    if not out:  # nothing matched a pattern: fall back to opening lines as "problem first"
        out = [Hook(" ".join(t.sentence_text(i).split()[: C.HOOK_MAX_WORDS]), "problem_first")
               for i in range(min(5, len(t.sentences)))]
    return out


def offline_captions(t: Transcript, n: int) -> list[str]:
    out = []
    for i in range(len(t.sentences)):
        c = re.sub(f"[#{DASHES}]", " ", t.sentence_text(i).lower())
        c = " ".join(c.split())[:150].rstrip(" ,")
        if len(c) >= 10:
            out.append(c)
    return out


# ---------------------------------------------------------------- Claude writer


class HookOut(BaseModel):
    text: str = Field(description="On-screen hook, sentence case, under 10 words, no line breaks")
    pattern: str = Field(description="One of: " + ", ".join(PATTERNS))
    source_quote: str = Field(description="Exact words from the transcript this hook is based on")


class HooksOut(BaseModel):
    hooks: list[HookOut]


class CaptionsOut(BaseModel):
    captions: list[str]


def _hook_bank() -> str:
    if C.HOOK_BANK.exists():
        return C.HOOK_BANK.read_text()[:20000]
    return "\n".join(f"- {k}: {v}" for k, v in PATTERNS.items())


class Usage:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, u) -> None:
        self.input_tokens += getattr(u, "input_tokens", 0) or 0
        self.output_tokens += getattr(u, "output_tokens", 0) or 0

    @property
    def usd(self) -> float:  # claude-opus-5-5 list price, $4 / $20 per million tokens
        return round(self.input_tokens * 4e-6 + self.output_tokens * 20e-6, 5)


def _client():
    import anthropic
    return anthropic.Anthropic()


def _ask(prompt: str, schema, usage: Usage):
    resp = _client().messages.parse(
        model=C.CLAUDE_MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    )
    usage.add(resp.usage)
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError(f"Claude returned no usable output (stop_reason={resp.stop_reason})")
    return resp.parsed_output


def claude_hooks(t: Transcript, n_wanted: int, usage: Usage, avoid: list[str] = ()) -> list[Hook]:
    prompt = f"""You write on-screen hooks for Instagram trial reels. Each hook is the text shown in the first
2-3 seconds of the same talking-head video; we test them against each other.

Transcript (the ONLY source of facts):
<transcript>
{t.text}
</transcript>

Hook patterns (each hook must follow exactly one, named by its key):
<patterns>
{_hook_bank()}
</patterns>
Allowed pattern keys: {", ".join(PATTERNS)}.

Write {n_wanted} hooks:
- Every number, name and claim must come from the transcript. Do not invent or round numbers.
- Under 10 words. Sentence case. No hashtags, no emoji, no quotation marks.
- Each hook clearly different from the others; spread them across patterns.
- source_quote: the exact transcript words the hook is based on.
{"- Do not repeat these: " + "; ".join(avoid) if avoid else ""}"""
    out = _ask(prompt, HooksOut, usage)
    return [Hook(h.text.strip(), h.pattern.strip(), h.source_quote) for h in out.hooks]


def claude_captions(t: Transcript, hooks: list[str], usage: Usage) -> list[str]:
    prompt = f"""Write one Instagram caption for each of these {len(hooks)} trial reels of the same video.

Transcript (the ONLY source of facts):
<transcript>
{t.text}
</transcript>

Hooks, one per reel: {hooks}

Rules for every caption: one flat line, all lower case, no hashtags, at most one emoji, no long dashes,
10 to 150 characters, facts only from the transcript, and every caption different from the others.
Return exactly {len(hooks) + 2} captions (a couple of spares)."""
    return _ask(prompt, CaptionsOut, usage).captions


def have_claude() -> bool:
    import os
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
