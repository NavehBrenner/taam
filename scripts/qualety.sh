#!/usr/bin/env bash
# Run qualety (https://github.com/NavehBrenner/qualety) against this repo.
#
# qualety is not on npm or PyPI yet and has no tagged release (qualety#59), so
# the only way to run it today is to build the workspace. This clones a pinned
# commit into .tools/ (gitignored) and execs the built CLI. Same script locally
# and in CI, so a green CI means a green desk.
#
# When the first registry cut lands, this whole file becomes `pip install qualety`.
#
# Usage:  ./scripts/qualety.sh            # check
#         ./scripts/qualety.sh check --diff
set -euo pipefail

REPO=https://github.com/NavehBrenner/qualety.git
PIN=4b3dd3692fc9e01658e8bed47d11568c60e66933
DIR="$(git rev-parse --show-toplevel)/.tools/qualety"
CLI="$DIR/packages/qualety/dist/cli.js"

if [ "$(git -C "$DIR" rev-parse HEAD 2>/dev/null || true)" != "$PIN" ] || [ ! -f "$CLI" ]; then
  echo "qualety: building $PIN into .tools/qualety (one-off, then cached)" >&2
  rm -rf "$DIR"
  git clone --quiet --filter=blob:none "$REPO" "$DIR"
  git -C "$DIR" switch --quiet --detach "$PIN"
  (cd "$DIR" && pnpm install --frozen-lockfile --silent && pnpm build >/dev/null)
fi

exec node "$CLI" "${@:-check}"
