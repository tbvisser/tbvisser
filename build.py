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


def frame(svg, r=16, fill=None):
    t = svg.t
    svg.add(f'<rect x="0.5" y="0.5" width="{svg.w-1}" height="{svg.h-1}" rx="{r}" '
            f'fill="{fill or t["card"]}" stroke="{t["line"]}"/>')


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


def hero(theme):
    s = Svg(W, 340, theme); t = s.t
    s.add(f'<defs><clipPath id="c"><rect x="0.5" y="0.5" width="{W-1}" height="339" rx="18"/></clipPath>'
          f'<pattern id="d" width="22" height="22" patternUnits="userSpaceOnUse">'
          f'<circle cx="1" cy="1" r="1" fill="{t["grid"]}"/></pattern>'
          f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{t["bg"]}"/>'
          f'<stop offset=".55" stop-color="{t["bg"]}" stop-opacity="0"/></linearGradient></defs>')
    s.add(f'<rect x="0.5" y="0.5" width="{W-1}" height="339" rx="18" fill="{t["bg"]}" stroke="{t["line"]}"/>')
    s.add('<g clip-path="url(#c)">')
    s.add(f'<rect width="{W}" height="340" fill="url(#d)"/>')
    # construction lines behind the mark (brand board motif)
    for x in (560, 700, 840):
        s.add(f'<path d="M{x} 0V340" stroke="{t["grid"]}"/>')
    for y in (90, 250):
        s.add(f'<path d="M520 {y}H{W}" stroke="{t["grid"]}"/>')
    s.add(f'<circle cx="700" cy="170" r="150" fill="none" stroke="{t["grid"]}"/>')
    s.add(f'<g class="mark">{symbol(theme, 548, 26, 300)}</g>')
    s.add(f'<rect width="{W}" height="340" fill="url(#fade)"/>')
    s.add('</g>')
    crosshairs(s)
    # copy
    s.add(f'<circle class="pulse" cx="52" cy="70" r="4" fill="{CORAL}"/>')
    s.text(64, 74, "FOUNDER — AION GROUP", "JBM", 400, 11.5, t["muted"], track=0.14)
    s.text(46, 150, "Thomas Visser", "Outfit", 500, 58, t["fg"], track=-0.025)
    s.text(46, 200, "Knowledge that compounds", "Outfit", 300, 34, t["muted"], track=-0.02,
           extra='')
    tw = width("Knowledge that compounds", "Outfit", 300, 34, -0.02)
    s.text(46 + tw + 1, 200, ".", "Outfit", 500, 34, CORAL)
    s.add(f'<path d="M48 236H112" stroke="{CORAL}" stroke-width="2"/>')
    s.text(46, 270, "Quant models, data architecture & applied AI —", "Outfit", 400, 15.5, t["muted"])
    s.text(46, 292, "measured against a baseline, built to keep.", "Outfit", 400, 15.5, t["muted"])
    s.text(W - 46, 304, "NETHERLANDS", "JBM", 400, 10.5, t["faint"], track=0.14, anchor="end")
    css = ("@keyframes p{0%,100%{opacity:1}50%{opacity:.25}}.pulse{animation:p 2.4s ease-in-out infinite}"
           "@keyframes r{from{opacity:0;transform:translateX(14px)}to{opacity:1;transform:none}}"
           ".mark{animation:r 1.1s cubic-bezier(.2,.7,.2,1) both}")
    return s.render("Thomas Visser — Founder, Aion Group. Knowledge that compounds.", css)


def section(theme, num, label, title, sub=None):
    s = Svg(W, 92 if sub else 70, theme); t = s.t
    s.kicker(2, 22, num, label)
    s.text(0, 58, title, "Outfit", 500, 28, t["fg"], track=-0.02)
    if sub:
        s.text(0, 84, sub, "Outfit", 400, 14.5, t["muted"])
    return s.render(f"{num} — {label}: {title}")


VENTURES = [
    ("01", "Aion Group", "Founder", "Algorithms & quant optimisation", "for financial products.", "aiongp.com", True),
    ("02", "Verticallm", "Venture", "Supply chain strategy,", "delivered by AI.", "verticallm.ai", False),
    ("03", "tradeflow.so", "Venture", "Trading dashboard", "& trade replay.", "tradeflow.so", False),
    ("04", "Locally", "Venture", "Local-first AI for", "one-person businesses.", "locallyai.nl", False),
]


def venture(theme, v):
    num, name, role, l1, l2, url, lead = v
    s = Svg(432, 188, theme); t = s.t
    frame(s, 14)
    if lead:
        s.add(f'<path d="M26 1.5H86" stroke="{CORAL}" stroke-width="3"/>')
    s.text(26, 38, num, "JBM", 400, 11.5, CORAL, track=0.1)
    s.text(406, 38, role.upper(), "JBM", 400, 10.5, t["faint"], track=0.14, anchor="end")
    s.text(26, 84, name, "Outfit", 500, 27, t["fg"], track=-0.02)
    s.text(26, 116, l1, "Outfit", 400, 15, t["muted"])
    s.text(26, 137, l2, "Outfit", 400, 15, t["muted"])
    s.add(f'<path d="M26 156H406" stroke="{t["line"]}"/>')
    s.text(26, 175, url, "JBM", 400, 11.5, t["muted"], track=0.04)
    s.text(406, 175, "↗", "JBM", 400, 13, CORAL, anchor="end")
    return s.render(f"{name} — {l1} {l2} {url}")


PRINCIPLES = [
    ("Data first,", "AI second.", "Models are only as strong", "as the data beneath them."),
    ("Evidence", "by default.", "Every model has to beat an", "honest baseline, out of sample."),
    ("No model", "lock-in.", "Swap providers and models", "without rebuilding the stack."),
    ("You keep", "the keys.", "Code, data and models are", "handed over — yours to own."),
]


def principles(theme):
    s = Svg(W, 214, theme); t = s.t
    frame(s, 16)
    cw = W / 4
    for i, (a, b, c, d) in enumerate(PRINCIPLES):
        x = i * cw + 26
        if i:
            s.add(f'<path d="M{i*cw} 26V188" stroke="{t["line"]}"/>')
        s.text(x, 46, f"0{i+1}", "JBM", 400, 11.5, CORAL, track=0.1)
        s.text(x, 90, a, "Outfit", 500, 21, t["fg"], track=-0.02)
        s.text(x, 116, b, "Outfit", 500, 21, t["muted"], track=-0.02)
        s.text(x, 156, c, "Outfit", 400, 12.8, t["muted"])
        s.text(x, 175, d, "Outfit", 400, 12.8, t["muted"])
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
        s.add(f'<rect x="0.5" y="0.5" width="{s.w-1}" height="45" rx="23" fill="{CORAL}"/>')
        fg = "#0B0C10"
    else:
        s.add(f'<rect x="0.5" y="0.5" width="{s.w-1}" height="45" rx="23" fill="{t["card"]}" stroke="{t["line"]}"/>')
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
        for v in VENTURES:
            files[f"v-{v[0]}-{th}"] = venture(th, v)
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


if __name__ == "__main__":
    main()
