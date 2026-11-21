#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markdown-it-py>=4.3.0",
#     "pyyaml>=6.0.4",
#     "skills-ref>=0.1.1",
# ]
# ///
"""Turn a tree of API docs into a tree of agent skills.

Pipeline. Every step reads and writes files in the --out workspace, so you can
stop, inspect or hand-edit between steps:

  map ROOT.md   crawl the docs        -> taxonomy.json, taxonomy.md (mermaid)
  plan          agent groups docs     -> plan.json, plan.md (mermaid)
  generate      agent writes nodes    -> <skill-name>/**/SKILL.md
  check DIR     validate a skill tree (skills-ref + links)
  package DIR   zip a skill into an installer (DIR.zip)
  install SRC   install a skill (directory or .zip) into a skills directory
  build ROOT.md map + plan + generate + check (+ install with --install)

Agent steps shell out to any CLI agent that reads a prompt on stdin and prints
its answer on stdout: `claude -p` by default, or --agent / $SKILLTREE_AGENT.
The agent instructions are references/planning.md and references/writing.md,
so the CLI and an agent doing the steps by hand follow the same rules.
"""

import argparse
import itertools
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from skills_ref import validate

REFS = Path(__file__).resolve().parent.parent / "references"
DEFAULT_AGENT = os.environ.get("SKILLTREE_AGENT", "claude -p")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_LINES = 500  # Agent Skills guidance for a SKILL.md body

# Indented code blocks are off so content nested in mkdocs tabs
# (`=== "Python"` + 4-space indent) is still parsed as markdown.
MD = MarkdownIt("commonmark").disable("code")


class Error(Exception):
    """A user-facing failure: printed without a traceback."""


# --------------------------------------------------------------------------
# Markdown helpers
# --------------------------------------------------------------------------

def parse_md(text: str) -> tuple[list[str], list[str]]:
    """Return the h1-h3 headings and the link targets of a markdown text."""
    tokens = MD.parse(text)
    headings, links = [], []
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag in ("h1", "h2", "h3"):
            headings.append("#" * int(tok.tag[1]) + " " + tokens[i + 1].content)
        links += [c.attrs["href"] for c in tok.children or [] if c.type == "link_open"]
    return headings, links


def is_local(href: str) -> bool:
    return "://" not in href and not href.startswith(("mailto:", "#"))


def mermaid(tree: dict, label) -> str:
    """Render a {..., "children": [...]} tree as a mermaid flowchart."""
    ids = itertools.count()
    lines = ["```mermaid", "graph LR"]

    def walk(node, parent=None):
        nid = f"n{next(ids)}"
        text = label(node).replace('"', "#quot;")
        lines.append(f'  {nid}["{text}"]')
        if parent:
            lines.append(f"  {parent} --> {nid}")
        for child in node.get("children", []):
            walk(child, nid)

    walk(tree)
    return "\n".join(lines + ["```"])


# --------------------------------------------------------------------------
# map: crawl docs into a taxonomy tree
# --------------------------------------------------------------------------

class _MkdocsLoader(yaml.SafeLoader):
    """SafeLoader that tolerates mkdocs tags such as !ENV."""


_MkdocsLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def doc_node(docs_dir: Path, rel: str, title: str | None = None) -> dict:
    text = (docs_dir / rel).read_text(encoding="utf-8")
    headings, links = parse_md(text)
    h1 = next((h[2:] for h in headings if h.startswith("# ")), Path(rel).stem)
    return {"title": title or h1, "path": rel, "lines": len(text.splitlines()),
            "headings": headings, "links": links, "children": []}


def nav_nodes(items: list, docs_dir: Path, skip: str) -> list[dict]:
    """Turn a mkdocs `nav:` list into taxonomy nodes (sections have path None)."""
    nodes = []
    for item in items:
        title, value = next(iter(item.items())) if isinstance(item, dict) else (None, item)
        if isinstance(value, list):
            nodes.append({"title": title, "path": None,
                          "children": nav_nodes(value, docs_dir, skip)})
        elif value != skip and is_local(value):
            node = doc_node(docs_dir, value, title)
            del node["links"]
            nodes.append(node)
    return nodes


