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
