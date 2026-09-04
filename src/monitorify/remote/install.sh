#!/usr/bin/env bash

set -e

REPO_URL="https://github.com/leonst036/Monitorify.git"
export PATH="$HOME/.local/bin:$PATH"

install_via_pipx() {
    if command -v pipx >/dev/null 2>&1; then
        echo "[1/3] Attempting installation via pipx..."
        pipx ensurepath >/dev/null 2>&1 || true
        if pipx install --force "git+${REPO_URL}"; then
            echo "Successfully installed via pipx"
            return 0
        fi
    fi
    return 1
}

install_via_pip() {
    echo "[2/3] Attempting installation via pip..."
    if command -v pip >/dev/null 2>&1; then
        if pip install --upgrade "git+${REPO_URL}" || pip install --break-system-packages --upgrade "git+${REPO_URL}"; then
            echo "Successfully installed via pip"
            return 0
        fi
    fi
    if python3 -m pip --version >/dev/null 2>&1; then
        if python3 -m pip install --upgrade "git+${REPO_URL}" || python3 -m pip install --break-system-packages --upgrade "git+${REPO_URL}"; then
            echo "Successfully installed via python3 -m pip"
            return 0
        fi
    fi
    return 1
}

install_deps() {
    echo "[3/3] pipx and pip not found. Attempting to install package manager dependencies..."
    SUDO_CMD=""
    if [ "$(id -u)" -ne 0 ]; then
        if command -v sudo >/dev/null 2>&1; then
            SUDO_CMD="sudo"
        fi
    fi

    if command -v apt-get >/dev/null 2>&1; then
        $SUDO_CMD apt-get update && $SUDO_CMD apt-get install -y pipx git || $SUDO_CMD apt-get install -y python3-pip python3-venv git
    elif command -v dnf >/dev/null 2>&1; then
        $SUDO_CMD dnf install -y pipx git || $SUDO_CMD dnf install -y python3-pip git
    elif command -v pacman >/dev/null 2>&1; then
        $SUDO_CMD pacman -Sy --noconfirm python-pipx git || $SUDO_CMD pacman -Sy --noconfirm python-pip git
    elif command -v zypper >/dev/null 2>&1; then
        $SUDO_CMD zypper install -y python3-pipx git || $SUDO_CMD zypper install -y python3-pip git
    elif command -v apk >/dev/null 2>&1; then
        $SUDO_CMD apk add pipx git || $SUDO_CMD apk add py3-pip git
    else
        echo "No supported package manager found."
        return 1
    fi
}

if install_via_pipx; then
    exit 0
fi

if install_via_pip; then
    exit 0
fi

if install_deps; then
    export PATH="$HOME/.local/bin:$PATH"
    if install_via_pipx; then
        exit 0
    fi
    if install_via_pip; then
        exit 0
    fi
fi

echo "All installation methods failed."
exit 1
