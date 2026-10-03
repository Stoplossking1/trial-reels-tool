"""R4 / R7: hooks and captions only use what is said, and follow the format rules."""
from trialreels.transcript import Transcript, Word
from trialreels.writing import Hook, caption_problems, hook_problems, offline_captions, offline_hooks, pick_hooks


def tr(text):
    t = Transcript([Word(w, i * 0.3, i * 0.3 + 0.25, i * 0.3, i * 0.3 + 0.25) for i, w in enumerate(text.split())])
    from trialreels.transcript import split_sentences
    t.sentences = split_sentences(t.words)
    return t


T = tr("I stopped paying for three apps this year. A Turkish studio cloned my app in a week. How do you stop that?")


def test_hook_number_must_be_said():
    assert hook_problems(Hook("3 apps I stopped paying for", "number_first"), T) == []
    assert any("number 5" in p for p in hook_problems(Hook("5 apps I stopped paying for", "number_first"), T))


def test_hook_name_must_be_said():
    assert hook_problems(Hook("A Turkish studio cloned my app", "named_thing"), T) == []
    assert any("Google" in p for p in hook_problems(Hook("Google cloned my app", "named_thing"), T)) or \
        any("Google" in p for p in hook_problems(Hook("Why Google cloned my app", "named_thing"), T))


def test_hook_length_and_pattern():
    assert any("words" in p for p in hook_problems(Hook("one two three four five six seven eight nine ten", "question"), T))
    assert any("pattern" in p for p in hook_problems(Hook("A Turkish studio", "clickbait"), T))


def test_own_hook_skips_fact_check_but_not_length():
    assert hook_problems(Hook("My 7 best tips", "own"), T, own=True) == []
    assert hook_problems(Hook("a b c d e f g h i j k", "own"), T, own=True)


def test_pick_hooks_unique_and_spread():
    cands = [Hook("A Turkish studio cloned my app", "named_thing"), Hook("a turkish studio cloned my app!", "named_thing"),
             Hook("How do you stop that?", "question"), Hook("3 apps I stopped paying for", "number_first")]
    hooks, _ = pick_hooks(cands, 3, T)
    assert len(hooks) == 3 and len({h.pattern for h in hooks}) == 3


def test_caption_rules():
    assert caption_problems("a turkish studio cloned my app in a week", T) == []
    assert caption_problems("A Turkish studio cloned my app", T)          # not lower case
    assert caption_problems("cloned in a week #apps", T)                 # hashtag
    assert caption_problems("cloned in a week — wild", T)            # long dash
    assert caption_problems("cloned in a week \U0001F600\U0001F600", T)   # two emoji
    assert caption_problems("cloned in 2 days", T)                       # number not said


def test_offline_writer_only_cuts_from_transcript():
    for h in offline_hooks(T):
        assert hook_problems(h, T) == [] or h.pattern == "problem_first"
    assert all(not caption_problems(c, T) for c in offline_captions(T, 3))
