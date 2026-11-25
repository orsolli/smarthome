#!/usr/bin/env bash
# backfill.sh - scan old Nix generations into one timeline.
#
# Run it inside a shell that has python3 and bottle:
#   nix-shell -p python3 python3Packages.bottle \
#     --command "vulnerabilities/scripts/backfill.sh --gens 1 2 3"
#
# A generation link is a different derivation of the same machine, so every
# scan is recorded under the identity of the running system (--as-target) and
# dated when that generation was activated: the mtime of the profile symlink,
# read with lstat (stat does not follow symlinks). The generation link itself is
# passed to vulnix and stored in scans.scanned_path, so the row says which
# generation it actually scanned.
#
# Usage:
#   backfill.sh --gens 1 2 3            # explicit generations
#   backfill.sh                         # every link in --profile-dir
#   backfill.sh --gens 2 3 --dry-run    # show what would run
#
# Options:
#   --gens N...        generations to scan (default: all found links)
#   --profile-dir DIR  where generation links live (default /nix/var/nix/profiles)
#   --db PATH          DATABASE_PATH (default: the app's data directory)
#   --target ID        identity the scans join (default /run/current-system)
#   --vulnix PATH      vulnix binary (default /run/current-system/sw/bin/vulnix)
#   --dry-run          print the commands instead of running them
#
# Note: vulnix -j exits 2 when it finds vulnerabilities. That is a result, not
# a failure: the JSON on stdout is still valid and the scan is stored.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

profile_dir=/nix/var/nix/profiles
db=""
target=/run/current-system
vulnix=/run/current-system/sw/bin/vulnix
dry_run=false
gens=()

while [ $# -gt 0 ]; do
  case "$1" in
    --gens)
      shift
      while [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; do
        gens+=("$1")
        shift
      done
      ;;
    --profile-dir) profile_dir="$2"; shift 2 ;;
    --db)          db="$2";         shift 2 ;;
    --target)      target="$2";     shift 2 ;;
    --vulnix)      vulnix="$2";     shift 2 ;;
    --dry-run)     dry_run=true;    shift ;;
    -h|--help)     sed -n '2,29p' "$0"; exit 0 ;;
    *)             echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Default: every generation link that still exists. Nothing is hardcoded, so a
# machine with a different number of generations backfills its own history.
if [ ${#gens[@]} -eq 0 ]; then
  for link in "$profile_dir"/system-*-link; do
    [ -L "$link" ] || continue
    gens+=("${link##*system-}")
    gens[-1]="${gens[-1]%-link}"
  done
  # system-10 sorts before system-2 as text; scan the oldest generation first.
  gens=($(printf '%s\n' "${gens[@]}" | sort -n))
fi

if [ ${#gens[@]} -eq 0 ]; then
  echo "no generation links found in $profile_dir" >&2
  exit 1
fi

if [ -z "$db" ]; then
  db="$MODULE_DIR/data/vulnix.db"
fi

if [ ! -x "$vulnix" ]; then
  echo "warning: vulnix is not executable at $vulnix; the mock scanner is used" >&2
fi

cd "$MODULE_DIR"

for gen in "${gens[@]}"; do
  link="$profile_dir/system-$gen-link"
  if [ ! -L "$link" ]; then
    echo "skipping generation $gen: $link does not exist"
    continue
  fi
  ts=$(date -d "@$(stat -c %Y "$link")" +%Y-%m-%dT%H:%M:%S)
  if $dry_run; then
    printf 'DATABASE_PATH=%s VULNIX_PATH=%s python -m app scan --target %s --as-target %s --at %s\n' \
      "$db" "$vulnix" "$link" "$target" "$ts"
    continue
  fi
  echo "scanning generation $gen (activated $ts)"
  DATABASE_PATH="$db" VULNIX_PATH="$vulnix" \
    python -m app scan --target "$link" --as-target "$target" --at "$ts"
done
