"""Cat-themed UI helpers: glowing gradient buttons and dreamy panel backgrounds."""

import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageFilter, ImageDraw

from ui.theme import *


def assets_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CAT_BG_TODAY = os.path.join(assets_dir(), "cat bg 2.png")
CAT_BG_ANALYTICS = os.path.join(assets_dir(), "cat bg 1.png")


# ── Gradient painter ────────────────────────────────────────────────────────

def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def paint_vertical_gradient(canvas: tk.Canvas, stops, tag: str = "grad"):
    """Paint a smooth multi-stop vertical gradient onto a Canvas, full size."""
    canvas.delete(tag)
    w = max(canvas.winfo_width(), 2)
    h = max(canvas.winfo_height(), 2)
    rgb_stops = [_hex_to_rgb(c) for c in stops]
    segs = len(rgb_stops) - 1
    for y in range(h):
        t = y / max(h - 1, 1)
        pos = t * segs
        i = min(int(pos), segs - 1)
        local = pos - i
        r1, g1, b1 = rgb_stops[i]
        r2, g2, b2 = rgb_stops[i + 1]
        r = int(r1 + (r2 - r1) * local)
        g = int(g1 + (g2 - g1) * local)
        b = int(b1 + (b2 - b1) * local)
        canvas.create_line(0, y, w, y, fill=f"#{r:02x}{g:02x}{b:02x}", tags=tag)
    canvas.tag_lower(tag)


def make_gradient_canvas(parent, stops, width=None, height=None) -> tk.Canvas:
    """Create a Canvas that repaints a gradient on resize."""
    kwargs = {"highlightthickness": 0, "bd": 0}
    if width:
        kwargs["width"] = width
    if height:
        kwargs["height"] = height
    canvas = tk.Canvas(parent, **kwargs)

    def _repaint(_e=None):
        paint_vertical_gradient(canvas, stops)

    canvas.bind("<Configure>", _repaint)
    canvas.after(60, _repaint)
    return canvas


# ── Glowing gradient button ─────────────────────────────────────────────────

_GLOW_MAP = {
    BTN_START[0]:   GLOW_PINK,
    BTN_PAUSE[0]:   "#FFE799",
    BTN_RESET[0]:   GLOW_LILAC,
    BTN_END[0]:     "#FF9CC8",
    BTN_EXPORT_PDF[0]: GLOW_PINK,
    BTN_EXPORT_XLS[0]: GLOW_CYAN,
    BTN_SECONDARY[0]: GLOW_LILAC,
    ACCENT1: GLOW_PINK,
    ACCENT2: GLOW_LILAC,
    ACCENT3: GLOW_CYAN,
    SURFACE: GLOW_LILAC,
}


def _border_for(fg: str) -> str:
    return _GLOW_MAP.get(fg, GLOW_PINK)


def create_cat_button(
    master,
    text: str,
    fg_color,
    hover_color,
    command=None,
    *,
    text_color="#FFFFFF",
    width=None,
    height=BTN_HEIGHT,
    font_size=14,
    bold=True,
    state="normal",
    pack_kwargs=None,
    grid_kwargs=None,
    **extra,
):
    """Rounded pill button with a glowing pink/lilac halo border."""
    border = _border_for(fg_color if isinstance(fg_color, str) else fg_color[0] if fg_color else ACCENT1)
    font = ctk.CTkFont(
        family="Segoe UI",
        size=font_size,
        weight="bold" if bold else "normal",
    )
    btn = ctk.CTkButton(
        master,
        text=text,
        fg_color=fg_color,
        hover_color=hover_color,
        text_color=text_color,
        font=font,
        height=height,
        corner_radius=BTN_RADIUS,
        border_width=BTN_BORDER_WIDTH,
        border_color=border,
        command=command,
        state=state,
        **extra,
    )
    if width is not None:
        btn.configure(width=width)

    # Subtle hover glow: brighten the border when the cursor enters.
    def _on_enter(_e):
        btn.configure(border_color="#FFFFFF")

    def _on_leave(_e):
        btn.configure(border_color=border)

    btn.bind("<Enter>", _on_enter)
    btn.bind("<Leave>", _on_leave)

    if pack_kwargs is not None:
        btn.pack(**pack_kwargs)
    elif grid_kwargs is not None:
        btn.grid(**grid_kwargs)
    return btn


# ── Cat panel background (gradient + glow + cat image) ──────────────────────

def setup_cat_panel_background(tab: ctk.CTkFrame, image_path: str) -> ctk.CTkFrame:
    """
    Layered panel background:
      1. multi-stop nebula gradient
      2. soft glowing radial bloom
      3. cat image with violet/pink overlay
    Returns a transparent container for scrollable content.
    """
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(0, weight=1)

    bg_canvas = tk.Canvas(tab, highlightthickness=0, bd=0)
    bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

    container = ctk.CTkFrame(tab, fg_color="transparent")
    container.place(x=0, y=0, relwidth=1, relheight=1)
    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=1)

    state = {"photo": None, "path": image_path}

    def _composed_image(w: int, h: int) -> Image.Image:
        # 1) gradient base (pastel pink → peach sky)
        grad = Image.new("RGB", (w, h))
        stops = [_hex_to_rgb(c) for c in GRADIENT_ANALYTICS]
        segs = len(stops) - 1
        px = grad.load()
        for y in range(h):
            t = y / max(h - 1, 1)
            pos = t * segs
            i = min(int(pos), segs - 1)
            local = pos - i
            r1, g1, b1 = stops[i]
            r2, g2, b2 = stops[i + 1]
            r = int(r1 + (r2 - r1) * local)
            g = int(g1 + (g2 - g1) * local)
            b = int(b1 + (b2 - b1) * local)
            for x in range(w):
                px[x, y] = (r, g, b)
        base = grad.convert("RGBA")

        # 2) soft cloud-bloom (two pastel circles for a dreamy haze)
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([-w * 0.2, -h * 0.3, w * 0.6, h * 0.5], fill=(255, 220, 230, 130))
        gd.ellipse([w * 0.5, h * 0.4, w * 1.2, h * 1.1], fill=(255, 210, 190, 130))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=70))
        base = Image.alpha_composite(base, glow)

        # 3) cat photo with a gentle blush wash (keeps the illustration soft)
        try:
            cat = Image.open(state["path"]).convert("RGBA")
            cat = cat.resize((w, h), Image.Resampling.LANCZOS)
            cat = cat.filter(ImageFilter.GaussianBlur(radius=0.6))
            wash = Image.new("RGBA", (w, h), (255, 200, 215, 70))
            cat = Image.alpha_composite(cat, wash)
            # Blend cat softly over the gradient (a touch stronger so the
            # kitten reads clearly against the pale sky).
            base = Image.blend(base, cat, alpha=0.55)
        except OSError:
            pass

        return base

    def _redraw(_event=None):
        w = tab.winfo_width()
        h = tab.winfo_height()
        if w < 4 or h < 4:
            return
        try:
            img = _composed_image(w, h)
            state["photo"] = ImageTk.PhotoImage(img)
            bg_canvas.delete("all")
            bg_canvas.create_image(0, 0, anchor="nw", image=state["photo"])
        except OSError:
            bg_canvas.configure(bg=BG_MID)

    tab.bind("<Configure>", _redraw)
    tab.after(80, _redraw)
    return container