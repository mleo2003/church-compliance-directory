#!/usr/bin/env python3
"""Build static HTML from compliance directory markdown files."""

import markdown
import re
import shutil
from pathlib import Path

SRC = Path("/data/vault/projects/compliance-calendar/content")
OUT = Path("/tmp/cc-directory/docs")

CSS = """
:root {
  --bg: #ffffff;
  --text: #1a1a2e;
  --muted: #555;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --border: #e2e8f0;
  --callout-bg: #eff6ff;
  --callout-border: #93c5fd;
  --tag-bg: #f1f5f9;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 16px;
  line-height: 1.65;
  color: var(--text);
  background: var(--bg);
}
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); text-decoration: underline; }

/* Nav */
nav {
  background: var(--text);
  color: #fff;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  height: 52px;
  position: sticky;
  top: 0;
  z-index: 100;
}
nav .brand { font-weight: 700; font-size: 1rem; color: #fff; letter-spacing: -0.3px; }
nav .brand span { color: #60a5fa; }
nav a { color: #cbd5e1; font-size: 0.875rem; }
nav a:hover { color: #fff; text-decoration: none; }
nav .spacer { flex: 1; }
nav .cta {
  background: var(--accent);
  color: #fff !important;
  padding: 0.35rem 0.85rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
}
nav .cta:hover { background: var(--accent-hover); }

/* Layout */
.container { max-width: 860px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }

/* Disclaimer */
blockquote {
  background: var(--callout-bg);
  border-left: 4px solid var(--callout-border);
  padding: 0.85rem 1.1rem;
  border-radius: 0 6px 6px 0;
  margin: 1.5rem 0;
  font-size: 0.9rem;
  color: #1e40af;
}
blockquote p { margin: 0; }

/* Typography */
h1 { font-size: 1.75rem; font-weight: 800; margin: 1.5rem 0 0.5rem; line-height: 1.25; }
h2 { font-size: 1.2rem; font-weight: 700; margin: 2rem 0 0.75rem; padding-bottom: 0.4rem; border-bottom: 1px solid var(--border); }
h3 { font-size: 1rem; font-weight: 700; margin: 1.5rem 0 0.5rem; }
p { margin: 0.75rem 0; }
ul, ol { margin: 0.75rem 0 0.75rem 1.5rem; }
li { margin: 0.3rem 0; }
strong { font-weight: 600; }

/* Tables */
table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
th { background: var(--tag-bg); text-align: left; padding: 0.6rem 0.8rem; font-weight: 600; border: 1px solid var(--border); }
td { padding: 0.55rem 0.8rem; border: 1px solid var(--border); vertical-align: top; }
tr:nth-child(even) td { background: #fafafa; }

/* Sources */
.sources { margin-top: 2.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
.sources h2 { border-bottom: none; font-size: 1rem; color: var(--muted); }
.sources ul { font-size: 0.85rem; color: var(--muted); }
.sources li { margin: 0.4rem 0; }

/* Footer */
footer {
  margin-top: 3rem;
  padding: 1.5rem;
  text-align: center;
  font-size: 0.8rem;
  color: var(--muted);
  border-top: 1px solid var(--border);
}

/* State grid (index only) */
.state-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
.state-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.1rem;
  transition: box-shadow 0.15s;
}
.state-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.08); border-color: var(--accent); }
.state-card h3 { margin: 0 0 0.4rem; font-size: 0.95rem; }
.state-card p { font-size: 0.82rem; color: var(--muted); margin: 0 0 0.6rem; }
.state-card a { font-size: 0.82rem; font-weight: 600; }

@media (max-width: 600px) {
  .container { padding: 1.25rem 1rem 3rem; }
  h1 { font-size: 1.4rem; }
  table { font-size: 0.8rem; }
  td, th { padding: 0.4rem 0.5rem; }
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Church Compliance Directory</title>
  <meta name="description" content="{description}">
  <style>{css}</style>
</head>
<body>
<nav>
  <span class="brand">Church<span>Compliance</span>.guide</span>
  <a href="/index.html">Directory</a>
  <div class="spacer"></div>
  <a class="cta" href="https://compliancecalendar.app">Get Compliance Calendar →</a>
</nav>
<div class="container">
{body}
</div>
<footer>
  <p>Church Compliance Directory — a free resource by <a href="https://compliancecalendar.app">Compliance Calendar</a></p>
  <p style="margin-top:0.4rem">Not legal or tax advice. Links point to official government agency pages. Last updated Feb 2026.</p>
</footer>
</body>
</html>"""

