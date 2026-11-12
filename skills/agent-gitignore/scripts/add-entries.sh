#!/bin/sh
# Add agent runtime artifact entries to the repo's .gitignore (idempotent),
# then commit ONLY that file so the commit stays atomic.
set -eu

MARKER="# agent runtime artifacts"
COMMIT_MSG="chore: ignore agent runtime artifacts"

# agent|kind|path
#   dir     -> write "path/"
#   file    -> write "path"
#   pattern -> write the glob as-is; only added when at least one match exists
# Extend only after verifying the path holds disposable project-level state,
# never user-authored agent configuration.
CATALOG='
zcode|dir|.zcode/plans
zcode|dir|.zcode/workflow-runs
zcode|dir|.zcode/workflow-drafts
workbuddy|dir|.workbuddy
mimosa|dir|.mimosa
video2code|dir|.v2c
claude-code|file|.claude/settings.local.json
aider|file|.aider.chat.history.md
aider|file|.aider.input.history
aider|file|.aider.llm.history
aider|pattern|.aider.tags.cache.v*/
'

usage() {
  cat <<'USAGE'
usage: add-entries.sh [--dry-run] [--no-commit] [--only <agents>]

  --dry-run        print what would change; touch nothing, commit nothing
  --no-commit      append entries but skip the automatic commit
  --only <agents>  comma-separated agents (zcode,workbuddy,mimosa,
                   video2code,claude-code,aider)
USAGE
}

dry_run=0
do_commit=1
only_list=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) dry_run=1 ;;
    --no-commit) do_commit=0 ;;
    --only)
      [ $# -ge 2 ] || { echo "--only requires an agent list" >&2; exit 2; }
      only_list=",$2,"
      shift
      ;;
    --only=*) only_list=",${1#--only=}," ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

# Reject --only values that name no catalog agent, so a typo cannot silently
# turn into a no-op.
if [ -n "$only_list" ]; then
  old_ifs=$IFS
  IFS=','
  for requested in $only_list; do
    [ -n "$requested" ] || continue
    matched=0
    while IFS='|' read -r agent _ _; do
      if [ "$agent" = "$requested" ]; then
        matched=1
      fi
    done <<EOF
$CATALOG
EOF
    if [ "$matched" -eq 0 ]; then
      echo "unknown agent in --only: $requested" >&2
      IFS=$old_ifs
      exit 2
    fi
  done
  IFS=$old_ifs
fi

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
gi=$root/.gitignore

# In a git repo, check whether .gitignore already had pending changes (staged
# or unstaged) BEFORE creating/touching it: an auto-commit would mix them in,
# while a file this script itself is about to create must not count as pending.
in_repo=0
pending=""
if git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  in_repo=1
  pending=$(git -C "$root" status --porcelain -- .gitignore)
fi

if [ "$dry_run" -eq 0 ] && [ ! -f "$gi" ]; then
  touch "$gi"
fi

is_ignored() {
  if [ "$in_repo" -eq 1 ]; then
    git -C "$root" check-ignore --no-index -q -- "$1"
  else
    base=${1%/}
    if [ -f "$gi" ]; then
      while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
          "$base" | "$base/" | "/$base" | "/$base/") return 0 ;;
        esac
      done <"$gi"
    fi
    return 1
  fi
}

added=""
covered=""
tracked=""
absent=""
header_written=0

while IFS='|' read -r agent kind rel; do
  [ -n "$agent" ] || continue

  if [ -n "$only_list" ]; then
    case "$only_list" in
      *",$agent,"*) ;;
      *) continue ;;
    esac
  fi

  # Expand patterns in the repo root; literal paths are used as-is.
  first=""
  if [ "$kind" = "pattern" ]; then
    for candidate in "$root"/$rel; do
      if [ -e "$candidate" ]; then
        first=$candidate
        break
      fi
    done
  elif [ -e "$root/$rel" ]; then
    first="$root/$rel"
  fi

  if [ -z "$first" ]; then
    absent="$absent $rel ($agent)"
    continue
  fi

  probe=${first#"$root"/}

  case "$kind" in
    dir) entry="$rel/" ;;
    *) entry="$rel" ;;
  esac

  # Report tracked paths because ignore rules do not affect the index. A
  # directory rule still applies to future untracked artifacts in that tree.
  if [ "$in_repo" -eq 1 ]; then
    case "$kind" in
      dir) tracked_paths=$(git -C "$root" ls-files -- "$rel") ;;
      pattern) tracked_paths=$(git -C "$root" ls-files -- "$probe") ;;
      *) tracked_paths=$(git -C "$root" ls-files -- "$probe") ;;
    esac
    if [ -n "$tracked_paths" ]; then
      case "$kind" in
        dir)
          tracked="$tracked $(printf '%s' "$tracked_paths" | tr '\n' ',' | sed 's/,$//') ($agent; unaffected)"
          ;;
        *)
          tracked="$tracked $probe ($agent)"
          continue
          ;;
      esac
    fi
  fi

  if is_ignored "$probe"; then
    covered="$covered $entry ($agent)"
    continue
  fi

  added="$added $entry ($agent)"

  if [ "$dry_run" -eq 0 ]; then
    if [ "$header_written" -eq 0 ]; then
      # Normalize the trailing newline only when an append is actually needed;
      # a no-op run must leave .gitignore byte-identical.
      if [ -s "$gi" ] && [ -n "$(tail -c 1 "$gi")" ]; then
        printf '\n' >>"$gi"
      fi
      grep -qxF "$MARKER" "$gi" || printf '%s\n' "$MARKER" >>"$gi"
      header_written=1
    fi
    printf '%s\n' "$entry" >>"$gi"
  fi
done <<EOF
$CATALOG
EOF

echo "repo root: $root"
if [ "$in_repo" -eq 0 ]; then
  echo "not a git repository: changes cannot be committed; review whether to keep .gitignore"
fi
if [ "$dry_run" -eq 1 ]; then
  [ -n "$added" ] && echo "would add:$added"
else
  [ -n "$added" ] && echo "added:$added"
fi
[ -n "$covered" ] && echo "already ignored:$covered"
[ -n "$tracked" ] && echo "tracked, unaffected:$tracked"
[ -n "$absent" ] && echo "not present, skipped:$absent"

if [ "$dry_run" -eq 0 ] && [ "$do_commit" -eq 1 ] && [ "$in_repo" -eq 1 ] && [ -n "$added" ]; then
  if [ -n "$pending" ]; then
    echo "commit skipped: .gitignore already had pending changes before this run:"
    printf '%s\n' "$pending"
  else
    git -C "$root" add -- .gitignore
    if out=$(git -C "$root" commit -m "$COMMIT_MSG" -- .gitignore 2>&1); then
      echo "committed: $(git -C "$root" rev-parse --short HEAD) $COMMIT_MSG"
    else
      echo "commit failed: $out"
    fi
  fi
fi
