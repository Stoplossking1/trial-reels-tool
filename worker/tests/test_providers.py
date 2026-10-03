"""Claude and Deepgram calls, with the network faked: the code around them must enforce the rules."""
import json
import types

import httpx

from trialreels import transcript as TR, writing


def test_claude_hooks_are_checked(transcript, monkeypatch):
    fake = writing.HooksOut(hooks=[
        writing.HookOut(text="3 apps I stopped paying for", pattern="number_first", source_quote="3 apps I stopped paying for"),
        writing.HookOut(text="7 apps I stopped paying for", pattern="number_first", source_quote="apps"),     # made-up 7
        writing.HookOut(text="Netflix charges me 40 dollars", pattern="named_thing", source_quote="40 dollars"),  # made-up name
        writing.HookOut(text="Why are you still paying for this?", pattern="question", source_quote="Why are you still paying for this?"),
    ])
    usage = writing.Usage()

    def fake_ask(prompt, schema, u):
        assert "<transcript>" in prompt and transcript.text in prompt
        u.input_tokens += 1000
        u.output_tokens += 200
        return fake

    monkeypatch.setattr(writing, "_ask", fake_ask)
    hooks, notes = writing.pick_hooks(writing.claude_hooks(transcript, 4, usage), 4, transcript)
    assert [h.text for h in hooks] == ["3 apps I stopped paying for", "Why are you still paying for this?"]
    assert any("number 7" in n for n in notes) and any("Netflix" in n for n in notes)
    assert usage.usd == round(1000 * 4e-6 + 200 * 20e-6, 5)


def test_deepgram_response_is_parsed(clip, tmp_path, monkeypatch):
    video, _ = clip
    body = {"metadata": {"duration": 17.0}, "results": {"channels": [{"alternatives": [{"words": [
        {"word": "three", "punctuated_word": "3", "start": 0.6, "end": 0.88},
        {"word": "apps", "punctuated_word": "apps.", "start": 0.95, "end": 1.23}]}]}]}}

    def fake_post(url, **kw):
        assert url == "https://api.deepgram.com/v1/listen" and kw["headers"]["Authorization"] == "Token k"
        return types.SimpleNamespace(status_code=200, json=lambda: body, text=json.dumps(body))

    monkeypatch.setattr(httpx, "post", fake_post)
    t = TR.transcribe_deepgram(video, tmp_path, "k")
    assert [w.text for w in t.words] == ["3", "apps."] and t.cost_usd > 0


def test_safe_bounds_cover_the_word(transcript):
    for w in transcript.words:
        assert w.safe_start <= w.start and w.safe_end >= w.end
