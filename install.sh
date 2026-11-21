#!/bin/sh
# Install the iskillz skill into a project, for every agent it uses.
#
#   cd my-project
#   curl -fsSL https://raw.githubusercontent.com/anteloc/iskillz/master/install.sh | sh
#
# Options (after `sh -s --` when piped, e.g. `| sh -s -- --global`):
#   [DIR]          project to install into (default: the current directory)
#   --global       install into your personal skills directories instead
#   --agent NAME   agent directory to use: claude, agents, qwen, codex, gemini,
#                  opencode (repeatable; default: every one the project has,
#                  else .claude)
#   --ref REF      branch, tag or commit to install (default: master)
#   --force        replace an existing iskillz folder not installed by this script
#
# Run again to update. From a local checkout, `./install.sh DIR` installs that
# checkout instead of downloading.
set -eu

REPO="${ISKILLZ_REPO:-anteloc/iskillz}"
REF="${ISKILLZ_REF:-master}"
SKILL_DIR="skills/iskillz"
FILES="SKILL.md scripts references LICENSE CC-BY-SA-4.0"
AGENT_DIRS=".claude .agents .qwen .codex .gemini .opencode"
MARKER=".iskillz-install"

say() { printf '%s\n' "$*"; }
die() { printf 'iskillz install: %s\n' "$*" >&2; exit 1; }

target=. global=0 agents="" force=0
while [ $# -gt 0 ]; do
  case "$1" in
    --global) global=1 ;;
    --agent) [ $# -ge 2 ] || die "--agent needs a name"
             agents="$agents .${2#.}"; shift ;;
    --ref) [ $# -ge 2 ] || die "--ref needs a value"; REF=$2; shift ;;
    --force) force=1 ;;
    -h|--help) sed -n '2,18p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) die "unknown option $1 (see --help)" ;;
    *) target=$1 ;;
  esac
  shift
done

[ "$global" = 1 ] && target=$HOME
[ -d "$target" ] || die "no such directory: $target"
target=$(cd "$target" && pwd)

# Source: this checkout when run from one, else a download of $REPO at $REF.
src=""
case "$0" in
  *install.sh)
    here=$(cd "$(dirname "$0")" && pwd)/$SKILL_DIR
    [ -f "$here/SKILL.md" ] && [ -f "$here/scripts/skilltree.py" ] && src=$here ;;
esac
if [ -z "$src" ]; then
  command -v curl >/dev/null || die "curl is needed to download iskillz"
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL -o "$tmp/src.tar.gz" "https://github.com/$REPO/archive/$REF.tar.gz" 2>/dev/null \
    || die "could not download $REPO at $REF (no such branch, tag or commit?)"
  tar -xzf "$tmp/src.tar.gz" -C "$tmp" && rm "$tmp/src.tar.gz"
  src=$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -n 1)/$SKILL_DIR
  [ -f "$src/SKILL.md" ] || die "$REPO at $REF has no $SKILL_DIR/SKILL.md"
  version=$REF
else
  version="local checkout $src"
fi

# Where: the agent directories the project (or $HOME) already has.
if [ -z "$agents" ]; then
  for d in $AGENT_DIRS; do [ -d "$target/$d" ] && agents="$agents $d"; done
fi
[ -n "$agents" ] || agents=".claude"

for d in $agents; do
  dest="$target/$d/skills/iskillz"
  if [ -e "$dest" ] && [ ! -f "$dest/$MARKER" ] && [ "$force" != 1 ]; then
    die "$dest exists and was not installed by this script (use --force to replace it)"
  fi
  rm -rf "$dest"
  mkdir -p "$dest"
  for f in $FILES; do
    [ -e "$src/$f" ] && cp -R "$src/$f" "$dest/"
  done
  find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
  printf 'repo: %s\nversion: %s\n' "$REPO" "$version" > "$dest/$MARKER"
  say "installed: $dest"
  last=$dest
done

# Requirements of the skill itself: Python 3.11+ runs the script, git fetches repos.
python=""
for p in python3 python; do
  if command -v "$p" >/dev/null && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    python=$p; break
  fi
done
if [ -n "$python" ]; then
  # First run installs the script's dependencies (private virtualenv): do it now.
  say "setting up the skill's Python dependencies (once, about a minute)..."
  "$python" "$last/scripts/skilltree.py" --help >/dev/null \
    || say "note: could not set up the dependencies now (the skill retries on first use)"
else
  say "note: the skill needs Python 3.11 or newer: https://www.python.org/downloads/"
fi
command -v git >/dev/null || say "note: install git to fetch docs from repositories"

say ""
say "Done. Start a new agent session so it picks up the skill, then ask e.g.:"
say "  \"make a skill for the <library> API and install it in this project\""
[ "$global" = 1 ] || say "Commit the skill folder(s) above to share them with your team."
