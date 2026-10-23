#!/usr/bin/env bash
# ==============================================================================
# SyncFrame Standalone Binary Build Pipeline (Linux x86_64)
# ==============================================================================
# Compila a aplicação SyncFrame em um único executável ELF autônomo (--onefile)
# utilizando PyInstaller e a especificação de otimização de footprint syncframe.spec.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "========================================================================"
echo "  SyncFrame — Pipeline de Empacotamento em Binário Único (v1.0.0)"
echo "========================================================================"

# 1. Localizar ou validar PyInstaller
PYINSTALLER_BIN=""
if [[ -f "${SCRIPT_DIR}/.venv/bin/pyinstaller" ]]; then
    PYINSTALLER_BIN="${SCRIPT_DIR}/.venv/bin/pyinstaller"
elif command -v pyinstaller &>/dev/null; then
    PYINSTALLER_BIN="$(command -v pyinstaller)"
elif python3 -m PyInstaller --version &>/dev/null; then
    PYINSTALLER_BIN="python3 -m PyInstaller"
else
    echo "[-] Erro: PyInstaller não encontrado no ambiente virtual nem no host."
    echo "    Instale-o via: pip install pyinstaller"
    exit 1
fi

echo "[+] Utilizando compilador PyInstaller: ${PYINSTALLER_BIN}"

# 2. Limpeza pré-compilação de artefatos residuais
echo "[+] Limpando diretórios de build anteriores (build/, dist/)..."
rm -rf build dist

# 3. Execução da compilação via syncframe.spec
echo "[+] Iniciando compilação do executável standalone ELF..."
START_TIME=$(date +%s)

${PYINSTALLER_BIN} --clean syncframe.spec

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# 4. Validação da integridade do artefato gerado
TARGET_BINARY="${SCRIPT_DIR}/dist/SyncFrame"

if [[ ! -f "${TARGET_BINARY}" ]]; then
    echo "[-] Erro crítico: O binário esperado '${TARGET_BINARY}' não foi gerado."
    exit 1
fi

chmod +x "${TARGET_BINARY}"

BINARY_SIZE="$(du -h "${TARGET_BINARY}" | cut -f1)"

echo ""
echo "========================================================================"
echo "  [OK] Compilacao Concluida com Sucesso em ${ELAPSED} segundos!"
echo "========================================================================"
echo "  • Caminho do Executável : ${TARGET_BINARY}"
echo "  • Tamanho do Binário    : ${BINARY_SIZE}"
echo "  • Formato               : $(file -b "${TARGET_BINARY}")"
echo "========================================================================"
echo ""

# 5. Execução do teste pré-voo automatizado no binário
echo "[+] Executando teste pré-voo de integridade no binário compilado..."
echo "--- Versão do Binário ---"
"${TARGET_BINARY}" --version

echo ""
echo "--- Diagnóstico de Sistema via Binário ---"
"${TARGET_BINARY}" --cli-check

echo ""
echo "========================================================================"
echo "  Binário pronto para uso!"
echo "  Para testar a interface gráfica, execute via duplo clique ou pelo terminal:"
echo "    ./dist/SyncFrame"
echo "========================================================================"