def crawl_links(docs_dir: Path, root_rel: str) -> dict:
    """Breadth-first walk of local .md links; a doc's parent is where it was first linked."""
    tree = doc_node(docs_dir, root_rel)
    queue, seen = [tree], {root_rel}
    while queue:
        node = queue.pop(0)
        for href in node.pop("links"):
            target = (docs_dir / node["path"]).parent / href.split("#")[0]
            if not is_local(href) or target.suffix != ".md" or not target.is_file():
                continue
            rel = os.path.relpath(target, docs_dir)
            if rel.startswith("..") or rel in seen:
                continue
            seen.add(rel)
            child = doc_node(docs_dir, rel)
            node["children"].append(child)
            queue.append(child)
    return tree


def find_mkdocs(root: Path) -> Path | None:
    for d in root.parents:
        for name in ("mkdocs.yml", "mkdocs.yaml"):
            if (d / name).is_file():
                return d / name
    return None


def build_taxonomy(root: Path) -> dict:
    """Prefer the mkdocs nav (the authors' own hierarchy); fall back to links."""
    if not root.is_file():
        raise Error(f"root doc not found: {root}")
    cfg = find_mkdocs(root)
    if cfg:
        conf = yaml.load(cfg.read_text(encoding="utf-8"), Loader=_MkdocsLoader) or {}
        docs_dir = (cfg.parent / conf.get("docs_dir", "docs")).resolve()
        if conf.get("nav") and docs_dir in root.parents:
            rel = root.relative_to(docs_dir).as_posix()
            tree = doc_node(docs_dir, rel)
            del tree["links"]
            tree["children"] = nav_nodes(conf["nav"], docs_dir, skip=rel)
            return {"docs_dir": docs_dir, "source": f"mkdocs nav ({cfg.name})", "tree": tree}
    docs_dir = root.parent
    return {"docs_dir": docs_dir, "source": "markdown links",
            "tree": crawl_links(docs_dir, root.name)}


def cmd_map(args) -> dict:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    taxonomy = build_taxonomy(Path(args.root).resolve())
    # Stored relative to the workspace so it can be moved or committed.
    taxonomy["docs_dir"] = os.path.relpath(taxonomy["docs_dir"], out.resolve())
    (out / "taxonomy.json").write_text(json.dumps(taxonomy, indent=2) + "\n")
    diagram = mermaid(taxonomy["tree"], lambda n: n["title"] + (
        f"<br/><small>{n['path']} · {n['lines']} lines</small>" if n["path"] else ""))
    (out / "taxonomy.md").write_text(
        f"# Docs taxonomy\n\nSource: {taxonomy['source']}\n\n{diagram}\n")
    return {"taxonomy": str(out / "taxonomy.json"), "diagram": str(out / "taxonomy.md")}


# --------------------------------------------------------------------------
# Agent plumbing
# --------------------------------------------------------------------------

def ask(agent: str, prompt: str) -> str:
    """Send a prompt to a CLI agent on stdin; return its stdout."""
    try:
        result = subprocess.run(shlex.split(agent), input=prompt,
                                capture_output=True, text=True)
    except FileNotFoundError:
        raise Error(f"agent command not found: {agent!r} (set --agent)")
    if result.returncode:
        raise Error(f"agent exited {result.returncode}: {result.stderr.strip()[-800:]}")
    return result.stdout.strip()


def unfence(text: str) -> str:
    """Drop a code fence wrapping the whole answer, which agents sometimes add."""
    m = re.fullmatch(r"```[\w-]*\n(.*)\n```", text.strip(), re.DOTALL)
    return m.group(1) if m else text


