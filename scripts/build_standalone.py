#!/usr/bin/env python3
"""Buduje jeden plik HTML: inline CSS, hero PNG (base64), fireworks-js z CDN."""
from __future__ import annotations

import re
import base64
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dysoteka.standalone.min.html"
FW_URL = "https://cdn.jsdelivr.net/npm/fireworks-js@2.10.8/dist/index.umd.js"


def minify_css(s: str) -> str:
    s = re.sub(r"/\*[\s\S]*?\*/", "", s)
    return re.sub(r"\s+", " ", s).strip()


def minify_small_script(body: str) -> str:
    body = re.sub(r"//[^\n]*", "", body)
    return re.sub(r"\s+", " ", body).strip()


def main() -> None:
    css = minify_css((ROOT / "styles.css").read_text(encoding="utf-8"))
    png = (ROOT / "assets" / "hero-mood.png").read_bytes()
    data_uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")

    with urllib.request.urlopen(FW_URL, timeout=60) as r:
        fw_js = r.read().decode("utf-8")
    fw_js = fw_js.replace("</script>", "<\\/script>")

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="styles.css" />',
        f"<style>{css}</style>",
    )
    html = html.replace('src="assets/hero-mood.png"', f'src="{data_uri}"')
    html = html.replace(
        '<script src="https://cdn.jsdelivr.net/npm/fireworks-js@2.10.8/dist/index.umd.js"></script>',
        f"<script>{fw_js}</script>",
    )

    html = re.sub(r"<!--[\s\S]*?-->", "", html)
    html = re.sub(r">\s+<", "><", html)

    parts: list[str] = []
    pos = 0
    for m in re.finditer(r"<script([^>]*)>([\s\S]*?)</script>", html):
        parts.append(html[pos : m.start()])
        attrs, body = m.group(1), m.group(2)
        if len(body) > 50000:
            parts.append(f"<script{attrs}>{body}</script>")
        else:
            parts.append(f"<script{attrs}>{minify_small_script(body)}</script>")
        pos = m.end()
    parts.append(html[pos:])
    html = "".join(parts)

    OUT.write_text(html, encoding="utf-8")
    print(f"OK {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
