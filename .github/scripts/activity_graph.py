"""Gera activity-graph.svg: contribuições dos últimos 30 dias, em roxo (tema escuro).

Lê o calendário de contribuições pela API GraphQL do GitHub (GITHUB_TOKEN) e desenha uma linha com
área, pontos e eixos. Sem serviço de terceiros: roda na Action do próprio repositório.
"""
import json
import os
import urllib.request
from datetime import date, timedelta

USER = os.environ.get("USERNAME", "ThiagoRodrigues11")
TOKEN = os.environ["GITHUB_TOKEN"]
DAYS = 30
OUT = os.environ.get("OUT", "activity-graph.svg")

end = date.today()
start = end - timedelta(days=DAYS - 1)
query = """query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) { contributionsCollection(from: $from, to: $to) {
    contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"""
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {
        "login": USER, "from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"}}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
data = json.load(urllib.request.urlopen(req, timeout=30))
days = {d["date"]: d["contributionCount"]
        for w in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for d in w["contributionDays"]}
series = [(start + timedelta(days=i), days.get(str(start + timedelta(days=i)), 0)) for i in range(DAYS)]

W, H = 840, 300
L, R, T, B = 52, 24, 58, 46
pw, ph = W - L - R, H - T - B
top = max(4, max(c for _, c in series))
step = max(1, -(-top // 4))
top = step * 4
x = lambda i: L + pw * i / (DAYS - 1)
y = lambda c: T + ph * (1 - c / top)
pts = [(x(i), y(c)) for i, (_, c) in enumerate(series)]
line = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
area = f"M{L},{T + ph} L" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + f" L{L + pw},{T + ph} Z"
total = sum(c for _, c in series)

grid, labels = [], []
for k in range(5):
    v = step * k
    gy = y(v)
    grid.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{L + pw}" y2="{gy:.1f}" class="grid"/>')
    labels.append(f'<text x="{L - 10}" y="{gy + 4:.1f}" class="axis" text-anchor="end">{v}</text>')
for i in range(0, DAYS, 5):
    d = series[i][0]
    labels.append(f'<text x="{x(i):.1f}" y="{T + ph + 22}" class="axis" text-anchor="middle">{d.day:02d}/{d.month:02d}</text>')
dots = "".join(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" class="pt"><title>{d.day:02d}/{d.month:02d}: {c}</title></circle>'
               for (px, py), (d, c) in zip(pts, series))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribuições nos últimos {DAYS} dias: {total}">
<style>
 .bg{{fill:#0d1117}} .title{{font:600 17px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#e9d5ff}}
 .sub{{font:400 12px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#a78bfa}}
 .axis{{font:400 11px 'Segoe UI',Ubuntu,Arial,sans-serif;fill:#8b7aa8}} .grid{{stroke:#2e1065;stroke-width:1}}
 .line{{fill:none;stroke:#a855f7;stroke-width:2.5;stroke-linejoin:round;stroke-linecap:round;stroke-dasharray:2400;stroke-dashoffset:2400;animation:draw 2.2s ease-out forwards}}
 .area{{fill:url(#g);opacity:0;animation:fade 1.2s .8s ease-out forwards}}
 .pt{{fill:#f3e8ff;stroke:#7c3aed;stroke-width:1.5;opacity:0;animation:fade .6s 1.8s ease-out forwards}}
 @keyframes draw{{to{{stroke-dashoffset:0}}}} @keyframes fade{{to{{opacity:1}}}}
 @media (prefers-reduced-motion:reduce){{.line{{animation:none;stroke-dashoffset:0}} .area,.pt{{animation:none;opacity:1}}}}
</style>
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7c3aed" stop-opacity=".55"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></linearGradient></defs>
<rect width="{W}" height="{H}" rx="12" class="bg"/>
<text x="{L}" y="30" class="title">Atividade nos últimos {DAYS} dias</text>
<text x="{L}" y="47" class="sub">{total} contribuições · {series[0][0].day:02d}/{series[0][0].month:02d} a {series[-1][0].day:02d}/{series[-1][0].month:02d}</text>
{"".join(grid)}
<path d="{area}" class="area"/>
<polyline points="{line}" class="line"/>
{dots}
{"".join(labels)}
</svg>'''
open(OUT, "w", encoding="utf-8").write(svg)
print(f"{OUT}: {total} contribuições em {DAYS} dias")
