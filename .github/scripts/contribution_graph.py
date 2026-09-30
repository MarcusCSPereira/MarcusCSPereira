"""Render the GitHub contribution calendar as SVG, using GitHub's own palette.

Writes dist/contributions-dark.svg and dist/contributions-light.svg.
Requires GITHUB_TOKEN and GITHUB_USER in the environment.
"""
import datetime
import json
import os
import urllib.request

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""

THEMES = {
    "dark": {
        "text": "#9198a1",
        "title": "#f0f6fc",
        "levels": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
        "stroke": "rgba(255,255,255,0.05)",
    },
    "light": {
        "text": "#59636e",
        "title": "#1f2328",
        "levels": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
        "stroke": "rgba(31,35,40,0.05)",
    },
}

LEVEL_INDEX = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}

CELL, GAP = 10, 3
STEP = CELL + GAP
LEFT, TOP = 32, 44
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"


def fetch_calendar(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(calendar, theme):
    t = THEMES[theme]
    weeks = calendar["weeks"]
    width = LEFT + len(weeks) * STEP + 10
    height = TOP + 7 * STEP + 34
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">',
        f'<text x="{LEFT}" y="16" font-size="14" fill="{t["title"]}">'
        f'{calendar["totalContributions"]} contributions in the last year</text>',
    ]

    last_month = None
    for i, week in enumerate(weeks):
        first = datetime.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and first.day <= 7 and i < len(weeks) - 2:
            out.append(
                f'<text x="{LEFT + i * STEP}" y="{TOP - 8}" font-size="10" '
                f'fill="{t["text"]}">{first.strftime("%b")}</text>'
            )
        last_month = first.month

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text x="0" y="{TOP + row * STEP + CELL - 1}" font-size="10" '
            f'fill="{t["text"]}">{label}</text>'
        )

    for i, week in enumerate(weeks):
        for day in week["contributionDays"]:
            weekday = (datetime.date.fromisoformat(day["date"]).weekday() + 1) % 7
            color = t["levels"][LEVEL_INDEX[day["contributionLevel"]]]
            out.append(
                f'<rect x="{LEFT + i * STEP}" y="{TOP + weekday * STEP}" width="{CELL}" '
                f'height="{CELL}" rx="2" fill="{color}" stroke="{t["stroke"]}">'
                f'<title>{day["contributionCount"]} contributions on {day["date"]}</title></rect>'
            )

    legend_y = TOP + 7 * STEP + 12
    legend_x = width - 10 - 5 * STEP - 30
    out.append(
        f'<text x="{legend_x - 30}" y="{legend_y + CELL - 1}" font-size="10" '
        f'fill="{t["text"]}">Less</text>'
    )
    for n, color in enumerate(t["levels"]):
        out.append(
            f'<rect x="{legend_x + n * STEP}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}" stroke="{t["stroke"]}"/>'
        )
    out.append(
        f'<text x="{legend_x + 5 * STEP + 4}" y="{legend_y + CELL - 1}" font-size="10" '
        f'fill="{t["text"]}">More</text>'
    )
    out.append("</svg>")
    return "\n".join(out)


def main():
    calendar = fetch_calendar(os.environ["GITHUB_USER"], os.environ["GITHUB_TOKEN"])
    os.makedirs("dist", exist_ok=True)
    for theme in THEMES:
        with open(f"dist/contributions-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(render(calendar, theme))


if __name__ == "__main__":
    main()
