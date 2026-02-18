#!/usr/bin/env python3
"""Build static HTML from compliance directory markdown files."""

import markdown
import re
import shutil
from pathlib import Path

SRC = Path("/data/vault/projects/compliance-tracker/content")
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
  <a class="cta" href="https://compliancecalendar.app">Get Compliance Tracker \u2192</a>
</nav>
<div class="container">
{body}
</div>
<footer>
  <p>Church Compliance Directory \u2014 a free resource by <a href="https://compliancecalendar.app">Compliance Tracker</a></p>
  <p style="margin-top:0.4rem">Not legal or tax advice. Links point to official government agency pages. Last updated Feb 2026.</p>
</footer>
</body>
</html>"""

# (url_slug, display_name, meta_description)
STATE_PAGES = [
    ("alabama",        "Alabama",         "SOS nonprofit filings, ALDOR withholding, DOL UI for AL churches."),
    ("alaska",         "Alaska",          "CBPL biennial report, no state income tax, DOL UI for AK churches."),
    ("arizona",        "Arizona",         "ACC annual report, ADOR withholding, DES unemployment for AZ churches."),
    ("arkansas",       "Arkansas",        "SOS annual report, DFA withholding, DWS UI for AR churches."),
    ("california",     "California",      "State filings, EDD payroll, AB 506 volunteer screening for CA churches."),
    ("colorado",       "Colorado",        "SOS periodic report, DOR withholding, CDLE/FAMLI for CO churches."),
    ("connecticut",    "Connecticut",     "SOTS annual report, DCP charity registration, CT Paid Leave for CT churches."),
    ("delaware",       "Delaware",        "Division of Corporations annual report, DOR withholding for DE churches."),
    ("florida",        "Florida",         "Annual report deadline, reemployment tax for FL churches."),
    ("georgia",        "Georgia",         "Annual registration, DOL payroll, charities renewal for GA churches."),
    ("hawaii",         "Hawaii",          "DCCA annual report, TDI/PHCA obligations, DLIR UI for HI churches."),
    ("idaho",          "Idaho",           "SOS annual report, STC withholding, IDOL UI for ID churches."),
    ("illinois",       "Illinois",        "NFP annual report, DCFS Mandated Reporter training for IL churches."),
    ("indiana",        "Indiana",         "INBiz biennial report, DOR withholding, county income tax for IN churches."),
    ("iowa",           "Iowa",            "SOS biennial report, Iowa DOR withholding, IWD UI for IA churches."),
    ("kansas",         "Kansas",          "SOS annual report, KDOR withholding, DOL UI for KS churches."),
    ("kentucky",       "Kentucky",        "SOS annual report, DOR withholding, local occupational tax for KY churches."),
    ("louisiana",      "Louisiana",       "SOS annual report, LDR withholding, LWC UI for LA churches."),
    ("maine",          "Maine",           "SOS annual report, MRS withholding, DOL UI reimbursement for ME churches."),
    ("maryland",       "Maryland",        "SDAT annual report, Comptroller withholding, county payroll tax for MD churches."),
    ("massachusetts",  "Massachusetts",   "SOC/AG dual reporting, PFML obligations, DUA UI for MA churches."),
    ("michigan",       "Michigan",        "LARA annual report, UIA exemption election for MI churches."),
    ("minnesota",      "Minnesota",       "SOS annual renewal, MN Paid Leave (2026), DEED UI for MN churches."),
    ("mississippi",    "Mississippi",     "SOS annual report, MDOR withholding, MDES UI for MS churches."),
    ("missouri",       "Missouri",        "No standard annual report, registered agent maintenance for MO churches."),
    ("montana",        "Montana",         "SOS annual report (April 15), DOR withholding, DLI UI for MT churches."),
    ("nebraska",       "Nebraska",        "SOS biennial report, DOR withholding, DOL UI for NE churches."),
    ("nevada",         "Nevada",          "SilverFlume annual list, no income tax but MBT, DETR UI for NV churches."),
    ("new-hampshire",  "New Hampshire",   "SOS annual report, AG Charitable Trusts, no income tax for NH churches."),
    ("new-jersey",     "New Jersey",      "SOS annual report, four payroll obligations (withholding/UI/SDI/FLI) for NJ churches."),
    ("new-mexico",     "New Mexico",      "SOS biennial report, GRT nuance, DWS UI for NM churches."),
    ("new-york",       "New York",        "CHAR500, DOS financial disclosure, DOL unemployment for NY churches."),
    ("north-carolina", "North Carolina",  "Charitable solicitation license, UI exemption for NC churches."),
    ("north-dakota",   "North Dakota",    "SOS annual report (Aug 1), Tax Commissioner withholding for ND churches."),
    ("ohio",           "Ohio",            "5-year SOS renewal, AG annual report, ODJFS quarterly for OH churches."),
    ("oklahoma",       "Oklahoma",        "SOS annual report (July 1), Tax Commission withholding for OK churches."),
    ("oregon",         "Oregon",          "SOS annual report, DOJ charity registration, OR Paid Leave for OR churches."),
    ("pennsylvania",   "Pennsylvania",    "Annual report, Act 153 three-clearance requirement for PA churches."),
    ("rhode-island",   "Rhode Island",    "SOS annual report, AG charity registration, TDI/TCI for RI churches."),
    ("south-carolina", "South Carolina",  "SOS annual report, SCDOR withholding, DEW UI for SC churches."),
    ("south-dakota",   "South Dakota",    "SOS annual report, no state income tax, DLR UI for SD churches."),
    ("tennessee",      "Tennessee",       "SOS annual report, no income tax, DOL UI for TN churches."),
    ("texas",          "Texas",           "SOS entity maintenance, franchise tax, payroll for TX churches."),
    ("utah",           "Utah",            "DCED annual report, TAC withholding, DWS UI for UT churches."),
    ("vermont",        "Vermont",         "SOS annual report, DFR charity registration, DET UI for VT churches."),
    ("virginia",       "Virginia",        "SCC annual report, Tax Dept withholding, VEC UI for VA churches."),
    ("washington",     "Washington",      "SOS annual report, no income tax, L&I/ESD/PFML for WA churches."),
    ("west-virginia",  "West Virginia",   "SOS annual report, Tax Dept withholding, BRT UI for WV churches."),
    ("wisconsin",      "Wisconsin",       "DFI annual report, DOR withholding, AG charity registration for WI churches."),
    ("wyoming",        "Wyoming",         "SOS annual report, no state income tax, DWS UI for WY churches."),
]

md_parser = markdown.Markdown(extensions=["tables", "fenced_code"])

def render_page(title, description, body_html, out_path):
    html = HTML_TEMPLATE.format(
        title=title,
        description=description,
        css=CSS,
        body=body_html,
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path.name}")

def convert_md(src_path):
    md_parser.reset()
    text = src_path.read_text(encoding="utf-8")
    # Strip YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    return md_parser.convert(text)

# Ensure output dirs exist
(OUT / "states").mkdir(parents=True, exist_ok=True)

# Build state pages
built = 0
missing = []
for slug, state_name, description in STATE_PAGES:
    src = SRC / f"church-compliance-deadlines-{slug}-2026-draft.md"
    if not src.exists():
        print(f"  MISSING: {src.name}")
        missing.append(slug)
        continue
    body = convert_md(src)
    body = body.replace('<h2>Sources</h2>', '<div class="sources"><h2>Sources</h2>')
    body += '</div>'
    out = OUT / "states" / f"{slug}.html"
    render_page(f"Church Compliance \u2014 {state_name}", description, body, out)
    built += 1

print(f"\nBuilt {built} state pages. Missing: {missing or 'none'}")

# Build index
index_src = SRC / "church-compliance-directory-index.md"
index_body = convert_md(index_src)

state_cards = '\n<div class="state-grid">\n'
for slug, state_name, desc in STATE_PAGES:
    state_cards += f'''<div class="state-card">
  <h3>{state_name}</h3>
  <p>{desc}</p>
  <a href="states/{slug}.html">View {state_name} guide \u2192</a>
</div>\n'''
state_cards += '</div>\n'

index_body = re.sub(
    r'<table>.*?</table>',
    state_cards,
    index_body,
    count=1,
    flags=re.DOTALL
)

render_page(
    "Church Compliance Directory",
    "State-by-state compliance guides for churches \u2014 official government links, no legal advice.",
    index_body,
    OUT / "index.html"
)

(OUT.parent / "_config.yml").write_text("theme: null\n")
print("Build complete.")