def walk(node: dict, parent: Path = Path(), ancestors: tuple = ()):
    """Yield (node, dir relative to the workspace, ancestor nodes) depth-first."""
    here = parent / node["name"]
    yield node, here, ancestors
    for child in node.get("children", []):
        yield from walk(child, here, ancestors + (node,))


# --------------------------------------------------------------------------
# plan: agent groups docs into a skill tree
# --------------------------------------------------------------------------

def load_plan(out: Path) -> dict:
    """Read plan.json, resolving docs_dir (stored relative to the workspace)."""
    plan_file = out / "plan.json"
    if not plan_file.is_file():
        raise Error(f"{plan_file} not found: run `plan` first")
    plan = json.loads(plan_file.read_text())
    plan["docs_dir"] = str((out / plan["docs_dir"]).resolve())
    return plan


def plan_problems(plan: dict) -> list[str]:
    docs_dir = Path(plan["docs_dir"])
    problems = []
    for node, here, _ in walk(plan["skill"]):
        name = node.get("name", "")
        if not NAME_RE.match(name) or len(name) > 64:
            problems.append(f"{here}: bad name {name!r} (lowercase-hyphen, max 64)")
        if not 0 < len(node.get("description", "")) <= 1024:
            problems.append(f"{here}: description must be 1-1024 characters")
        names = [c.get("name") for c in node.get("children", [])]
        problems += [f"{here}: duplicate child {n!r}" for n in set(names) if names.count(n) > 1]
        problems += [f"{here}: source not found: {s}" for s in node.get("sources", [])
                     if not (docs_dir / s).is_file()]
    return problems


