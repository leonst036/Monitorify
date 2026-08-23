#!/usr/bin/env bash

REPO_URL="https://github.com/leonst036/Monitorify.git"

echo "[1/3] Attempting installation via pipx..."
if command -v pipx >/dev/null 2>&1 && pipx install "git+${REPO_URL}"; then
    echo "Successfully installed via pipx"
    exit 0
fi

echo "[2/3] Attempting installation via pip+git..."
if pip install "git+${REPO_URL}" 2>/dev/null || \
   pip install --break-system-packages "git+${REPO_URL}" 2>/dev/null || \
   python3 -m pip install "git+${REPO_URL}" 2>/dev/null || \
   python3 -m pip install --break-system-packages "git+${REPO_URL}" 2>/dev/null; then
    echo "Successfully installed via pip+git"
    exit 0
fi

echo "[3/3] Attempting installation via git clone..."
TMP_DIR=$(mktemp -d)
if git clone "${REPO_URL}" "$TMP_DIR" && \
   (pip install "$TMP_DIR" 2>/dev/null || \
    pip install --break-system-packages "$TMP_DIR" 2>/dev/null || \
    python3 -m pip install "$TMP_DIR" 2>/dev/null || \
    python3 -m pip install --break-system-packages "$TMP_DIR" 2>/dev/null); then
    rm -rf "$TMP_DIR"
    echo "Successfully installed via git clone"
    exit 0
else
    rm -rf "$TMP_DIR"
    echo "All installation methods failed."
    exit 1
fi
