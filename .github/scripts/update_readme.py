import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.monkeytype.com"
START = "<!--MONKEYTYPE-START-->"
END = "<!--MONKEYTYPE-END-->"
SVG_FILE = "monkeytype-stats.svg"

# (title on the card, Monkeytype mode, [(mode2, label shown on the card), ...])
SECTIONS = [
    ("time", "time", [("15", "15s"), ("30", "30s"), ("60", "60s"), ("120", "120s")]),
    ("words", "words", [("10", "10"), ("25", "25"), ("50", "50"), ("100", "100")]),
    ("quote", "quote", [(None, "best")]),
]


def get(path, key, **params):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"ApeKey {key}",
            "User-Agent": "github-profile-readme-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["data"]


def flatten(data):
    # The API can return a list of results, or a dict of lists. Handle both.
    if isinstance(data, list):
        return [e for e in data if isinstance(e, dict)]
    if isinstance(data, dict):
        out = []
        for value in data.values():
            out += flatten(value)
        return out
    return []


def best_for(key, mode, mode2=None):
    params = {"mode": mode}
    if mode2:
        params["mode2"] = mode2
    try:
        data = get("/users/personalBests", key, **params)
    except urllib.error.HTTPError as err:
        if err.code in (400, 404, 422):
            print(f"No data for {mode} {mode2} (HTTP {err.code})")
            return None
        raise
    entries = flatten(data)
    if not entries:
        return None
    return max(entries, key=lambda e: e.get("wpm", 0))


def make_svg(sections, stats):
    # Green dark theme
    bg, main, sub, text = "#212830", "#41ce5c", "#788386", "#ccdae6"
    font = "'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    width, pad = 560, 25
    label_w, col_w = 70, 110
    row_h, rows_top = 78, 62
    footer_line = rows_top + row_h * len(sections) + 8
    height = footer_line + 40

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{font}">',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="12" fill="{bg}" stroke="{main}" stroke-width="2"/>',
        f'<text x="{pad}" y="40" font-size="20" font-weight="bold" fill="{main}">monkeytype</text>',
        f'<text x="{width - pad}" y="40" font-size="12" fill="{sub}" text-anchor="end">personal bests</text>',
    ]

    for r, (title, cols) in enumerate(sections):
        top = rows_top + r * row_h
        if r > 0:
            parts.append(
                f'<line x1="{pad}" y1="{top - 8}" x2="{width - pad}" y2="{top - 8}" '
                f'stroke="{sub}" stroke-opacity="0.25"/>'
            )
        parts.append(f'<text x="{pad}" y="{top + 38}" font-size="13" fill="{sub}">{title}</text>')
        for c, (label, pb) in enumerate(cols):
            cx = pad + label_w + col_w * (c + 0.5)
            wpm = str(round(pb["wpm"])) if pb else "-"
            acc = f"{round(pb['acc'])}%" if pb else "-"
            parts += [
                f'<text x="{cx:.1f}" y="{top + 12}" font-size="11" fill="{sub}" text-anchor="middle">{label}</text>',
                f'<text x="{cx:.1f}" y="{top + 42}" font-size="28" font-weight="bold" fill="{main}" text-anchor="middle">{wpm}</text>',
                f'<text x="{cx:.1f}" y="{top + 60}" font-size="12" fill="{text}" text-anchor="middle">{acc}</text>',
            ]

    total = int(stats.get("timeTyping", 0))
    hours, minutes = total // 3600, (total % 3600) // 60
    parts += [
        f'<line x1="{pad}" y1="{footer_line}" x2="{width - pad}" y2="{footer_line}" stroke="{sub}" stroke-opacity="0.4"/>',
        f'<text x="{pad}" y="{footer_line + 24}" font-size="12"><tspan fill="{sub}">tests completed </tspan>'
        f'<tspan fill="{text}">{stats.get("completedTests", 0)}</tspan></text>',
        f'<text x="{width // 2 + 20}" y="{footer_line + 24}" font-size="12"><tspan fill="{sub}">time typing </tspan>'
        f'<tspan fill="{text}">{hours}h {minutes}m</tspan></text>',
        "</svg>",
    ]
    return "\n".join(parts)


def update_readme(path, block):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        sys.exit("README.md is missing the MONKEYTYPE-START / MONKEYTYPE-END markers")
    new_text = pattern.sub(f"{START}\n{block}\n{END}", text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)


def main():
    key = os.environ["MT_APE_KEY"]

    sections = []
    for title, mode, items in SECTIONS:
        cols = []
        for mode2, label in items:
            cols.append((label, best_for(key, mode, mode2)))
            time.sleep(0.5)
        sections.append((title, cols))

    stats = get("/users/stats", key)

    with open(SVG_FILE, "w", encoding="utf-8") as f:
        f.write(make_svg(sections, stats))

    # ?v=... makes GitHub load the newest image instead of an old saved copy
    block = f'<p align="center"><img src="{SVG_FILE}?v={int(time.time())}" alt="Monkeytype stats" /></p>'
    update_readme("README.md", block)


if __name__ == "__main__":
    main()
