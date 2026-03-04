#!/usr/bin/env bash
set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-ollama:11434}"
MODEL_NAME="${MODEL_NAME:-jarvis}"

wait_for_ollama() {
  echo "[jarvis] Waiting for Ollama at http://${OLLAMA_HOST} ..."
  for i in {1..60}; do
    if curl -fsS "http://${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
      echo "[jarvis] Ollama is up."
      return 0
    fi
    sleep 1
  done
  echo "[jarvis] Ollama did not become ready in time." >&2
  return 1
}

create_model_if_modelfile_present() {
  if [[ -f "/app/Modelfile" ]]; then
    echo "[jarvis] Creating/updating model '${MODEL_NAME}' from /app/Modelfile ..."
    # Ollama CLI can talk to a remote host via OLLAMA_HOST env (scheme optional).
    export OLLAMA_HOST="http://${OLLAMA_HOST}"
    ollama create "${MODEL_NAME}" -f /app/Modelfile || true
  else
    echo "[jarvis] No /app/Modelfile mounted; skipping model creation."
  fi
}

main() {
  wait_for_ollama
  create_model_if_modelfile_present

  # If user passes a command, run it. Otherwise start jarvis chat.
  if [[ $# -gt 0 ]]; then
    exec "$@"
  else
    exec jarvis chat
  fi
}

main "$@"
