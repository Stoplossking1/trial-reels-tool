"""Draw hook, caption and cover text as transparent PNGs with the real font files.

We draw text ourselves (not with ffmpeg drawtext) so every box's exact pixels are known to the checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config as C

MAX_TEXT_W = C.SAFE_X1 - C.SAFE_X0           # 930: full safe width
MAX_TEXT_W_LOW = C.BUTTONS_X - C.SAFE_X0     # 825: below the buttons line


def available_fonts() -> list[str]:
    out = []
    for fam, files in C.FONTS.items():
        if fam in C.BANNED_FONTS:
            continue
        if all((C.FONT_DIR / f).exists() for f in files.values()):
            out.append(fam)
    return out


@lru_cache(maxsize=64)
def font(family: str, weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(C.FONT_DIR / C.FONTS[family][weight]), size)


def cap_height(f: ImageFont.FreeTypeFont) -> int:
    b = f.getbbox("H")
    return b[3] - b[1]


def wrap(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        trial = f"{cur} {w}".strip()
        if f.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def balanced(text: str, f: ImageFont.FreeTypeFont, max_w: int, max_lines: int) -> list[str] | None:
    """Wrap into at most max_lines; for two lines, split where the lines are most even."""
    lines = wrap(text, f, max_w)
    if len(lines) > max_lines:
        return None
    if len(lines) == 2:
        ws = text.split()
        best = None
        for k in range(1, len(ws)):
            a, b = " ".join(ws[:k]), " ".join(ws[k:])
            la, lb = f.getlength(a), f.getlength(b)
            if la <= max_w and lb <= max_w and (best is None or abs(la - lb) < best[0]):
                best = (abs(la - lb), [a, b])
        lines = best[1] if best else lines
    return lines


@dataclass
class TextImage:
    image: Image.Image
    cap_px: int      # cap height of the text, for the 28 px rule
    lines: int


PAD_X, PAD_Y = 34, 22


def draw_text(lines: list[str], f: ImageFont.FreeTypeFont, style: str) -> TextImage:
    """style: white_shadow | black_on_white_pill | white_on_black_pill | caption (white, dark edge)"""
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * 1.08)
    tw = int(max(f.getlength(l) for l in lines))
    stroke = max(3, f.size // 14) if style == "caption" else 0
    shadow = 14 if style == "white_shadow" else 0
    pad_x = PAD_X if "pill" in style else stroke + shadow
    pad_y = PAD_Y if "pill" in style else stroke + shadow
    w, h = tw + 2 * pad_x, lh * len(lines) + 2 * pad_y
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if "pill" in style:
        bg = (255, 255, 255, 255) if style == "black_on_white_pill" else (0, 0, 0, 205)
        ImageDraw.Draw(img).rounded_rectangle((0, 0, w - 1, h - 1), radius=min(28, h // 2), fill=bg)
    fg = (0, 0, 0, 255) if style == "black_on_white_pill" else (255, 255, 255, 255)
    if shadow:
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        for i, line in enumerate(lines):
            x = (w - f.getlength(line)) / 2
            d.text((x + 3, pad_y + i * lh + 4), line, font=f, fill=(0, 0, 0, 170))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        x = (w - f.getlength(line)) / 2
        d.text((x, pad_y + i * lh), line, font=f, fill=fg,
               stroke_width=stroke, stroke_fill=(0, 0, 0, 255) if stroke else None)
    return TextImage(img, cap_height(f), len(lines))


def fit_hook(text: str, family: str, style: str, start_size: int = 84, min_size: int = 44,
             max_w: int = MAX_TEXT_W) -> TextImage | None:
    """Largest size (<= start_size) where the hook fits in two lines inside max_w. None if it never fits."""
    inner = max_w - 2 * PAD_X
    for size in range(start_size, min_size - 1, -2):
        f = font(family, "bold", size)
        lines = balanced(text, f, inner, C.HOOK_MAX_LINES)
        if lines:
            ti = draw_text(lines, f, style)
            if ti.image.width <= max_w:
                return ti
    return None


def caption_image(text: str, family: str, size_name: str, max_w: int = MAX_TEXT_W_LOW) -> TextImage:
    size = C.CAPTION_SIZES[size_name]
    while True:
        f = font(family, "bold", size)
        lines = balanced(text, f, max_w - 20, 2)
        if lines:
            ti = draw_text(lines, f, "caption")
            if ti.image.width <= max_w or size <= 40:
                return ti
        size -= 2


def save(ti: TextImage, path: Path) -> Path:
    ti.image.save(path)
    return path
