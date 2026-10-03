"""Render a plan with FFmpeg (design 1.6). Filter order matters: trim, mirror, zoom, colour, speed, then text.

Our text is overlaid after the mirror, so it never reads backwards. No music is ever added.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image

from . import config as C
from .media import has_filter, run
from .plan import VersionPlan

TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


@lru_cache(maxsize=None)
def _has(name: str) -> bool:
    return has_filter(name)


def base_chain(vp: VersionPlan, hdr: bool) -> str:
    """Everything up to (not including) speed and text: also used for the cover frame."""
    lk = vp.look
    f = []
    if hdr and _has("zscale") and _has("tonemap"):
        f.append(TONEMAP)
    if lk.mirror:
        f.append("hflip")
    f.append(f"scale={C.W}:{C.H}:force_original_aspect_ratio=increase,crop={C.W}:{C.H}")
    if lk.zoom > 1.0:
        zw, zh = 2 * round(C.W * lk.zoom / 2), 2 * round(C.H * lk.zoom / 2)
        ox, oy = vp.geo.offset
        f.append(f"scale={zw}:{zh},crop={C.W}:{C.H}:{round(ox * lk.zoom)}:{round(oy * lk.zoom)}")
    f.append(f"eq=brightness={lk.brightness}:saturation={lk.saturation}")
    f.append("setsar=1")
    return ",".join(f)


def audio_chain(speed: float) -> str:
    # Keep pitch so the voice doesn't sound sped up. rubberband sounds better than atempo when present.
    stretch = f"rubberband=tempo={speed}:pitchq=quality" if _has("rubberband") else f"atempo={speed}"
    return f"{stretch},afade=t=in:d=0.01,aresample=48000"


def command(vp: VersionPlan, src: str, out: Path, hdr: bool) -> list[str]:
    lk = vp.look
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if lk.trim > 0:
        cmd += ["-ss", f"{lk.trim:.3f}"]
    cmd += ["-i", src]
    for o in vp.overlays:
        cmd += ["-i", o.png]
    fc = [f"[0:v]{base_chain(vp, hdr)},setpts=(PTS-STARTPTS)/{lk.speed},fps={C.FPS}[v0]"]
    last = "v0"
    for k, o in enumerate(vp.overlays, 1):
        fc.append(f"[{last}][{k}:v]overlay={o.x}:{o.y}:enable='between(t,{o.t0},{o.t1})':eof_action=repeat[v{k}]")
        last = f"v{k}"
    fc.append(f"[{last}]format=yuv420p[vout]")
    fc.append(f"[0:a]asetpts=PTS-STARTPTS,{audio_chain(lk.speed)}[aout]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", str(lk.crf),
            "-g", str(lk.gop), "-r", str(C.FPS), "-color_primaries", "bt709", "-color_trc", "bt709",
            "-colorspace", "bt709", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-map_metadata", "-1", "-movflags", "+faststart", "-shortest", str(out)]
    return cmd


def render(vp: VersionPlan, src: str, out: Path, hdr: bool) -> Path:
    run(command(vp, src, out, hdr))
    return out


def cover(vp: VersionPlan, src: str, out: Path, hdr: bool) -> Path:
    """The chosen source frame with this version's mirror/zoom/colour, plus the cover text. 1080x1920 JPG."""
    raw = out.with_suffix(".frame.png")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{vp.cover_src_t:.3f}", "-i", src,
         "-vf", base_chain(vp, hdr), "-frames:v", "1", str(raw)])
    img = Image.open(raw).convert("RGBA")
    o = vp.cover_overlay
    img.alpha_composite(Image.open(o.png).convert("RGBA"), (o.x, o.y))
    img.convert("RGB").save(out, "JPEG", quality=92)
    raw.unlink(missing_ok=True)
    return out
