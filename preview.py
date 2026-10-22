import os, pathlib
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).parent
body = pathlib.Path(os.environ["TMPDIR"], "r.html").read_text() if pathlib.Path(os.environ["TMPDIR"], "r.html").exists() else pathlib.Path("/tmp/r.html").read_text()
for scheme, bg in (("dark", "#0d1117"), ("light", "#ffffff")):
    page_html = f"""<html><head><base href="file://{root}/"><style>body{{background:{bg};margin:0;padding:32px;font-family:-apple-system}}
    .md{{width:838px;margin:auto;border:1px solid {'#30363d' if scheme=='dark' else '#d0d7de'};border-radius:6px;padding:24px}} img{{max-width:100%}} p{{margin:0 0 8px}}</style></head>
    <body><div class=md>{body}</div></body></html>"""
    f = root / f".preview-{scheme}.html"; f.write_text(page_html)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 920, "height": 900}, color_scheme=scheme, device_scale_factor=1.5)
        pg.goto(f.as_uri()); pg.wait_for_timeout(1800)
        pg.screenshot(path=str(os.environ["TMPDIR"] + f"/profile-{scheme}.png"), full_page=True); b.close()
    f.unlink()
print("done")
