#!/usr/bin/env bash
# Generated-clean gate: regenerate everything, fail if the working tree changed.
# Proves generated code matches its source contract and was not hand-edited.
# Wire your real generator(s) below. Run: bash tools/verify/check-generated-clean.sh
set -euo pipefail

# --- Replace with the repo's actual generator commands ---
# Examples:
#   pnpm run gen:api        # openapi-generator / orval
#   buf generate            # protobuf
#   pnpm run gen:prisma     # prisma generate
GENERATE_CMDS=(
  # "pnpm run generate"
)

if [ ${#GENERATE_CMDS[@]} -eq 0 ]; then
  echo "check-generated-clean: no generators configured — edit GENERATE_CMDS or remove this check." >&2
  exit 0
fi

for cmd in "${GENERATE_CMDS[@]}"; do
  echo "+ $cmd"
  eval "$cmd"
done

if ! git diff --quiet; then
  echo 'Generated files are not clean. Run the generator(s) and commit the result:' >&2
  git --no-pager diff --stat
  exit 1
fi
echo 'check-generated-clean: ok'
