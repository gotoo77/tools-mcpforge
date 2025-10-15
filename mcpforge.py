# MCPForge 🔨
# Générateur de serveurs MCP (Model Context Protocol) à partir de projets existants.
# Version : Démo complète (Python)

import re
import json
import tempfile
import re
from pathlib import Path
from jinja2 import Template

# ---------------------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------------------

def mkdirp(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def info(msg: str):
    print(msg)


def warn(msg: str):
    print(f"[WARN] {msg}")


# ---------------------------------------------------------------------------
# ANALYSEURS
# ---------------------------------------------------------------------------
# Ajout de la fonction générique scan_project et amélioration du scanner Express
def scan_project(project_dir: Path):
    route_re = re.compile(r'\bapp\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']', re.I)
    tools = []
    resources = []

    for path in Path(project_dir).rglob('*.*'):
        if any(excluded in str(path) for excluded in ["node_modules", ".venv", "venv", ".git", "__pycache__"]):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if path.suffix == ".js":
            for match in route_re.finditer(content):
                method, route = match.groups()
                if not route.startswith("/"):
                    continue
                safe_name = route.strip('/').replace('/', '_') or 'root'
                tools.append({
                    "name": f"{method.lower()}_{safe_name}",
                    "description": f"Route Express détectée: {method.upper()} {route} ({path.name})",
                    "inputSchema": {"type": "object", "properties": {}}
                })

        elif path.suffix in (".json", ".env", ".yaml", ".yml"):
            resources.append({
                "uri": f"file://{path.resolve()}",
                "name": path.name,
                "description": f"Ressource détectée ({path.suffix})"
            })

    return {'tools': tools, 'resources': resources}

def analyze_js_project(project: Path):
    return scan_project(project)

def analyze_py_project(project: Path):
    dec_re = re.compile(r'@(?:app|router)\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']', re.I)
    tools, resources = [], []
    for file in project.rglob('*.py'):
        try:
            text = file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for m in dec_re.finditer(text):
            method, route = m.group(1).upper(), m.group(2)
            safe_route = route.strip('/').replace('/', '_') or 'root'
            tools.append({
                'name': f"{method.lower()}_{safe_route}",
                'description': f"Route Python détectée: {method} {route} ({file.name})",
                'inputSchema': {'type': 'object', 'properties': {}}
            })
    for candidate in ['config.yaml', 'config/app.config.json', 'logs/app.log', '.env']:
        p = project / candidate
        if p.exists():
            resources.append({'uri': f'file://{p}', 'name': candidate, 'description': 'Fichier détecté'})
    return {'tools': tools, 'resources': resources}


# ---------------------------------------------------------------------------
# GÉNÉRATION MANIFEST + SERVEUR MCP
# ---------------------------------------------------------------------------

def build_manifest(name, tools, resources):
    return {
        'name': name,
        'version': '0.1.0',
        'tools': [
            {
                'name': t['name'],
                'description': t.get('description', ''),
                'inputSchema': t.get('inputSchema', {'type': 'object'})
            }
            for t in tools
        ],
        'resources': [
            {
                'uri': r['uri'],
                'name': r.get('name', r['uri']),
                'description': r.get('description', '')
            }
            for r in resources
        ],
        'prompts': []
    }


def write_server_stub(outdir: Path, name: str, tools, resources):
    mkdirp(outdir)
    code = [
        f"# Auto-généré par MCPForge\n"
        f"from fastmcp import FastMCP\n\n"
        f"mcp = FastMCP(name='{name}')\n"
    ]

    seen = {}  # Dictionnaire pour traquer les doublons

    for t in tools:
        # Nom Python valide
        base_name = re.sub(r'[^0-9a-zA-Z_]', '_', t['name'])
        # Gestion des doublons
        count = seen.get(base_name, 0) + 1
        seen[base_name] = count
        py_name = f"{base_name}_{count}" if count > 1 else base_name

        # Génération du code de tool
        code.append(
            f"\n@mcp.tool(name=\"{t['name']}\", description=\"{t.get('description','Route détectée')}\")\n"
            f"def {py_name}() -> dict:\n"
            f"    \"\"\"Tool auto-généré depuis MCPForge\"\"\"\n"
            f"    return {{'ok': True, 'called': '{t['name']}'}}\n"
        )

    code.append("\nif __name__ == '__main__':\n    mcp.run()\n")
    (outdir / 'server_stub_fastmcp.py').write_text(''.join(code), encoding='utf-8')


# ---------------------------------------------------------------------------
# RAPPORT HTML
# ---------------------------------------------------------------------------

def write_report(outdir: Path, project: Path, tools, resources):
    mkdirp(outdir / 'report')
    tpl = Template(
        """<!doctype html><html><head><meta charset='utf-8'><title>MCPForge</title>
        <meta name='viewport' content='width=device-width,initial-scale=1'>
        <style>body{font-family:system-ui,Segoe UI,Roboto,Ubuntu,sans-serif;margin:2rem} .muted{color:#666} .card{border:1px solid #ddd;border-radius:8px;padding:1rem;margin:.5rem 0} code{background:#f7f7f7;padding:2px 4px;border-radius:4px}</style>
        </head><body>
        <h1>MCPForge — Rapport</h1>
        <p class='muted'>Projet scanné : {{ project }}</p>
        <h2>🛠 Tools détectés ({{ tools|length }})</h2>
        {% if tools %}{% for t in tools %}<div class='card'><b>{{t.name}}</b><div class='muted'>{{t.description}}</div><pre><code>{{ t.inputSchema | tojson(indent=2) }}</code></pre></div>{% endfor %}{% else %}<p>Aucun tool détecté.</p>{% endif %}
        <h2>📚 Resources détectées ({{ resources|length }})</h2>
        {% if resources %}{% for r in resources %}<div class='card'><b>{{r.name}}</b><div class='muted'>{{r.description}}</div><code>{{r.uri}}</code></div>{% endfor %}{% else %}<p>Pas de resources.</p>{% endif %}
        </body></html>"""
    )
    html = tpl.render(project=str(project), tools=tools, resources=resources)
    (outdir / 'report/index.html').write_text(html, encoding='utf-8')


# ---------------------------------------------------------------------------
# TESTS (SELFTEST)
# ---------------------------------------------------------------------------

def run_selftests() -> int:
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        js = root / 'app.js'
        js.write_text("app.get('/ping',()=>{});", encoding='utf-8')
        r = analyze_js_project(root)
        assert any(t['name'] == 'get_ping' for t in r['tools'])
        ok += 1
        py = root / 'demo.py'
        py.write_text("@app.post('/foo')\ndef foo():\n return 'ok'", encoding='utf-8')
        r2 = analyze_py_project(root)
        assert any(t['name'] == 'post_foo' for t in r2['tools'])
        ok += 1
    print(f"✅ Selftests OK ({ok} suites)")
    return 0


# ---------------------------------------------------------------------------
# CLI PRINCIPALE
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scanner un projet et générer un squelette MCP.')
    parser.add_argument('project', nargs='?', help='Chemin du projet à scanner')
    parser.add_argument('--out', default='./mcp-out', help='Dossier de sortie')
    parser.add_argument('--prefer', choices=['auto', 'js', 'python'], default='auto')
    parser.add_argument('--selftest', action='store_true', help='Exécuter les tests intégrés et quitter')
    args = parser.parse_args()

    if args.selftest:
        run_selftests()
        return

    if not args.project:
        info("❌ Aucun chemin fourni. Utilisez : python mcpforge.py <chemin_du_projet> ou --selftest pour tester.")
        return

    project = Path(args.project).resolve()
    outdir = Path(args.out).resolve()
    has_js = any(p.is_file() and p.suffix in ('.js', '.ts') for p in project.rglob('*'))
    has_py = any(p.is_file() and p.suffix == '.py' for p in project.rglob('*'))
    prefer = args.prefer if args.prefer != 'auto' else ('python' if has_py and not has_js else 'js')
    res = analyze_py_project(project) if prefer == 'python' and has_py else analyze_js_project(project)
    tools, resources = res['tools'], res['resources']
    mkdirp(outdir)
    manifest = build_manifest('auto-mcp', tools, resources)
    (outdir / 'mcp-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    write_server_stub(outdir, 'auto-mcp', tools, resources)
    write_report(outdir, project, tools, resources)
    info(f'✅ Terminé. Fichiers générés dans {outdir}')


if __name__ == '__main__':
    main()
