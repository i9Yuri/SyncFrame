#!/usr/bin/env bash
# ==============================================================================
# SyncFrame Desktop Launcher
# High-Fidelity Audio/Video Lossless Remux & Acoustic Synchronizer
# ==============================================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# ANSI Terminal Colors
CYAN='\033[0;36m'
EMERALD='\033[0;32m'
AMBER='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}[INFO] Inicializando SyncFrame v1.0.0...${NC}"

# 1. Checagem de ferramentas essenciais do sistema operacional
MISSING_DEPS=()

for bin in ffmpeg ffprobe mkvmerge mpv; do
    if ! command -v "$bin" &>/dev/null; then
        MISSING_DEPS+=("$bin")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}[ERRO CRITICO] Ferramentas do sistema ausentes:${NC} ${MISSING_DEPS[*]}"
    echo -e "${AMBER}Instale os pacotes requeridos atraves do gerenciador de sua distribuicao:${NC}"
    echo -e "  • Nobara / Fedora: ${CYAN}sudo dnf install ffmpeg mkvtoolnix mpv${NC}"
    echo -e "  • Ubuntu / Debian: ${CYAN}sudo apt install ffmpeg mkvtoolnix mpv${NC}"
    echo -e "  • Arch Linux:      ${CYAN}sudo pacman -S ffmpeg mkvtoolnix-cli mpv${NC}"
    exit 1
fi

# 2. Configuração do ambiente virtual Python (.venv)
VENV_DIR="$PROJECT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${AMBER}[CONFIG] Criando ambiente virtual isolado (.venv)...${NC}"
    python3 -m venv "$VENV_DIR" --system-site-packages
fi

# Ativação do ambiente virtual
source "$VENV_DIR/bin/activate"

# 3. Validação silenciosa e atômica de dependências
REQ_FILE="$PROJECT_DIR/requirements.txt"
HASH_FILE="$VENV_DIR/.requirements.hash"

if [ -f "$REQ_FILE" ]; then
    CURRENT_HASH=$(sha256sum "$REQ_FILE" | awk '{print $1}')
    SAVED_HASH=""
    [ -f "$HASH_FILE" ] && SAVED_HASH=$(cat "$HASH_FILE")

    if [ "$CURRENT_HASH" != "$SAVED_HASH" ]; then
        if ! python3 -c "import numpy, PySide6" &>/dev/null; then
            echo -e "${AMBER}[DEP] Atualizando dependencias Python (requirements.txt)...${NC}"
            pip install --quiet --disable-pip-version-check -r "$REQ_FILE" || {
                echo -e "${RED}Aviso: Falha ao atualizar algumas dependencias pelo pip. Tentando prosseguir com pacotes do sistema...${NC}"
            }
        fi
        echo "$CURRENT_HASH" > "$HASH_FILE"
    fi
fi

# 4. Execução da aplicação com contenção segura de concorrência
echo -e "${EMERALD}[OK] Ambiente validado. Iniciando interface grafica com limitacao de threads (2 cores)...${NC}"
export PYTHONPATH="$PROJECT_DIR:${PYTHONPATH:-}"
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export VECLIB_MAXIMUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
exec python3 "$PROJECT_DIR/src/main.py" "$@"
