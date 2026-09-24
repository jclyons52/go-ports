#!/usr/bin/env python3
"""Render index.html (and README.md) from manifest.json.

The output is a single self-contained HTML file: no CDN, no external fonts, no
build step beyond running this script. GitHub Pages serves it directly from the
repository root.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
GITHUB = "https://github.com/jclyons52/"

CSS = """
:root {
  --bg: #0b0d10;
  --panel: #12151a;
  --panel-2: #161a21;
  --line: #232833;
  --text: #dfe3ea;
  --muted: #8b94a3;
  --accent: #4cc2ff;
  --accent-2: #7ee787;
  --warn: #ffb454;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: radial-gradient(1200px 600px at 20% -10%, #14202b 0%, var(--bg) 55%) fixed;
  color: var(--text);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 22px 96px; }
header.top { padding: 76px 0 40px; border-bottom: 1px solid var(--line); }
.eyebrow { font: 12px/1.4 var(--mono); letter-spacing: .18em; text-transform: uppercase; color: var(--muted); }
h1 { font-size: clamp(30px, 4.6vw, 50px); line-height: 1.1; margin: 14px 0 10px; letter-spacing: -0.02em; }
h1 .accent { color: var(--accent-2); }
.sub { color: var(--muted); font-size: 17px; max-width: 62ch; }
.hero {
  margin: 36px 0 0; padding: 26px 26px 22px; border: 1px solid var(--line);
  border-radius: 14px; background: linear-gradient(180deg, var(--panel-2), var(--panel));
}
.hero h2 { margin: 0 0 6px; font-size: 24px; font-family: var(--mono); }
.hero .tagline { color: var(--text); margin: 0 0 16px; max-width: 78ch; }
.hero ul { margin: 0; padding-left: 20px; color: var(--muted); }
.hero li { margin: 6px 0; }
.hero li strong { color: var(--text); font-weight: 600; }
nav.toc { display: flex; flex-wrap: wrap; gap: 10px; margin: 26px 0 0; font: 13px var(--mono); }
nav.toc a { border: 1px solid var(--line); border-radius: 999px; padding: 5px 12px; color: var(--muted); }
nav.toc a:hover { color: var(--text); border-color: #313846; text-decoration: none; }
section { margin-top: 60px; }
section > h2 { font-size: 22px; margin: 0 0 6px; font-family: var(--mono); }
section > p.blurb { color: var(--muted); margin: 0 0 22px; max-width: 80ch; }
.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); }
.card {
  border: 1px solid var(--line); border-radius: 12px; padding: 18px 18px 16px;
  background: var(--panel); display: flex; flex-direction: column;
}
.card h3 { margin: 0 0 4px; font-size: 16px; font-family: var(--mono); }
.card h3 a { color: var(--text); }
.card .pkg { font: 12px var(--mono); color: var(--warn); margin-bottom: 10px; }
.card p { margin: 0 0 12px; color: var(--muted); font-size: 14.5px; }
.card .evidence {
  margin-top: auto; font: 12.5px/1.5 var(--mono); color: var(--accent-2);
  border-top: 1px dashed var(--line); padding-top: 10px;
}
.card .evidence::before { content: "✓ "; color: var(--accent-2); }
.method ol { counter-reset: step; list-style: none; padding: 0; margin: 0; }
.method li { counter-increment: step; position: relative; padding: 0 0 16px 46px; color: var(--muted); }
.method li::before {
  content: counter(step); position: absolute; left: 0; top: 0;
  width: 28px; height: 28px; border-radius: 8px; border: 1px solid var(--line);
  background: var(--panel-2); color: var(--accent); font: 13px/28px var(--mono); text-align: center;
}
.method li strong { color: var(--text); }
footer { margin-top: 70px; padding-top: 22px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13.5px; }
footer code { font-family: var(--mono); color: var(--text); }
.stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px 26px; margin: 22px 0 0; font-family: var(--mono); font-size: 13px; color: var(--muted); }
.stat-row > div { min-width: 0; }
.stat-row b { display: block; font-size: 24px; color: var(--text); font-weight: 600; }
.snippets { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); }
.snippet { border: 1px solid var(--line); border-radius: 12px; background: var(--panel); padding: 16px 18px; min-width: 0; }
.snippet h3 { margin: 0 0 10px; font: 13px var(--mono); color: var(--warn); text-transform: lowercase; letter-spacing: .04em; }
.snippet pre { margin: 0; font: 12.5px/1.7 var(--mono); color: var(--text); overflow-x: auto; white-space: pre; }
"""


def esc(text):
    return html.escape(str(text), quote=True)


def repo_url(name):
    return f"{GITHUB}{name}"


def render_card(repo):
    return f"""      <article class="card">
        <h3><a href="{esc(repo_url(repo['repo']))}">{esc(repo['repo'])}</a></h3>
        <div class="pkg">port of {esc(repo['pkg'])}</div>
        <p>{esc(repo['desc'])}</p>
        <div class="evidence">{esc(repo['evidence'])}</div>
      </article>"""


def render_section(section):
    cards = "\n".join(render_card(r) for r in section["repos"])
    return f"""    <section id="{esc(section['id'])}">
      <h2>{esc(section['title'])}</h2>
      <p class="blurb">{esc(section['blurb'])}</p>
      <div class="grid">
{cards}
      </div>
    </section>"""


def build():
    data = json.loads((ROOT / "manifest.json").read_text())
    site = data["site"]
    hero = data["highlight"]
    sections = data["sections"]
    method = data["method"]

    all_repos = [r for s in sections for r in s["repos"]]
    repo_count = len(all_repos)
    consume = data.get("consume")
    if consume:
        snippets = "\n".join(
            f"""      <div class="snippet">
        <h3>{esc(s['label'])}</h3>
        <pre>{esc(s['code'])}</pre>
      </div>"""
            for s in consume["snippets"]
        )
        consume_html = f"""    <section id="consume">
      <h2>{esc(consume['title'])}</h2>
      <p class="blurb">{esc(consume['blurb'])}</p>
      <div class="snippets">
{snippets}
      </div>
    </section>"""
    else:
        consume_html = ""

    toc = " ".join(
        f'<a href="#{esc(s["id"])}">{esc(s["title"])}</a>' for s in sections
    )
    hero_points = "\n".join(f"          <li>{p}</li>" for p in hero["points"])
    method_steps = "\n".join(f"          <li>{s}</li>" for s in method["steps"])
    body_sections = "\n".join(render_section(s) for s in sections)

    stats = site.get("stats") or [
        {"value": str(repo_count), "label": "ports & tools"},
        {"value": "0", "label": "tolerated mismatches"},
        {"value": "npm", "label": "package as the oracle"},
    ]
    stat_row = "\n".join(
        f'        <div><b>{esc(s["value"])}</b>{esc(s["label"])}</div>' for s in stats
    )

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(site['title'])} — {esc(site['owner'])}</title>
<meta name="description" content="{esc(site['subtitle'])}">
<style>{CSS}</style>
</head>
<body>
  <div class="wrap">
    <header class="top">
      <div class="eyebrow">verification-driven ports</div>
      <h1>{esc(site['title'])}<br><span class="accent">{esc(site['subtitle'])}</span></h1>
      <p class="sub">{esc(site['intro'])}</p>
      <div class="stat-row">
{stat_row}
      </div>
      <nav class="toc">{toc} <a href="#consume">Using them</a> <a href="#method">How a port is verified</a></nav>
    </header>

    <section id="highlight" class="hero">
      <h2>{esc(hero['name'])}</h2>
      <p class="tagline">{esc(hero['tagline'])}</p>
      <ul>
{hero_points}
      </ul>
      <p style="margin:16px 0 0"><a href="{esc(repo_url(hero['repo']))}">{esc(repo_url(hero['repo']))}</a></p>
    </section>

{body_sections}

{consume_html}

    <section id="method" class="method">
      <h2>{esc(method['title'])}</h2>
      <ol>
{method_steps}
      </ol>
    </section>

    <footer>
      Every repo above is open source and carries its own oracle harness.
      The toolchain that produced them is <a href="{esc(repo_url('uplift'))}">uplift</a>.
      <br>Built with <code>build_site.py</code> from <code>manifest.json</code> — no framework, one static page.
    </footer>
  </div>
</body>
</html>
"""
    (ROOT / "index.html").write_text(page)

    readme = [
        "# Go ports of JavaScript tooling",
        "",
        site["subtitle"] + ".",
        "",
        site["intro"],
        "",
        f"Website: https://{site['owner']}.github.io/go-ports/ (built from `manifest.json` by `build_site.py`)",
        "",
    ]
    for section in sections:
        readme.append(f"## {section['title']}")
        readme.append("")
        readme.append(section["blurb"])
        readme.append("")
        for repo in section["repos"]:
            readme.append(
                f"- **[{repo['repo']}]({repo_url(repo['repo'])})** — port of `{repo['pkg']}`. "
                f"{repo['desc']} _{repo['evidence']}_"
            )
        readme.append("")
    readme.append("## How a port is verified")
    readme.append("")
    readme.extend(f"{i}. {s}" for i, s in enumerate(method["steps"], 1))
    readme.append("")
    if consume:
        readme.append(f"## {consume['title']}")
        readme.append("")
        readme.append(consume["blurb"])
        readme.append("")
        for snippet in consume["snippets"]:
            readme.append(f"**{snippet['label']}**")
            readme.append("")
            readme.append("```sh")
            readme.append(snippet["code"])
            readme.append("```")
            readme.append("")
    (ROOT / "README.md").write_text("\n".join(readme))

    print(f"wrote index.html ({len(page)} bytes), README.md, {repo_count} repos")
    return repo_count


if __name__ == "__main__":
    build()
