"""Generates assets/header.svg — animated particle network banner (pure SVG/CSS, works in GitHub READMEs)."""
import math
import random

random.seed(42)
W, H = 1200, 340
N = 70
LINK = 150

parts = []
for i in range(N):
    x, y = random.uniform(0, W), random.uniform(0, H)
    ang = random.uniform(0, 2 * math.pi)
    amp = random.uniform(15, 45)
    dx, dy = amp * math.cos(ang), amp * math.sin(ang)
    dur = random.uniform(7, 16)
    r = random.choice([1.2, 1.6, 2.0, 2.6])
    col = random.choice(["#22d3ee", "#a78bfa", "#38bdf8", "#e879f9", "#ffffff"])
    parts.append((x, y, dx, dy, dur, r, col))

out = []
out.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#05060f"/><stop offset="55%" stop-color="#0b1026"/><stop offset="100%" stop-color="#140a2b"/>
  </linearGradient>
  <radialGradient id="glow1" cx="20%" cy="30%" r="45%"><stop offset="0%" stop-color="#22d3ee" stop-opacity=".22"/><stop offset="100%" stop-color="#22d3ee" stop-opacity="0"/></radialGradient>
  <radialGradient id="glow2" cx="85%" cy="75%" r="50%"><stop offset="0%" stop-color="#a855f7" stop-opacity=".25"/><stop offset="100%" stop-color="#a855f7" stop-opacity="0"/></radialGradient>
  <linearGradient id="txt" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#22d3ee"/><stop offset="50%" stop-color="#ffffff"/><stop offset="100%" stop-color="#c084fc"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0;-1 0" dur="8s" repeatCount="indefinite"/>
  </linearGradient>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#ffffff" stroke-opacity=".035"/></pattern>
  <filter id="blur"><feGaussianBlur stdDeviation="1.2"/></filter>
  <clipPath id="clip"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<style>
  .p {{ animation-timing-function: ease-in-out; animation-iteration-count: infinite; animation-direction: alternate; }}
  .tw {{ animation: tw 3s ease-in-out infinite alternate; }}
  @keyframes tw {{ from {{ opacity: .25 }} to {{ opacity: 1 }} }}
  .ln {{ animation: ln 6s ease-in-out infinite alternate; }}
  @keyframes ln {{ from {{ stroke-opacity: .02 }} to {{ stroke-opacity: .28 }} }}
  .scan {{ animation: scan 6s linear infinite; }}
  @keyframes scan {{ from {{ transform: translateY(-40px) }} to {{ transform: translateY({H + 40}px) }} }}
  .sub {{ animation: fade 1.2s ease-out .6s both; }}
  .name {{ animation: fade 1.2s ease-out both; }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateY(10px) }} to {{ opacity: 1; transform: none }} }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0 }} }}
''')
for i, (x, y, dx, dy, dur, r, col) in enumerate(parts):
    out.append(f"  @keyframes m{i} {{ from {{ transform: translate(0,0) }} to {{ transform: translate({dx:.1f}px,{dy:.1f}px) }} }}\n")
out.append("</style>\n<g clip-path=\"url(#clip)\">\n")
out.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>'
           f'<rect width="{W}" height="{H}" fill="url(#glow1)"/><rect width="{W}" height="{H}" fill="url(#glow2)"/>\n')

# connection lines between nearby particles (fade in/out)
out.append('<g stroke="#67e8f9" stroke-width=".8">\n')
for i in range(N):
    for j in range(i + 1, N):
        a, b = parts[i], parts[j]
        d = math.hypot(a[0] - b[0], a[1] - b[1])
        if d < LINK:
            delay = random.uniform(0, 6)
            out.append(f'<line class="ln" style="animation-delay:-{delay:.1f}s" x1="{a[0]:.0f}" y1="{a[1]:.0f}" x2="{b[0]:.0f}" y2="{b[1]:.0f}"/>\n')
out.append("</g>\n")

# particles
for i, (x, y, dx, dy, dur, r, col) in enumerate(parts):
    delay = random.uniform(0, 3)
    out.append(f'<g class="p" style="animation-name:m{i};animation-duration:{dur:.1f}s">'
               f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r*2.6:.1f}" fill="{col}" opacity=".18" filter="url(#blur)"/>'
               f'<circle class="tw" style="animation-delay:-{delay:.1f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"/></g>\n')

# scanline
out.append(f'<rect class="scan" x="0" y="0" width="{W}" height="2" fill="#22d3ee" opacity=".12"/>\n')

# text block
out.append(f'''<g font-family="'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif" text-anchor="middle">
  <text class="name" x="{W/2}" y="160" font-size="72" font-weight="800" letter-spacing="2" fill="url(#txt)">Thomas Visser</text>
  <text class="sub" x="{W/2}" y="210" font-size="22" fill="#cbd5e1" font-family="'Cascadia Code', 'Fira Code', Consolas, monospace">
    &gt; Data architecture · AI systems · Trading infrastructure<tspan class="cur" fill="#22d3ee">_</tspan>
  </text>
  <text class="sub" x="{W/2}" y="258" font-size="15" fill="#94a3b8" letter-spacing="4" font-family="'Cascadia Code', Consolas, monospace">AION PARTNERS  ◆  VERTICALLM  ◆  TRADEFLOW.SO  ◆  LOCALLY.AI</text>
</g>
''')
out.append(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#22d3ee" stroke-opacity=".25"/>\n')
out.append("</g>\n</svg>\n")

with open("assets/header.svg", "w", encoding="utf-8") as f:
    f.write("".join(out))
print("lines/particles written")
