import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://api.monkeytype.com"
START = "<!--MONKEYTYPE-START-->"
END = "<!--MONKEYTYPE-END-->"
TIME_MODES = ["15", "30", "60", "120"]
SVG_FILE = "monkeytype-stats.svg"


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


def best_for(key, seconds):
    entries = get("/users/personalBests", key, mode="time", mode2=seconds)
    if not entries:
        return None
    return max(entries, key=lambda e: e.get("wpm", 0))


def make_svg(bests, stats):
    # Monkeytype "serika dark" colors
    bg, main, sub, text = "#323437", "#e2b714", "#646669", "#d1d0c5"
    font = "'Roboto Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    width, height, pad = 495, 215, 25
    col_w = (width - 2 * pad) / len(bests)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{font}">',
        f'<rect width="{width}" height="{height}" rx="12" fill="{bg}"/>',
        f'<text x="{pad}" y="40" font-size="20" font-weight="bold" fill="{main}">monkeytype</text>',
        f'<text x="{width - pad}" y="40" font-size="12" fill="{sub}" text-anchor="end">personal bests</text>',
    ]

    for i, (seconds, pb) in enumerate(bests.items()):
        cx = pad + col_w * (i + 0.5)
        wpm = str(round(pb["wpm"])) if pb else "-"
        acc = f"{round(pb['acc'])}%" if pb else "-"
        parts += [
            f'<text x="{cx:.1f}" y="82" font-size="13" fill="{sub}" text-anchor="middle">{seconds}s</text>',
            f'<text x="{cx:.1f}" y="120" font-size="34" font-weight="bold" fill="{main}" text-anchor="middle">{wpm}</text>',
            f'<text x="{cx:.1f}" y="138" font-size="11" fill="{sub}" text-anchor="middle">wpm</text>',
            f'<text x="{cx:.1f}" y="160" font-size="15" fill="{text}" text-anchor="middle">{acc}</text>',
        ]

    total = int(stats.get("timeTyping", 0))
    hours, minutes = total // 3600, (total % 3600) // 60
    parts += [
        f'<line x1="{pad}" y1="176" x2="{width - pad}" y2="176" stroke="{sub}" stroke-opacity="0.4"/>',
        f'<text x="{pad}" y="198" font-size="12"><tspan fill="{sub}">tests completed </tspan>'
        f'<tspan fill="{text}">{stats.get("completedTests", 0)}</tspan></text>',
        f'<text x="{width // 2 + 20}" y="198" font-size="12"><tspan fill="{sub}">time typing </tspan>'
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
    bests = {s: best_for(key, s) for s in TIME_MODES}
    stats = get("/users/stats", key)

    with open(SVG_FILE, "w", encoding="utf-8") as f:
        f.write(make_svg(bests, stats))

    block = f'<p align="center"><img src="{SVG_FILE}" alt="Monkeytype stats" /></p>'
    update_readme("README.md", block)


if __name__ == "__main__":
    main()