STATE_PAGES = [
    ("church-compliance-deadlines-california-2026-draft.md",  "california",     "California", "State filings, EDD payroll, AB 506 volunteer screening for CA churches."),
    ("church-compliance-deadlines-texas-2026-draft.md",       "texas",          "Texas",       "SOS entity maintenance, franchise tax, payroll for TX churches."),
    ("church-compliance-deadlines-florida-2026-draft.md",     "florida",        "Florida",     "Annual report deadline, reemployment tax for FL churches."),
    ("church-compliance-deadlines-georgia-2026-draft.md",     "georgia",        "Georgia",     "Annual registration, DOL payroll, charities renewal for GA churches."),
    ("church-compliance-deadlines-ohio-2026-draft.md",        "ohio",           "Ohio",        "5-year SOS renewal, AG annual report, ODJFS quarterly for OH churches."),
    ("church-compliance-deadlines-new-york-2026-draft.md",    "new-york",       "New York",    "CHAR500, DOS financial disclosure, DOL unemployment for NY churches."),
    ("church-compliance-deadlines-north-carolina-2026-draft.md","north-carolina","North Carolina","Charitable solicitation license, UI exemption for NC churches."),
    ("church-compliance-deadlines-pennsylvania-2026-draft.md","pennsylvania",   "Pennsylvania","Annual report, Act 153 three-clearance requirement for PA churches."),
    ("church-compliance-deadlines-illinois-2026-draft.md",    "illinois",       "Illinois",    "NFP annual report, DCFS Mandated Reporter training for IL churches."),
    ("church-compliance-deadlines-michigan-2026-draft.md",    "michigan",       "Michigan",    "LARA annual report (Oct 1), UIA exemption for MI churches."),
]

md = markdown.Markdown(extensions=["tables", "fenced_code"])

def render_page(title, description, body_html, out_path):
    html = HTML_TEMPLATE.format(
        title=title,
        description=description,
        css=CSS,
        body=body_html,
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path}")

def convert_md(src_path):
    md.reset()
    text = src_path.read_text(encoding="utf-8")
    # Strip YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    return md.convert(text)

# Build state pages
for src_file, slug, state_name, description in STATE_PAGES:
    src = SRC / src_file
    if not src.exists():
        print(f"  MISSING: {src_file}")
        continue
    body = convert_md(src)
    # Wrap Sources section
    body = body.replace('<h2>Sources</h2>', '<div class="sources"><h2>Sources</h2>')
    body += '</div>'
    out = OUT / "states" / f"{slug}.html"
    render_page(f"Church Compliance — {state_name}", description, body, out)

# Build index
index_src = SRC / "church-compliance-directory-index.md"
index_body = convert_md(index_src)

# Replace the markdown table of states with a card grid
state_cards = '\n<div class="state-grid">\n'
for _, slug, state_name, desc in STATE_PAGES:
    state_cards += f'''<div class="state-card">
  <h3>{state_name}</h3>
  <p>{desc}</p>
  <a href="states/{slug}.html">View {state_name} guide →</a>
</div>\n'''
state_cards += '</div>\n'

# Replace the big markdown table with the card grid
index_body = re.sub(
    r'<table>.*?</table>',
    state_cards,
    index_body,
    count=1,
    flags=re.DOTALL
)

render_page(
    "Church Compliance Directory",
    "State-by-state compliance guides for churches — official government links, no legal advice.",
    index_body,
    OUT / "index.html"
)

# Copy a minimal _config.yml for GitHub Pages
(OUT.parent / "_config.yml").write_text("theme: null\n")
print("\nBuild complete.")
