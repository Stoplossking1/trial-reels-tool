"""Fixed numbers from docs/ready.md. Change them here, nowhere else."""
from pathlib import Path

W, H = 1080, 1920
FPS = 30

# Input limits (R2)
MIN_S = 5.0  # no maximum length (removed 2026-10-03); the 500 MB cap still applies
MAX_BYTES = 500 * 1024 * 1024
ASPECT_TOLERANCE = 0.02

# Versions (R3)
DEFAULT_VERSIONS, MAX_VERSIONS = 4, 5

# Safe area (R6): text must sit inside this box ...
SAFE_X0, SAFE_Y0, SAFE_X1, SAFE_Y1 = 75, 270, 1005, 1540
# ... and nothing may go right of this x below this y (like/comment/share buttons).
BUTTONS_X, BUTTONS_Y = 900, 1230

# Readability (R6)
MIN_TEXT_PX = 28          # cap height on the 1080-wide frame
MIN_ON_SCREEN_S = 1.2
HOOK_MIN_S, HOOK_MAX_S = 1.5, 3.0
LABEL_MAX_S = 3.5
FACE_PAD = 0.04           # face box grows by this share of frame size before overlap tests

# Hook text (R4)
HOOK_MAX_WORDS = 9        # "under 10 words"
HOOK_MAX_LINES = 2

# Look ranges (R5)
SPEED_RANGE = (1.15, 1.25)
ZOOM_RANGE = (1.00, 1.05)
BRIGHTNESS_RANGE = (0.0, 0.03)
SATURATION_RANGE = (1.00, 1.04)
TRIM_RANGE = (0.2, 0.8)
CRF_CHOICES = (18, 20, 22, 24)
GOP_CHOICES = (30, 45, 60, 90)
CAPTION_SIZES = {"small": 54, "medium": 64, "large": 76}
HOOK_STYLES = ("white_shadow", "black_on_white_pill", "white_on_black_pill")
MIN_LOOK_CHANGES = 3

# Minimum gaps so two versions really differ on a setting
MIN_DIFF = {"speed": 0.04, "zoom": 0.015, "brightness": 0.01, "saturation": 0.01, "trim": 0.2, "crf": 2}

# Audio
QUIET_DB = -40.0          # below this (or noise floor + 6 dB, whichever is higher) counts as quiet
QUIET_RUN_S = 0.06
CUT_WINDOW_S = 0.04

# Fonts: family -> files by weight. Licensed fonts are not in git; see worker/fonts/README.md.
FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
FONTS = {
    "Instagram Sans": {"bold": "Instagram_Sans_Bold.ttf", "medium": "Instagram_Sans_Medium.ttf"},
    "SF Pro Display": {"bold": "SF-Pro-Display-Bold.otf", "medium": "SF-Pro-Display-Medium.otf"},
    "Helvetica Neue": {"bold": "Helvetica-Neue-Bold.otf", "medium": "Helvetica-Neue-Medium.otf"},
    "Jost": {"bold": "Jost-Bold.ttf", "medium": "Jost-Medium.ttf"},
    "Inter": {"bold": "Inter-Bold.ttf", "medium": "Inter-Medium.ttf"},
}
BANNED_FONTS = ("Avenir Next",)  # renders italic

# Claude
CLAUDE_MODEL = "claude-opus-5-5"

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_BANK = REPO_ROOT / "reference" / "research" / "hook-bank.md"
