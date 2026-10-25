"""Background low-priority worker auditing local and remote versions of tools and SyncFrame."""

import json
import logging
import os
import shutil
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Optional

from PySide6.QtCore import QThread, Signal

from ...utils.system_check import PreFlightChecker

logger = logging.getLogger(__name__)

CURRENT_SYNCFRAME_VERSION = "1.2.0"


class DependencyUpdateWorker(QThread):
    """
    Asynchronous low-priority worker querying local and remote dependency versions.
    Performs silent background audits with zero UI thread contention and strict offline resilience.
    """

    audit_finished = Signal(dict)
    update_available = Signal(str, str)
    status_message = Signal(str)

    def __init__(self, parent: Optional[QThread] = None):
        super().__init__(parent)
        self.staging_dir = os.path.abspath(os.path.join(os.getcwd(), ".syncframe_tmp", "updates"))

    def run(self) -> None:
        """Executes version probing and remote checks in background."""
        logger.info("Iniciando auditoria assíncrona de dependências e atualizações...")
        self.status_message.emit("Verificando versões das ferramentas locais...")

        audit_result: Dict[str, dict] = {
            "syncframe": {
                "local_version": CURRENT_SYNCFRAME_VERSION,
                "remote_version": CURRENT_SYNCFRAME_VERSION,
                "has_update": False,
            },
            "tools": {}
        }

        # 1. Probing local tools
        report = PreFlightChecker.verify_system_binaries()
        for tool, ver in report.tool_versions.items():
            audit_result["tools"][tool] = {
                "local_version": ver,
                "remote_version": "Up-to-date",
                "has_update": False,
            }

        # 2. Remote check for SyncFrame via GitHub API (non-blocking with 3s timeout)
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/i9Yuri/SyncFrame/releases/latest",
                headers={"User-Agent": "SyncFrame-Updater/1.2.0"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    remote_tag = data.get("tag_name", "").lstrip("v").strip()
                    if remote_tag:
                        audit_result["syncframe"]["remote_version"] = remote_tag
                        if remote_tag != CURRENT_SYNCFRAME_VERSION:
                            audit_result["syncframe"]["has_update"] = True
                            self.update_available.emit("SyncFrame", remote_tag)
                            self._stage_update_notice("SyncFrame", remote_tag)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            logger.info("Verificação remota ignorada (offline ou timeout): %s", exc)
            self.status_message.emit("Verificação remota ignorada: offline")
        except Exception as exc:
            logger.debug("Falha na checagem de release do SyncFrame: %s", exc)

        # 3. Optional local package updates check (dnf check-update)
        if shutil.which("dnf"):
            try:
                # dnf check-update returns 100 if updates exist, 0 if clean
                res = subprocess.run(
                    ["dnf", "check-update", "ffmpeg", "mkvtoolnix", "mpv", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=4.0
                )
                if res.returncode == 100:
                    out = res.stdout.strip()
                    for pkg in ["ffmpeg", "mkvtoolnix", "mpv"]:
                        if pkg in out:
                            tool_name = "mkvmerge" if pkg == "mkvtoolnix" else pkg
                            if tool_name in audit_result["tools"]:
                                audit_result["tools"][tool_name]["has_update"] = True
                                self.update_available.emit(tool_name, "Nova versão no repositório")
            except Exception:
                pass

        has_any_update = (
            audit_result["syncframe"]["has_update"]
            or any(t.get("has_update") for t in audit_result["tools"].values())
        )

        if has_any_update:
            msg = "Atualização disponível para um ou mais componentes do sistema."
        else:
            msg = "Todas as ferramentas e componentes estão na versão mais recente."

        self.status_message.emit(msg)
        self.audit_finished.emit(audit_result)
        logger.info("Auditoria assíncrona finalizada: has_update=%s", has_any_update)

    def _stage_update_notice(self, item: str, version: str) -> None:
        """Writes staging notice into .syncframe_tmp/updates/ without blocking."""
        try:
            os.makedirs(self.staging_dir, exist_ok=True)
            notice_path = os.path.join(self.staging_dir, f"{item.lower()}_update.json")
            with open(notice_path, "w", encoding="utf-8") as f:
                json.dump({"item": item, "version": version}, f)
        except Exception as exc:
            logger.debug("Erro ao criar staging de atualização: %s", exc)
