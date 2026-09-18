#!/usr/bin/env bash
# ============================================================================
# Copies the authored lab guides into the CE Qwiklabs content bundle.
#
# The bundle needs real files at instructions/<locale>.md (GitWhisperer reads
# them from the bundle directory, and symlinks do not survive the export), but
# the guides are authored under labs/. Rather than maintain two copies by hand,
# this script regenerates the bundle copies and --check verifies they are in
# sync, so drift fails loudly in review instead of silently shipping a stale
# instruction file.
#
# Usage:
#   ./scripts/sync_qwiklabs_bundle.sh          # regenerate
#   ./scripts/sync_qwiklabs_bundle.sh --check  # verify only, non-zero if stale
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE="${REPO_ROOT}/qwiklabs_bundle/labs/gemini-enterprise-adk-lab"
DEST="${BUNDLE}/instructions"

declare -A MAP=(
  ["ko.md"]="labs/QWIKLABS_LAB_GUIDE.md"
  ["en.md"]="labs/QWIKLABS_LAB_GUIDE_EN.md"
)

CHECK_ONLY=0
if [ "${1:-}" = "--check" ]; then
  CHECK_ONLY=1
fi

mkdir -p "${DEST}"
STALE=0

for locale_file in "${!MAP[@]}"; do
  src="${REPO_ROOT}/${MAP[$locale_file]}"
  dst="${DEST}/${locale_file}"
  if [ ! -f "${src}" ]; then
    echo "[ERROR] source guide not found: ${src}" >&2
    exit 1
  fi
  if [ "${CHECK_ONLY}" = "1" ]; then
    if [ ! -f "${dst}" ] || ! cmp -s "${src}" "${dst}"; then
      echo "  [STALE] ${locale_file} differs from ${MAP[$locale_file]}"
      STALE=1
    else
      echo "  [OK]    ${locale_file}"
    fi
  else
    cp "${src}" "${dst}"
    echo "  [SYNC]  ${MAP[$locale_file]} -> instructions/${locale_file}"
  fi
done

if [ "${CHECK_ONLY}" = "1" ]; then
  if [ "${STALE}" = "1" ]; then
    echo
    echo "[ERROR] Bundle instructions are out of date. Run: ./scripts/sync_qwiklabs_bundle.sh" >&2
    exit 1
  fi
  echo "[OK] Bundle instructions are in sync."
fi
