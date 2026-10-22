#!/usr/bin/env python3
"""Builds the Aion Group-branded profile README assets (dark + light SVGs).

Fonts (Outfit, JetBrains Mono) are subset and embedded as WOFF so GitHub
renders them inside <img>. Run: python3 build.py
"""
import base64, io, re, html
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools import subset

ROOT = Path(__file__).parent
OUT = ROOT / "assets"
BRAND = Path.home() / "Projects/brands/aion-group"
FONTS = BRAND / "website/site/assets/fonts"
SYMBOL = BRAND / "delivery/symbol/aion-group-symbol-on-dark.svg"

FONT_FILES = {
    ("Outfit", 300): FONTS / "Outfit-300.ttf",
    ("Outfit", 400): FONTS / "Outfit-400.ttf",
    ("Outfit", 500): FONTS / "Outfit-500.ttf",
    ("JBM", 400): FONTS / "JetBrainsMono-400.ttf",
}
_tt = {k: TTFont(v) for k, v in FONT_FILES.items()}

CORAL = "#FF6B3D"
THEMES = {
    "dark": dict(bg="#0B0C10", card="#0E0F13", line="#FFFFFF1A", grid="#FFFFFF0A",
                 fg="#F3F3F0", muted="#F3F3F099", faint="#F3F3F059", g="#FFFFFF"),
    "light": dict(bg="#F3F3F0", card="#F7F6F2", line="#0B0C1021", grid="#0B0C100D",
                  fg="#0B0C10", muted="#0B0C1099", faint="#0B0C1066", g="#0B0C10"),
}


def width(s, fam, wt, size, track=0.0):
    f = _tt[(fam, wt)]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(c), cmap[32])][0] for c in s)
    return w / upm * size + track * size * max(len(s) - 1, 0)


