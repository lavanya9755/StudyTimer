# ── Soft Pastel Cat Cloud Theme ──────────────────────────────────────────────
# Dreamy pink → peach pastel sky (like the reference cat illustration).
# Buttons keep their vivid neon look from the previous theme — only the
# background palette + text colors change so everything stays readable.

# Backgrounds (used as fallbacks + for solid surfaces).
# The real magic is the GRADIENT_* stops below, painted by widgets.py.
BG_DARK = "#F6C6D2"   # dusty rose (sidebar fallback)
BG_MID = "#FBD9D2"    # blush peach main bg (behind gradient canvas)
CARD_BG = "#FFF3F5"   # cloud-white card
CARD_BORDER = "#F5B4C8"  # soft pink border
SURFACE = "#FCE4E9"   # raised cloud surface

# Gradient stops — consumed by widgets.py to paint panels & windows.
# Top → bottom mirrors the reference: pink sky melting into peach glow.
GRADIENT_LEFT_PANEL = ("#F6C2D1", "#FAD0C9", "#FBE3D3")   # pink → peach → cream
GRADIENT_MAIN_BG    = ("#F8D0DD", "#FAD0C9", "#FBE3D3")   # pastel sky
GRADIENT_CARD       = ("#FFF1F4", "#FCE0E8")              # card sheen
GRADIENT_ANALYTICS  = ("#FCE4EC", "#F8CBD8", "#FAD0B9")   # cotton-candy sunset

# Accents — kept vivid so buttons & highlights still pop on pastels.
ACCENT1 = "#FF5CD2"   # hot neon pink
ACCENT2 = "#9B6BFF"   # electric lilac
ACCENT3 = "#5DE0FF"   # cyan glow
ACCENT4 = "#7CFFB2"   # mint glow
ACCENT_WARN = "#FFB347"  # warm peach

# Text — dark plum/rose for legibility on pale pink backgrounds.
TEXT_PRIMARY = "#5B2A4A"     # deep plum
TEXT_SECONDARY = "#8A4A6B"   # muted mauve
TEXT_MUTED = "#B07E94"       # dusty rose

# Gradient-style button pairs (base, hover). Vivid → brighter on hover for glow lift.
BTN_START   = ("#FF5CD2", "#FF8AE2")   # neon pink
BTN_PAUSE   = ("#FFD75C", "#FFE899")   # gold
BTN_RESET   = ("#9B6BFF", "#B894FF")   # electric lilac
BTN_END     = ("#FF3D9A", "#FF6FB6")   # magenta
BTN_SECONDARY = ("#3A1A5C", "#5A2080")  # glassy purple
BTN_EXPORT_PDF = ("#FF6FB6", "#FF94CC")
BTN_EXPORT_XLS = ("#5DE0FF", "#8AECFF")

TAB_SELECTED   = "#FF5CD2"
TAB_HOVER      = "#FF8AE2"
TAB_UNSELECTED = "#3A1A5C"

# Glow ring colors — used by widgets.py for the halo border effect.
GLOW_PINK   = "#FFB8F0"
GLOW_LILAC  = "#C9B0FF"
GLOW_CYAN   = "#A6F0FF"
GLOW_MINT   = "#C0FFD9"

PAD = 16
CARD_RADIUS = 18
BTN_RADIUS = 24
BTN_HEIGHT = 46
BTN_BORDER_WIDTH = 3   # thicker so the glow ring reads