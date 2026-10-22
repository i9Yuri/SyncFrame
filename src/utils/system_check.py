"""System dependencies validation for host multimedia utilities."""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SystemDiagnostics:
    """Status report for host binaries required by SyncFrame."""
    ffmpeg_available: bool = False
    ffprobe_available: bool = False
    mkvmerge_available: bool = False
    mkvextract_available: bool = False
    mpv_available: bool = False
    ffplay_available: bool = False
    binary_paths: Dict[str, str] = field(default_factory=dict)
    missing_required: List[str] = field(default_factory=list)

    @property
    def is_operational(self) -> bool:
        """True if all mandatory binaries (ffmpeg, ffprobe, mkvmerge) are present."""
        return len(self.missing_required) == 0

    def install_instructions(self) -> str:
        """Generates distribution-specific package install instructions."""
        lines = [
            "Para instalar as ferramentas necessárias em sua distribuição Linux:",
            "",
            "• Nobara / Fedora / RHEL:",
            "  sudo dnf install ffmpeg mkvtoolnix mpv",
            "",
            "• Ubuntu / Debian / Mint:",
            "  sudo apt update && sudo apt install ffmpeg mkvtoolnix mpv",
            "",
            "• Arch Linux / Manjaro:",
            "  sudo pacman -S ffmpeg mkvtoolnix-cli mpv",
        ]
        return "\n".join(lines)


def check_system_dependencies() -> SystemDiagnostics:
    """
    Checks the availability and absolute paths of external multimedia tools on the host.
    """
    diag = SystemDiagnostics()
    required = ["ffmpeg", "ffprobe", "mkvmerge"]
    optional = ["mkvextract", "mpv", "ffplay"]

    for name in required:
        path = shutil.which(name)
        if path:
            diag.binary_paths[name] = path
            setattr(diag, f"{name}_available", True)
        else:
            diag.missing_required.append(name)

    for name in optional:
        path = shutil.which(name)
        if path:
            diag.binary_paths[name] = path
            setattr(diag, f"{name}_available", True)

    return diag


def diagnose_system_crash_logs() -> Dict[str, str]:
    """
    Inspeciona os logs do sistema operacional (journalctl da sessão anterior)
    para isolar causas de reinicialização ou desligamento abrupto (OOM, picos térmicos,
    falha de hardware MCE ou desarme de proteção da fonte/VRM).
    
    Returns:
        Dicionário com o diagnóstico detalhado e mitigações recomendadas.
    """
    report = {
        "last_reboot_type": "Desconhecido / Não diagnosticado",
        "oom_detected": "False",
        "mce_hardware_error": "False",
        "thermal_status": "Normal / Não reportado",
        "last_logged_activity": "",
        "recommended_mitigation": "Manter concorrência limitada (-threads 2) e prioridade normalizada."
    }

    journal_output = ""
    try:
        proc = subprocess.run(
            ["journalctl", "-b", "-1", "-n", "120", "--no-pager"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=4
        )
        if proc.returncode == 0:
            journal_output = proc.stdout
    except Exception:
        journal_output = ""

    if not journal_output:
        # Fallback para dmesg ou logs locais se journalctl não estiver disponível
        report["last_reboot_type"] = "Indisponível (journalctl anterior inacessível)"
        return report

    lines = [line.strip() for line in journal_output.strip().split("\n") if line.strip()]
    if lines:
        report["last_logged_activity"] = lines[-1]

    lower_log = journal_output.lower()

    # 1. Checagem de OOM Killer
    if any(k in lower_log for k in ("out of memory", "oom-killer", "killed process", "invoked oom-killer")):
        report["oom_detected"] = "True"
        report["last_reboot_type"] = "Estouro de Memória (OOM Killer acionado)"
        report["recommended_mitigation"] = "Reduzir janelas de leitura PCM e aplicar streaming estrito em blocos."

    # 2. Checagem de MCE / Hardware Panic
    elif any(k in lower_log for k in ("machine check exception", "mce: [hardware error]", "kernel panic", "fatal exception")):
        report["mce_hardware_error"] = "True"
        report["last_reboot_type"] = "Kernel Panic ou Falha de Hardware (MCE)"
        report["recommended_mitigation"] = "Verificar estabilidade de tensão de CPU e memórias ECC."

    # 3. Checagem de Desligamento Limpo vs Queda Abrupta
    clean_shutdown = any(k in lower_log for k in (
        "reached target shutdown",
        "reached target reboot",
        "systemd-shutdown",
        "reboot: restart",
        "power down"
    ))

    if not clean_shutdown and report["oom_detected"] == "False" and report["mce_hardware_error"] == "False":
        report["last_reboot_type"] = "Desarme Abrupto de Hardware (OCP/Térmico - Sem Shutdown Limpo)"
        report["recommended_mitigation"] = (
            "Limitar subprocessos FFmpeg a -threads 2, fixar OMP_NUM_THREADS=2 e "
            "evitar multiplexação simultânea com reprodução de vídeo acelerada por hardware."
        )

    # 4. Checagem do Daemon Térmico (thermald)
    if "thermald" in lower_log:
        if "unsupported cpu model" in lower_log or "deactivated successfully" in lower_log:
            report["thermal_status"] = "thermald inativo (CPU Xeon/plataforma não suportada pelo daemon)"
        else:
            report["thermal_status"] = "thermald ativo"

    return report