def cmd_plan(args) -> dict:
    out = Path(args.out)
    taxonomy_file = out / "taxonomy.json"
    if not taxonomy_file.is_file():
        raise Error(f"{taxonomy_file} not found: run `map` first")
    taxonomy = json.loads(taxonomy_file.read_text())
    prompt = "\n\n".join([
        (REFS / "planning.md").read_text(),
        "# Taxonomy to plan from",
        "```json\n" + json.dumps(taxonomy["tree"], indent=1) + "\n```",
    ])
    answer = ask(args.agent, prompt)
    try:
        skill = json.loads(answer[answer.find("{"):answer.rfind("}") + 1])
    except json.JSONDecodeError as exc:
        raise Error(f"agent did not return a JSON plan ({exc}):\n{answer[:800]}")
    plan = {"docs_dir": taxonomy["docs_dir"], "skill": skill}
    (out / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    diagram = mermaid(skill, lambda n: f"<b>{n['name']}</b>" + (
        "<br/><small>" + "<br/>".join(n["sources"]) + "</small>" if n.get("sources") else ""))
    (out / "plan.md").write_text(f"# Skill tree plan\n\n{diagram}\n")
    return {"plan": str(out / "plan.json"), "diagram": str(out / "plan.md"),
            "problems": plan_problems(load_plan(out))}


# --------------------------------------------------------------------------
# generate: agent writes each SKILL.md
# --------------------------------------------------------------------------

def node_prompt(node: dict, here: Path, ancestors: tuple, plan: dict) -> str:
    docs_dir = Path(plan["docs_dir"])
    lines = [(REFS / "writing.md").read_text(), "# Your assignment", "",
             f"Write the body of the `{node['name']}` skill.", "",
             f"Description: {node['description']}", ""]
    if ancestors:
        lines += ["Parent skills (already cover their own topics, do not repeat them):"]
        lines += [f"- {a['name']}: {a['description']}" for a in ancestors]
        lines.append("")
    if node.get("children"):
        lines += ["Subskills (listed automatically after your text):"]
        lines += [f"- {c['name']}: {c['description']}" for c in node["children"]]
        lines.append("")
    lines += ["Where each doc lives in the skill tree (use these paths to rewrite links):"]
    for other, other_dir, _ in walk(plan["skill"]):
        target = os.path.relpath(other_dir / "SKILL.md", here)
        lines += [f"- {src} -> {target}" for src in other.get("sources", [])]
    lines += ["", "# Source docs", ""]
    for src in node.get("sources", []):
        text = (docs_dir / src).read_text(encoding="utf-8")
        lines += [f'<doc path="{src}">', text, "</doc>", ""]
    return "\n".join(lines)


def ref_name(src: str) -> str:
    return src.replace("/", "-")


def render(node: dict, body: str) -> str:
    front = yaml.safe_dump({"name": node["name"], "description": node["description"]},
                           sort_keys=False, allow_unicode=True, width=10**6)
    parts = [f"---\n{front}---", body.strip()]
    if node.get("children"):
        parts.append("## Subskills\n\nRead the one that matches your task:\n\n" + "\n".join(
            f"- [{c['name']}]({c['name']}/SKILL.md): {c['description']}"
            for c in node["children"]))
    if node.get("sources"):
        parts.append("## Source docs\n\nVerbatim copies, for details not covered above:\n\n"
                     + "\n".join(f"- [{s}](references/{ref_name(s)})" for s in node["sources"]))
    return "\n\n".join(parts) + "\n"


def write_node(node, here: Path, ancestors, plan: dict, out: Path, agent: str) -> str:
    body = unfence(ask(agent, node_prompt(node, here, ancestors, plan)))
    node_dir = out / here
    (node_dir / "references").mkdir(parents=True, exist_ok=True)
    for src in node.get("sources", []):
        shutil.copyfile(Path(plan["docs_dir"]) / src, node_dir / "references" / ref_name(src))
    (node_dir / "SKILL.md").write_text(render(node, body))
    return str(here)


def cmd_generate(args) -> dict:
    out = Path(args.out)
    plan = load_plan(out)
    if problems := plan_problems(plan):
        return {"problems": problems}
    nodes = [n for n in walk(plan["skill"]) if not args.only or n[0]["name"] in args.only]

    def job(item):
        node, here, ancestors = item
        try:
            done = write_node(node, here, ancestors, plan, out, args.agent)
            print(f"wrote {done}/SKILL.md", file=sys.stderr)
            return None
        except Error as exc:
            return f"{here}: {exc}"

    with ThreadPoolExecutor(args.jobs) as pool:
        problems = [p for p in pool.map(job, nodes) if p]
    return {"skill": str(out / plan["skill"]["name"]), "nodes": len(nodes), "problems": problems}


# --------------------------------------------------------------------------
# check / install
# --------------------------------------------------------------------------

def check_tree(root: Path) -> list[str]:
    if not (root / "SKILL.md").is_file():
        return [f"{root}: no SKILL.md"]
    problems = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        d = skill_md.parent
        problems += [f"{d}: {e}" for e in validate(d.resolve())]
        text = skill_md.read_text(encoding="utf-8")
        if (n := len(text.splitlines())) > MAX_LINES:
            problems.append(f"{skill_md}: {n} lines (keep under {MAX_LINES})")
        for href in parse_md(text)[1]:
            target = href.split("#")[0]
            if is_local(href) and target and not (d / target).exists():
                problems.append(f"{skill_md}: broken link {href}")
        parent_md = d.parent / "SKILL.md"
        if d != root and (not parent_md.is_file()
                          or f"{d.name}/SKILL.md" not in parent_md.read_text(encoding="utf-8")):
            problems.append(f"{skill_md}: not linked from {parent_md}")
    return problems


def cmd_check(args) -> dict:
    root = Path(args.dir)
    return {"skill": str(root), "skills": len(list(root.rglob("SKILL.md"))),
            "problems": check_tree(root)}


def cmd_package(args) -> dict:
    """Zip a skill as <name>/... (the layout skill uploaders and `install` expect)."""
    src = Path(args.dir).resolve()
    if problems := check_tree(src):
        return {"problems": problems}
    base = Path(args.output).with_suffix("") if args.output else src.parent / src.name
    archive = shutil.make_archive(str(base), "zip", root_dir=src.parent, base_dir=src.name)
    return {"package": archive}


def zip_skill_name(path: Path) -> str:
    """Name of the single top-level skill directory in a skill zip."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
    tops = {n.split("/")[0] for n in names}
    if len(tops) != 1 or f"{next(iter(tops))}/SKILL.md" not in names:
        raise Error(f"{path} is not a skill package (expected one <name>/SKILL.md)")
    return tops.pop()


def cmd_install(args) -> dict:
    src = Path(args.dir).resolve()
    is_zip = src.suffix == ".zip"
    if not is_zip and not (src / "SKILL.md").is_file():
        raise Error(f"{src} is not a skill (no SKILL.md) nor a .zip package")
    to = Path(args.to).expanduser()
    dest = to / (zip_skill_name(src) if is_zip else src.name)
    if dest.exists():
        if not args.force:
            raise Error(f"{dest} exists (use --force to replace it)")
        shutil.rmtree(dest)
    if is_zip:
        shutil.unpack_archive(src, to)  # zipfile drops absolute and ".." paths
    else:
        shutil.copytree(src, dest)
    return {"installed": str(dest)}


def cmd_build(args) -> dict:
    result = cmd_map(args)
    for step in (cmd_plan, cmd_generate):
        result |= step(args)
        if result.get("problems"):
            return result
    args.dir = result["skill"]
    result |= cmd_check(args)
    if args.install and not result["problems"]:
        args.to = args.install
        result |= cmd_install(args)
    return result


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="emit JSON")
    workspace = argparse.ArgumentParser(add_help=False)
    workspace.add_argument("-o", "--out", default="build",
                           help="workspace directory (default: build)")
    agent = argparse.ArgumentParser(add_help=False)
    agent.add_argument("--agent", default=DEFAULT_AGENT,
                       help=f"agent command, prompt on stdin (default: {DEFAULT_AGENT!r})")
    agent.add_argument("-j", "--jobs", type=int, default=4,
                       help="skills written in parallel (default: 4)")

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(required=True, metavar="command")

    p = sub.add_parser("map", parents=[common, workspace], help="crawl docs into a taxonomy")
    p.add_argument("root", help="root markdown doc, e.g. docs/index.md")
    p.set_defaults(func=cmd_map)

    p = sub.add_parser("plan", parents=[common, workspace, agent], help="agent plans the skill tree")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("generate", parents=[common, workspace, agent], help="agent writes the skills")
    p.add_argument("--only", nargs="+", metavar="NAME", help="(re)write only these skills")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("check", parents=[common], help="validate a skill tree")
    p.add_argument("dir", help="skill directory (the one holding the root SKILL.md)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("package", parents=[common], help="zip a skill into an installer")
    p.add_argument("dir", help="skill directory")
    p.add_argument("-o", "--output", help="zip path (default: <dir>.zip)")
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("install", parents=[common], help="install a skill (directory or .zip)")
    p.add_argument("dir", metavar="src", help="skill directory or .zip from `package`")
    p.add_argument("--to", default="~/.agents/skills", help="skills directory (default: ~/.agents/skills)")
    p.add_argument("--force", action="store_true", help="replace an existing install")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("build", parents=[common, workspace, agent], help="map + plan + generate + check")
    p.add_argument("root", help="root markdown doc")
    p.add_argument("--install", metavar="DIR", help="also install into this skills directory")
    p.add_argument("--force", action="store_true", help="replace an existing install")
    p.set_defaults(func=cmd_build, only=None)

    args = parser.parse_args()
    try:
        result = args.func(args)
    except Error as exc:
        print(f"skilltree: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            if key != "problems":
                print(f"{key}: {value}")
        for problem in result.get("problems", []):
            print(f"problem: {problem}", file=sys.stderr)
    return 1 if result.get("problems") else 0


if __name__ == "__main__":
    sys.exit(main())
