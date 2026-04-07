#!/bin/bash

set -euo pipefail

REMOTE_NAME="clinerules"
REMOTE_URL="https://github.com/ondrej-winter/clinerules"
REMOTE_REF="${REMOTE_NAME}/master"

sync_folder() {
  local source_path="$1"
  local destination_path="$2"
  local temp_root
  local extracted_path
  local staging_path

  temp_root="$(mktemp -d)"
  extracted_path="${temp_root}/${source_path}"
  staging_path="${temp_root}/staged"

  trap 'rm -rf "${temp_root}"' RETURN

  git archive --format=tar "${REMOTE_REF}" "${source_path}" | tar -xf - -C "${temp_root}"

  mkdir -p "${staging_path}"
  cp -R "${extracted_path}/." "${staging_path}/"

  rm -rf "${destination_path}"
  mkdir -p "${destination_path}"
  cp -R "${staging_path}/." "${destination_path}/"
}

ensure_remote() {
  if ! git remote get-url "${REMOTE_NAME}" >/dev/null 2>&1; then
    git remote add "${REMOTE_NAME}" "${REMOTE_URL}"
  fi
}

ensure_remote

git fetch "${REMOTE_NAME}" master

# Sync vendored copies from clinerules/master:
# - python/hexagonal/agents -> .agents/
# - python/hexagonal/clinerules -> .clinerules/
sync_folder "python/hexagonal/agents" ".agents"
sync_folder "python/hexagonal/clinerules" ".clinerules"
