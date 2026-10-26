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


def render(bests, stats):
    lines = [
        "| Test | Best WPM | Accuracy |",
        "|------|----------|----------|",
    ]
    for seconds, pb in bests.items():
        if pb:
            lines.append(f"| {seconds} seconds | {round(pb['wpm'])} | {round(pb['acc'])}% |")
        else:
            lines.append(f"| {seconds} seconds | - | - |")

    total_seconds = int(stats.get("timeTyping", 0))
    hours, minutes = total_seconds // 3600, (total_seconds % 3600) // 60
    lines.append("")
    lines.append(
        f"Tests completed: **{stats.get('completedTests', 0)}** "
        f"| Time typing: **{hours}h {minutes}m**"
    )
    return "\n".join(lines)


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
    update_readme("README.md", render(bests, stats))


if __name__ == "__main__":
    main()
