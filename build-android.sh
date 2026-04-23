#!/usr/bin/env bash
# Build a debug APK using the official kivy/buildozer Docker image.
# Requires: Docker Desktop (macOS/Windows) or Docker (Linux)
# First run downloads SDK/NDK and can take 20–40+ minutes.

set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"

# Apple Silicon: run the published amd64 image under emulation (slower but works).
PLATFORM_FLAG=()
if [[ "$(uname -m)" == "arm64" ]]; then
  PLATFORM_FLAG=(--platform linux/amd64)
fi

echo "Project: $ROOT"
echo "APK will appear in: $ROOT/bin/"
echo ""

# Image entrypoint already runs `buildozer`; pass only target and command.
exec docker run --interactive --tty --rm \
  "${PLATFORM_FLAG[@]}" \
  --volume "$HOME/.buildozer:/home/user/.buildozer" \
  --volume "$ROOT:/home/user/hostcwd" \
  --workdir /home/user/hostcwd \
  kivy/buildozer \
  android debug
