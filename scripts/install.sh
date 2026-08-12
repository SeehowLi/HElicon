#!/bin/sh
set -eu

usage() {
    echo "Usage: install.sh --target codex|claude-code|both|repo-local [--dry-run]"
}

target=""
dry_run=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --target)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            target=$2
            shift 2
            ;;
        --dry-run)
            dry_run=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

case "$target" in
    codex|claude-code|both|repo-local) ;;
    *) usage >&2; exit 2 ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_dir=$(dirname -- "$script_dir")
timestamp=$(date +%Y%m%d-%H%M%S)

python_cmd=""
if command -v python3 >/dev/null 2>&1; then
    python_cmd=python3
elif command -v python >/dev/null 2>&1; then
    python_cmd=python
fi

install_one() {
    destination=$1
    backup="${destination}.bak.${timestamp}"
    echo "target: $destination"
    if [ -e "$destination" ]; then
        echo "backup: $backup"
    fi
    if [ "$dry_run" -eq 1 ]; then
        echo "dry-run: copy $source_dir -> $destination"
        return
    fi
    [ -n "$python_cmd" ] || { echo "Python 3 is required." >&2; exit 1; }
    mkdir -p -- "$(dirname -- "$destination")"
    had_backup=0
    if [ -e "$destination" ]; then
        mv -- "$destination" "$backup"
        had_backup=1
    fi
    if ! mkdir -p -- "$destination"; then
        rm -rf -- "$destination"
        [ "$had_backup" -eq 0 ] || mv -- "$backup" "$destination"
        echo "Install copy failed; previous installation restored." >&2
        exit 1
    fi
    copy_failed=0
    for entry in "$source_dir"/.[!.]* "$source_dir"/..?* "$source_dir"/*; do
        [ -e "$entry" ] || continue
        name=$(basename -- "$entry")
        case "$name" in
            .git|.agents|.helicon|__pycache__|evals|handoff) continue ;;
        esac
        cp -R -- "$entry" "$destination"/ || copy_failed=1
    done
    find "$destination" -type d -name '__pycache__' -prune -exec rm -rf -- {} + || copy_failed=1
    find "$destination" -type f -name '*.pyc' -delete || copy_failed=1
    if [ "$copy_failed" -ne 0 ]; then
        rm -rf -- "$destination"
        [ "$had_backup" -eq 0 ] || mv -- "$backup" "$destination"
        echo "Install copy failed; previous installation restored." >&2
        exit 1
    fi
    if ! "$python_cmd" -B "$destination/scripts/check_skill_integrity.py" "$destination"; then
        rm -rf -- "$destination"
        [ "$had_backup" -eq 0 ] || mv -- "$backup" "$destination"
        echo "Integrity check failed; previous installation restored." >&2
        exit 1
    fi
    echo "installed: $destination"
}

case "$target" in
    codex)
        install_one "$HOME/.agents/skills/HElicon"
        ;;
    claude-code)
        install_one "$HOME/.claude/skills/HElicon"
        ;;
    both)
        install_one "$HOME/.agents/skills/HElicon"
        install_one "$HOME/.claude/skills/HElicon"
        ;;
    repo-local)
        install_one "$PWD/.agents/skills/HElicon"
        ;;
esac
