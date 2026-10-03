# Trial reel tool: what "ready" means

Written 2026-10-03 from the editing skill (`.claude/skills/daily-content/SKILL.md`, sections "Trial-reel variants",
"Safe area", "Clear visuals", "On-screen rules", "Captions", "Phase C0") and the day 1 trial results
(`posts/2026-10-01--day1-app-cloned-trials.md`). Everything below is what we already do by hand for Jordan's posts.
"Must" = needed before launch. "Should" = next version.

## 1. What it does

Someone uploads one vertical video. The tool sends back up to 5 versions of the same video, each with a different hook
and a different look, plus a cover and a caption for each, so they can post them as Instagram trial reels and see which
one strangers like best.

## 2. Input

- **Must:** one video, vertical (9:16), 5 to 90 seconds, MOV or MP4, up to 500 MB.
- **Must:** reject anything else with a plain message ("This video is sideways. Upload a vertical one.").
- **Must:** the user can type their own hook. If they leave it empty, the tool writes the hooks.
- **Should:** the user ticks what may change (for example "don't mirror, my video has text in it").

## 3. Output, for each version

- **Must:** the video, 1080 x 1920, H.264, roughly the same length as the original.
- **Must:** a cover image (1080 x 1920 JPG).
- **Must:** a caption (one line).
- **Must:** a short "what changed" list, so the user knows what the test is testing
  (for example "hook: number first; mirrored; 1.2x; Futura captions").
- **Must:** a posting order and the posting guide (section 8) on the download page.
- Default 4 versions, never more than 5 (Instagram's daily trial cap, see section 8).

## 4. The hook: the main thing that changes

On day 1 the hook was the only change that clearly mattered. The winning version got 1,933 views; the other three got
218, 52 and 47. They differed mainly in their hook.

- **Must:** every version has its own on-screen hook text. No two the same.
- **Must:** each hook follows a known pattern, and the pattern is named in "what changed":
  number first, threat or problem first, a short "how to", a specific named person or thing ("a Turkish studio"),
  a question. (Pattern list: `reference/research/hook-bank.md`.)
- **Must:** hooks come only from what is said in the video. No made-up numbers, names or claims.
- **Must:** hook text is under 10 words, at most two lines.
- **Should:** change the first words heard too, not only the text. We do this by moving a stronger sentence to the
  start (number first, threat first). It needs the transcript and clean cut points; a cut must never break a sentence.

## 5. The look: change several of these on every version

Each version must differ from every other version in its hook **and at least 3** of these. Ranges are the ones we use.

| Change | Range we use | Notes |
|---|---|---|
| Speed | 1.15x to 1.25x | Voice must not sound sped up. Keep pitch. |
| Mirror | on / off | Mirrors any text filmed in the video. Off if the user says the video has text. Overlays are drawn after the mirror, so the tool's own text never reads backwards. |
| Zoom | 1.00 to 1.05 | Small. Must not crop the face or the hands. |
| Colour | brightness +0 to +0.03, saturation 1.00 to 1.04 | Subtle. Must not look filtered. |
| Caption font | Futura, SF Pro Display, Helvetica Neue | Never Avenir Next (renders italic). |
| Caption size | small / medium / large | All must pass the size rule in section 6. |
| Hook style | white bold with soft shadow, no box (our default) / black text on white pill / other colours | Same font family across one video. |
| Start trim | cut 0.2 to 0.8 s off the start | Never cut into the first word. |
| Re-export | different quality setting per version | Makes each file different. |
| Music | none (default) | Never add a song. The user adds sound in the Instagram app. |

- **Must:** no two versions get the same combination.
- **Must:** a version that only changes the look and keeps the same hook is not allowed.

## 6. Rules every version must pass before it is shown to the user

These are checked by the tool, not by eye. A version that fails is fixed or not delivered.

**Safe area (from Jordan's live reel on an iPhone):** all text, captions and images sit inside
x 75 to 1005, y 270 to 1540, and nothing goes right of x 900 below y 1230 (like, comment, share buttons).
Above y 270 is the clock and reel header. Below y 1540 is the name and caption.

**Readable on a phone:**
- Any text a viewer must read is at least 28 px tall on the 1080-wide frame.
- Anything on screen stays at least 1.2 seconds.
- Text never covers the face.

**Timing:**
- The hook shows for the first sentence (about 1.5 to 3 seconds), then goes.
- Nothing else stays on screen for long. Labels last 1.5 to 3.5 seconds.

**Captions burned into the video (if on):**
- 1 to 4 words at a time, white bold with a dark edge.
- Words match what is said. Show the user the transcript so they can fix misheard words before export.

**Sound:**
- The voice is not clipped at any cut, not even a soft last word.
- No music added.

## 7. Cover and caption

**Cover (must):**
- A frame where the person's mouth is closed and they look composed. Never mid-word or blinking.
- A different frame or a different cover text on each version.
- The hook (or a short form of it) on the cover, inside the safe area.

**Caption (must):**
- One flat line, lower case, no hashtags, at most one emoji, no long dashes.
- Different on every version. Never the same caption on two trials.
- Facts only from the video.
- **Should:** an optional comment-keyword line ("comment TRIAL and I'll send it"). It gets the most comments,
  but only works if the user really sends something to everyone who comments.

## 8. Posting guide (shown on the download page)

1. Post every version as a trial reel. "Trial" on. "Share automatically with everyone" **off**.
2. **At most 5 trials a day.** Guides report a cap of about 5; going over can block trials for 30 days.
3. Post order: the version least like the last one goes next. Versions that open with the same words go last
   and far apart.
4. Set each version's cover and paste its own caption.
5. After 24 hours, compare views. Share the top one to your profile only if it has about **double** the middle one.
   If they are close, share your original. A few hundred views apart is noise, not a winner.

## 9. Not in this version

- Stickers and in-app songs (the user adds these in Instagram).
- Posting to Instagram for the user.
- Images or b-roll added on top of the video.
- Promising that it gets past Instagram's copy detection. We have not proven that (see section 11).

## 10. Money

- **Must:** one free generation per account. Sign-in needed, so one person can't take endless free runs.
- **Must:** the price per generation is set after measuring what one run really costs (transcript, hook writing,
  video work, storage). Show the real cost next to the price in the admin view.
- **Must:** a failed run is not charged and does not use up the free one.

## 11. Ready checklist

The tool is ready when all of these are true:

- [ ] Upload a real talking head (use day 1's `raw/IMG_4239.MOV` and day 2's `raw/E51D108D-...MOV`): 4 versions come back.
- [ ] Every version has its own hook, from a named pattern, using only what is said in the video.
- [ ] Every version differs from every other in the hook plus at least 3 changes from section 5.
- [ ] Every version passes the safe area, size and timing checks in section 6, on every frame, not one frame.
- [ ] No clipped words at any cut (listen to each version start to finish).
- [ ] Each version has its own cover (mouth closed) and its own one-line caption.
- [ ] The posting guide and the "what changed" list are on the download page.
- [ ] A sideways video, a 3-minute video and a silent video each get a clear error, and no charge.
- [ ] The free run works once per account, then asks for payment.
- [ ] One full run finishes in a time a person will wait for (measure it and put it on the page).

**After launch, the real test:** Jordan posts 4 versions from the tool as trials on his own account and writes the
24-hour views next to each hook. On day 1, three of four versions barely got shown (218, 52, 47). Either their hooks
were weaker, or Instagram treated the later uploads as copies; one test cannot tell. If tool versions show the same
pattern, the look changes are not enough and the first words must change too (section 4, "should").