class Svg:
    def __init__(self, w, h, theme):
        self.w, self.h, self.t, self.parts, self.chars = w, h, THEMES[theme], [], {}
        self.theme = theme

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, fam="Outfit", wt=400, size=16, fill=None, track=0.0,
             anchor="start", extra=""):
        self.chars.setdefault((fam, wt), set()).update(s)
        fill = fill or self.t["fg"]
        ls = f' letter-spacing="{track * size:.2f}"' if track else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{wt}" '
                 f'font-size="{size}" fill="{fill}"{ls} text-anchor="{anchor}" {extra}>'
                 f'{html.escape(s)}</text>')

    def kicker(self, x, y, num, label):
        # mono "NN — Label" kicker in coral, as on aiongp.com
        self.text(x, y, f"{num} — {label.upper()}", "JBM", 400, 11.5, CORAL, track=0.12)

    def fonts_css(self):
        css = []
        for (fam, wt), chars in self.chars.items():
            opts = subset.Options(); opts.flavor = "woff"; opts.layout_features = ["kern", "liga"]
            ss = subset.Subsetter(opts)
            ss.populate(text="".join(chars) + " ")
            f = TTFont(FONT_FILES[(fam, wt)]); ss.subset(f)
            buf = io.BytesIO(); f.flavor = "woff"; f.save(buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
            css.append(f"@font-face{{font-family:{fam};font-weight:{wt};"
                       f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
        return "".join(css)

    def render(self, title, anim_css=""):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{html.escape(title)}">'
                f'<title>{html.escape(title)}</title>'
                f'<style>{self.fonts_css()}{anim_css}</style>' + "".join(self.parts) + "</svg>")


_fid = [0]


def frame(svg, r=16, fill=None, tick=True, glow=True):
    """aiongp.com card: top-lit gradient, coral glow from the bottom-right, coral tick on the top edge."""
    t = svg.t; _fid[0] += 1; i = _fid[0]
    dark = svg.theme == "dark"
    top, bot = ("#17171A", "#0A0A0C") if dark else ("#FFFFFF", "#F3F2EE")
    ga = .16 if dark else .10
    svg.add(f'<defs><linearGradient id="cg{i}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>'
            f'<radialGradient id="cr{i}" cx="1" cy="1" r="0.9" gradientTransform="translate(0 0)">'
            f'<stop offset="0" stop-color="{CORAL}" stop-opacity="{ga}"/>'
            f'<stop offset="1" stop-color="{CORAL}" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="cs{i}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{"#FFFFFF" if dark else "#0B0C10"}" stop-opacity="{.16 if dark else .14}"/>'
            f'<stop offset="1" stop-color="{"#FFFFFF" if dark else "#0B0C10"}" stop-opacity="{.05 if dark else .08}"/></linearGradient></defs>')
    box = f'x="0.5" y="0.5" width="{svg.w-1}" height="{svg.h-1}" rx="{r}"'
    svg.add(f'<rect {box} fill="{fill or f"url(#cg{i})"}"/>')
    if glow:
        svg.add(f'<rect {box} fill="url(#cr{i})"/>')
    svg.add(f'<rect {box} fill="none" stroke="url(#cs{i})"/>')
    if tick:
        svg.add(f'<path d="M{r+8} 0.75H{r+38}" stroke="{CORAL}" stroke-width="1.5"/>')


def crosshairs(svg, inset=18, n=7):
    c = svg.t["faint"]
    for x, y in [(inset, inset), (svg.w - inset, inset), (inset, svg.h - inset), (svg.w - inset, svg.h - inset)]:
        svg.add(f'<path d="M{x-n} {y}H{x+n}M{x} {y-n}V{y+n}" stroke="{c}" stroke-width="1"/>')


def symbol(theme, x, y, size, a_fill=CORAL, g_fill=None):
    s = SYMBOL.read_text()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
    paths = re.findall(r"<path[^>]*/>", s)
    g_fill = g_fill or THEMES[theme]["g"]
    paths = [p.replace('fill="#FF6B3D"', f'fill="{a_fill}"').replace('fill="#FFFFFF"', f'fill="{g_fill}"') for p in paths]
    k = size / vb[2]
    return (f'<g transform="translate({x} {y}) scale({k:.5f}) translate({-vb[0]} {-vb[1]})">'
            + "".join(paths) + "</g>")


# ───────────────────────────── pieces ─────────────────────────────
W = 880


def smoke(w, h, n=46, seed=7):
    """Port of the aiongp.com hero 'smoke' canvas: drifting elliptical plumes, additive blend.
    Each plume follows the same Lissajous path as the site (cos(a+t), sin(1.3a+k+t)) as a looping SMIL motion."""
    import math, random
    rnd = random.Random(seed)
    cols = ["#FFFFFF"] * 4 + ["#FF7846"]
    out = ['<defs>']
    plumes = []
    for i in range(n):
        a, r, k, z = rnd.random() * 6.28, .25 + rnd.random() * .32, rnd.random() * 6.28, .45 + rnd.random() * .9
        c, o = cols[i % 5], (.05 if i % 5 > 2 else .06) * 1.35
        R = min(w, h) * .28 * z * 1.25
        out.append(f'<radialGradient id="sg{i}" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="{R:.1f}">'
                   f'<stop offset="0" stop-color="{c}" stop-opacity="{o:.3f}"/>'
                   f'<stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>')
        pts = []
        for j in range(61):
            tt = j / 60 * 2 * math.pi
            pts.append((w * .5 + math.cos(a + tt) * w * r * .9, h * .45 + math.sin(a * 1.3 + k + tt) * h * r * .6))
        d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
        dur = 70 + rnd.random() * 50
        plumes.append(f'<g style="mix-blend-mode:plus-lighter"><ellipse rx="{R*1.7:.1f}" ry="{R*.55:.1f}" '
                      f'transform="rotate({math.degrees(a*.6):.1f})" fill="url(#sg{i})"/>'
                      f'<animateMotion dur="{dur:.0f}s" repeatCount="indefinite" path="{d}"/></g>')
    out.append('</defs>')
    return "".join(out) + "".join(plumes)


def hero(theme):
    # The hero is always dark, exactly like the aiongp.com header, in both GitHub themes.
    H = 360
    s = Svg(W, H, "dark"); t = s.t
    s.add(f'<defs><clipPath id="c"><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18"/></clipPath>'
          f'<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset=".62" stop-color="#000" stop-opacity="0"/>'
          f'<stop offset="1" stop-color="#000"/></linearGradient>'
          f'<radialGradient id="vig" cx=".5" cy=".45" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
          f'<stop offset="1" stop-color="#000" stop-opacity=".7"/></radialGradient>'
          f'<radialGradient id="ember" cx=".72" cy=".72" r=".45"><stop offset="0" stop-color="{CORAL}" stop-opacity=".10"/>'
          f'<stop offset="1" stop-color="{CORAL}" stop-opacity="0"/></radialGradient>'
          f'<linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="{CORAL}" stop-opacity="0"/>'
          f'<stop offset=".5" stop-color="{CORAL}"/><stop offset="1" stop-color="{CORAL}" stop-opacity="0"/></linearGradient></defs>')
    s.add('<g clip-path="url(#c)">')
    s.add(f'<rect width="{W}" height="{H}" fill="#000"/>')
    s.add(f'<g style="isolation:isolate">{smoke(W, H)}</g>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#ember)"/>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#vig)"/>')
    s.add(f'<rect width="{W}" height="{H}" fill="url(#fade)"/>')
    s.add('</g>')
    s.add(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#FFFFFF14"/>')
    cx = W / 2
    s.text(cx, 92, "FOUNDER  ·  NETHERLANDS", "JBM", 400, 11, "#FFFFFFA6", track=0.18, anchor="middle")
    s.text(cx, 176, "Thomas Visser", "Outfit", 500, 72, "#FFFFFF", track=-0.03, anchor="middle")
    tw1 = width("Knowledge that ", "Outfit", 400, 34, -0.02)
    tw2 = width("compounds.", "Outfit", 400, 34, -0.02)
    x0 = cx - (tw1 + tw2) / 2
    s.text(x0, 226, "Knowledge that ", "Outfit", 400, 34, "#FFFFFF73", track=-0.02, extra='xml:space="preserve"')
    s.text(x0 + tw1, 226, "compounds", "Outfit", 400, 34, "#FFFFFF", track=-0.02)
    s.text(x0 + tw1 + width("compounds", "Outfit", 400, 34, -0.02) + 1, 226, ".", "Outfit", 500, 34, CORAL)
    s.text(cx, 272, "Quant  |  Data architecture  |  Applied AI  |  Building in the open", "Outfit", 400, 15,
           "#FFFFFFD9", anchor="middle", extra='xml:space="preserve"')
    s.add(f'<path class="rule" d="M{cx-70} 306H{cx+70}" stroke="url(#rule)" stroke-width="1.5"/>')
    css = ("@keyframes rl{0%,100%{opacity:.35}50%{opacity:1}}.rule{animation:rl 3.2s ease-in-out infinite}")
    return s.render("Thomas Visser — Knowledge that compounds. Quant, data architecture, applied AI.", css)


def section(theme, num, label, title, sub=None):
    s = Svg(W, 92 if sub else 70, theme); t = s.t
    s.kicker(2, 22, num, label)
    s.text(0, 58, title, "Outfit", 500, 28, t["fg"], track=-0.02)
    if sub:
        s.text(0, 84, sub, "Outfit", 400, 14.5, t["muted"])
    return s.render(f"{num} — {label}: {title}")


VENTURES = [
    ("aion", "Aion Group", "Quant optimisation for financial products", "aiongp.com"),
    ("verticallm", "Verticallm", "Supply chain strategy, delivered by AI", "verticallm.ai"),
    ("tradeflow", "tradeflow.so", "Trading dashboard & trade replay", "tradeflow.so"),
    ("locally", "Locally", "Local-first AI for one-person businesses", "locallyai.nl"),
]

TREEMARK = ROOT / "src/verticallm-treemark.png"
LOCALLY_ICON = Path.home() / "Projects/brands/locally/delivery/symbol/locally-symbol-app-icon.svg"


def logo_tile(key, x, y, size):
    """Each venture's own app-icon: brand colour tile + mark (official assets, not redrawn)."""
    r = size * 0.24
    k = size / 256
    tile = lambda fill: f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{r}" fill="{fill}"/>'
    if key == "aion":
        return tile(CORAL) + symbol("dark", x + size * 0.18, y + size * 0.18, size * 0.64, "#FFFFFF", "#FFFFFF")
    if key == "tradeflow":  # LogoIcon from tradeflow.so (viewBox 500), white on brand orange
        m = size * 0.5 / 500
        paths = ("M0 0H3.4722C95.5196 0 170.139 74.6192 170.139 166.667V166.667H0V0Z"
                 "M500 0H333.333C241.286 0 166.667 74.6192 166.667 166.667V166.667H500V0Z"
                 "M333.333 500L333.333 329.861C333.333 237.814 258.714 163.194 166.666 163.194V163.194L166.666 500L333.333 500Z")
        return tile("#F94616") + (f'<path transform="translate({x + size*0.25} {y + size*0.25}) scale({m:.5f})" '
                                  f'd="{paths}" fill="#FFFFFF"/>')
    if key == "locally":  # official app icon, recoloured to the org avatar (volt tile, ink mark)
        svg = LOCALLY_ICON.read_text()
        inner = re.search(r"<g transform.*</g>", svg, re.S).group(0)
        inner = inner.replace("#CBFF4D", "#0F1113")
        return tile("#CBFF4D") + f'<g transform="translate({x} {y}) scale({k:.5f})">{inner}</g>'
    if key == "verticallm":
        from PIL import Image
        im = Image.open(TREEMARK).convert("RGBA"); im.thumbnail((192, 192))
        buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        pad = size * 0.18
        return tile("#C38A1F") + (f'<image x="{x+pad}" y="{y+pad}" width="{size-2*pad}" height="{size-2*pad}" '
                                  f'href="data:image/png;base64,{b64}"/>')


def venture(theme, v):
    key, name, desc, url = v
    s = Svg(432, 112, theme); t = s.t
    frame(s, 16)
    s.add(logo_tile(key, 24, 28, 56))
    s.text(100, 52, name, "Outfit", 500, 21, t["fg"], track=-0.015)
    s.text(100, 76, desc, "Outfit", 400, 13.5, t["muted"])
    s.text(408, 52, "↗", "JBM", 400, 14, t["faint"], anchor="end")
    return s.render(f"{name} — {desc} ({url})")


PRINCIPLES = [
    ("Data first,", "AI second.", "Models are only as strong", "as the data beneath them."),
    ("Evidence", "by default.", "Every model has to beat an", "honest baseline, out of sample."),
    ("No model", "lock-in.", "Swap providers and models", "without rebuilding the stack."),
    ("You keep", "the keys.", "Code, data and models are", "handed over — yours to own."),
]


def principles(theme):
    s = Svg(W, 182, theme); t = s.t
    frame(s, 16)
    cw = W / 4
    for i, (a, b, c, d) in enumerate(PRINCIPLES):
        x = i * cw + 26
        if i:
            s.add(f'<path d="M{i*cw} 30V152" stroke="{t["line"]}"/>')
        s.text(x, 62, a, "Outfit", 500, 21, t["fg"], track=-0.02)
        s.text(x, 88, b, "Outfit", 500, 21, t["muted"], track=-0.02)
        s.text(x, 128, c, "Outfit", 400, 12.8, t["muted"])
        s.text(x, 147, d, "Outfit", 400, 12.8, t["muted"])
    return s.render("Principles: Data first, AI second. Evidence by default. No model lock-in. You keep the keys.")


STACK = [
    ("Quant & ML", "Python · PyTorch · Qlib · Kronos · CUDA · walk-forward backtesting"),
    ("Data", "Postgres · Supabase · Drizzle · knowledge graphs · RAG pipelines"),
    ("AI", "Anthropic · OpenAI · local models · agentic workflows · evals"),
    ("Product", "TypeScript · Next.js · React · tRPC · Electron · Tailwind"),
    ("Infra", "Docker · Vercel · GitHub Actions · Linux"),
]


def stack(theme):
    rh = 44
    s = Svg(W, 28 + rh * len(STACK), theme); t = s.t
    frame(s, 16)
    for i, (k, v) in enumerate(STACK):
        y = 14 + i * rh
        if i:
            s.add(f'<path d="M26 {y}H{W-26}" stroke="{t["line"]}"/>')
        s.text(26, y + 28, k.upper(), "JBM", 400, 11, CORAL, track=0.12)
        s.text(190, y + 28.5, v, "Outfit", 400, 15, t["fg"])
    return s.render("Toolkit — " + "; ".join(f"{k}: {v}" for k, v in STACK))


def button(theme, label, primary=False):
    pad = 22
    tw = width(label, "Outfit", 500, 14.5) + width(" ↗", "JBM", 400, 13)
    s = Svg(int(tw + pad * 2 + 6), 46, theme); t = s.t
    if primary:
        s.add('<defs><linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="#FF6B3D"/>'
              '<stop offset="1" stop-color="#FFB894"/></linearGradient></defs>')
        s.add(f'<rect x="0.5" y="0.5" width="{s.w-1}" height="45" rx="10" fill="url(#bg)"/>')
        fg = "#0B0C10"
    else:
        frame(s, 10, tick=False, glow=False)
        fg = t["fg"]
    s.text(pad, 28.5, label, "Outfit", 500, 14.5, fg)
    s.text(s.w - pad, 28.5, "↗", "JBM", 400, 13, fg if primary else CORAL, anchor="end")
    return s.render(label)


def footer(theme):
    s = Svg(W, 64, theme); t = s.t
    s.add(f'<path d="M0 1H{W}" stroke="{t["line"]}"/>')
    s.add(symbol(theme, 0, 24, 22))
    s.text(32, 41, "Aion Group", "Outfit", 500, 15, t["fg"], track=-0.01)
    s.text(W, 41, "DATA FIRST, AI SECOND", "JBM", 400, 10.5, t["faint"], track=0.14, anchor="end")
    return s.render("Aion Group — Data first, AI second.")


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    files = {}
    for th in THEMES:
        files[f"hero-{th}"] = hero(th)
        files[f"s-ventures-{th}"] = section(th, "01", "Ventures", "What I'm building.")
        files[f"s-principles-{th}"] = section(th, "02", "Principles", "How I work.")
        files[f"s-stack-{th}"] = section(th, "03", "Toolkit", "What I build with.")
        files[f"s-contact-{th}"] = section(th, "04", "Contact", "Let's talk.",
                                           "Working on a financial product with a decision to optimise? Plan a call.")
        for i, v in enumerate(VENTURES, 1):
            files[f"v-0{i}-{th}"] = venture(th, v)
        files[f"principles-{th}"] = principles(th)
        files[f"stack-{th}"] = stack(th)
        files[f"btn-call-{th}"] = button(th, "Plan a call", primary=True)
        files[f"btn-site-{th}"] = button(th, "aiongp.com")
        files[f"btn-linkedin-{th}"] = button(th, "LinkedIn")
        files[f"btn-mail-{th}"] = button(th, "info@aiongp.com")
        files[f"footer-{th}"] = footer(th)
    total = 0
    for name, svg in files.items():
        (OUT / f"{name}.svg").write_text(svg)
        total += len(svg)
    print(f"{len(files)} svgs, {total/1024:.0f} KB total")
    # cache-bust: GitHub/raw caches images by URL, so stamp each src with its content hash
    import hashlib
    readme = ROOT / "README.md"
    md = readme.read_text()
    def stamp(m):
        name = m.group(1)
        h = hashlib.sha1((OUT / f"{name}.svg").read_bytes()).hexdigest()[:8]
        return f"./assets/{name}.svg?v={h}"
    readme.write_text(re.sub(r"\./assets/([\w-]+)\.svg(?:\?v=\w+)?", stamp, md))


if __name__ == "__main__":
    main()
