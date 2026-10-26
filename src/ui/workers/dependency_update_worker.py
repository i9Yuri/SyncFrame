"""Background low-priority worker auditing local and remote versions of tools and SyncFrame."""

import json
import logging
import os
import shutil
import subprocess
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QThread, Signal

from ...utils.system_check import PreFlightChecker

logger = logging.getLogger(__name__)

CURRENT_SYNCFRAME_VERSION = "2.0.0"


def parse_semantic_version(v: str) -> Tuple[int, ...]:
    """Parses a version string like '1.5.0', 'v1.2.0', '1.0.0-rc1' into a comparable tuple of ints."""
    if not v:
        return (0, 0, 0)
    clean = v.lower().lstrip("v").strip()
    parts: List[int] = []
    for chunk in clean.split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


class DependencyUpdateWorker(QThread):
    """
    Asynchronous low-priority worker querying and applying updates for dependencies and SyncFrame.
    Performs background audits and automated updates with zero UI thread contention and offline resilience.
    """

    audit_finished = Signal(dict)
    update_available = Signal(str, str)
    status_message = Signal(str)
    update_progress = Signal(str, int)
    update_completed = Signal(str, bool, str)

    def __init__(
        self,
        parent: Optional[QThread] = None,
        auto_apply: bool = True,
        target_repo_dir: Optional[str] = None
    ):
        super().__init__(parent)
        self.auto_apply = auto_apply
        self.staging_dir = os.path.abspath(os.path.join(os.getcwd(), ".syncframe_tmp", "updates"))
        if target_repo_dir:
            self.repo_dir = target_repo_dir
        else:
            self.repo_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..")
            )

    def run(self) -> None:
        """Executes version probing and performs actual updates if any are found."""
        logger.info("Iniciando auditoria assíncrona de dependências e atualizações...")
        self.status_message.emit("Verificando versões das ferramentas locais...")

        audit_result: Dict[str, dict] = {
            "syncframe": {
                "local_version": CURRENT_SYNCFRAME_VERSION,
                "remote_version": CURRENT_SYNCFRAME_VERSION,
                "has_update": False,
                "updated": False,
            },
            "tools": {},
            "tools_updated": False,
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
        github_release_data = None
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/i9Yuri/SyncFrame/releases/latest",
                headers={"User-Agent": f"SyncFrame-Updater/{CURRENT_SYNCFRAME_VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    github_release_data = json.loads(resp.read().decode("utf-8"))
                    remote_tag = github_release_data.get("tag_name", "").lstrip("v").strip()
                    if remote_tag:
                        audit_result["syncframe"]["remote_version"] = remote_tag
                        # Only flag update if remote version is strictly greater than local version
                        if parse_semantic_version(remote_tag) > parse_semantic_version(CURRENT_SYNCFRAME_VERSION):
                            audit_result["syncframe"]["has_update"] = True
                            audit_result["syncframe"]["update_type"] = "release"
                            audit_result["syncframe"]["release_data"] = github_release_data
                            self.update_available.emit("SyncFrame", remote_tag)
                            self._stage_update_notice("SyncFrame", remote_tag)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            logger.info("Verificação remota ignorada (offline ou timeout): %s", exc)
            self.status_message.emit("Verificação remota ignorada: offline")
        except Exception as exc:
            logger.debug("Falha na checagem de release do SyncFrame: %s", exc)

        # 3. Git upstream check (if running inside git clone and no newer release was flagged)
        git_bin = shutil.which("git")
        current_branch = "master"
        if not audit_result["syncframe"]["has_update"] and git_bin and os.path.isdir(os.path.join(self.repo_dir, ".git")):
            try:
                subprocess.run(
                    [git_bin, "fetch", "origin", "--quiet"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    timeout=4.0,
                    check=False
                )
                b_res = subprocess.run(
                    [git_bin, "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    check=False
                )
                current_branch = b_res.stdout.strip() or "master"
                c_res = subprocess.run(
                    [git_bin, "rev-list", "--count", f"HEAD..origin/{current_branch}"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    check=False
                )
                if c_res.returncode == 0:
                    commits_behind = int(c_res.stdout.strip() or "0")
                    if commits_behind > 0:
                        audit_result["syncframe"]["has_update"] = True
                        audit_result["syncframe"]["update_type"] = "git"
                        audit_result["syncframe"]["commits_behind"] = commits_behind
                        self.update_available.emit("SyncFrame", f"{commits_behind} novos commits no repositório")
                        self._stage_update_notice("SyncFrame", f"git+{commits_behind}")
            except Exception as exc:
                logger.debug("Falha na verificação de commits upstream no git: %s", exc)

        # 4. Optional local package updates check (dnf check-update)
        tools_to_update = []
        if shutil.which("dnf"):
            try:
                res = subprocess.run(
                    ["dnf", "check-update", "ffmpeg", "mkvtoolnix", "mpv", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=5.0
                )
                if res.returncode == 100:
                    out = res.stdout.strip()
                    for pkg in ["ffmpeg", "mkvtoolnix", "mpv"]:
                        if pkg in out:
                            tool_name = "mkvmerge" if pkg == "mkvtoolnix" else pkg
                            if tool_name in audit_result["tools"]:
                                audit_result["tools"][tool_name]["has_update"] = True
                                tools_to_update.append(pkg)
                                self.update_available.emit(tool_name, "Nova versão no repositório")
            except Exception:
                pass

        has_any_update = (
            audit_result["syncframe"]["has_update"]
            or any(t.get("has_update") for t in audit_result["tools"].values())
        )

        # 5. If updates exist and auto_apply is True, EXECUTE the update!
        if has_any_update and self.auto_apply:
            self.status_message.emit("Atualização detectada! Iniciando procedimento de atualização...")
            logger.info("Iniciando procedimento de atualização automática dos componentes...")

            # 5A. Update SyncFrame
            if audit_result["syncframe"]["has_update"]:
                update_type = audit_result["syncframe"].get("update_type")
                if update_type == "git" and git_bin:
                    self.status_message.emit("Executando git pull para atualizar o SyncFrame...")
                    try:
                        pull_res = subprocess.run(
                            [git_bin, "pull", "--ff-only", "origin", current_branch],
                            cwd=self.repo_dir,
                            capture_output=True,
                            text=True,
                            timeout=25.0
                        )
                        if pull_res.returncode == 0:
                            self.status_message.emit("SyncFrame atualizado com sucesso via repositório Git!")
                            audit_result["syncframe"]["updated"] = True
                            self.update_completed.emit("SyncFrame", True, "Repositório Git atualizado")
                        else:
                            err_msg = pull_res.stderr.strip() or pull_res.stdout.strip()
                            self.status_message.emit(f"Aviso ao executar git pull: {err_msg}")
                            self.update_completed.emit("SyncFrame", False, err_msg)
                    except Exception as exc:
                        self.status_message.emit(f"Falha ao executar git pull: {exc}")
                        self.update_completed.emit("SyncFrame", False, str(exc))

                elif update_type == "release":
                    remote_ver = audit_result["syncframe"]["remote_version"]
                    self.status_message.emit(f"Baixando pacote do SyncFrame (v{remote_ver})...")
                    try:
                        assets = audit_result["syncframe"].get("release_data", {}).get("assets", [])
                        download_url = None
                        for a in assets:
                            if a.get("name") == "SyncFrame":
                                download_url = a.get("browser_download_url")
                                break
                        if download_url:
                            os.makedirs(self.staging_dir, exist_ok=True)
                            dest_path = os.path.join(self.staging_dir, "SyncFrame")
                            urllib.request.urlretrieve(download_url, dest_path)
                            os.chmod(dest_path, 0o755)
                            self.status_message.emit(f"Binário v{remote_ver} baixado com sucesso em {dest_path}.")
                            audit_result["syncframe"]["updated"] = True
                            self.update_completed.emit("SyncFrame", True, f"Binário v{remote_ver} baixado")
                        else:
                            self.status_message.emit(f"Asset binário não encontrado para a release v{remote_ver}.")
                            self.update_completed.emit("SyncFrame", False, "Asset não encontrado")
                    except Exception as exc:
                        self.status_message.emit(f"Falha no download da release do SyncFrame: {exc}")
                        self.update_completed.emit("SyncFrame", False, str(exc))

            # 5B. Update system tools
            if tools_to_update and shutil.which("pkexec") and shutil.which("dnf"):
                pkgs_str = " ".join(tools_to_update)
                self.status_message.emit(f"Atualizando dependências do sistema ({pkgs_str})...")
                try:
                    up_res = subprocess.run(
                        ["pkexec", "dnf", "upgrade", "-y"] + tools_to_update,
                        capture_output=True,
                        text=True,
                        timeout=120.0
                    )
                    if up_res.returncode == 0:
                        self.status_message.emit("Ferramentas do sistema atualizadas com sucesso!")
                        audit_result["tools_updated"] = True
                        self.update_completed.emit("Ferramentas do sistema", True, "Atualizadas via dnf")
                    else:
                        self.status_message.emit("Atualização de ferramentas do sistema não concluída ou rejeitada.")
                        self.update_completed.emit("Ferramentas do sistema", False, "Rejeitada ou erro dnf")
                except Exception as exc:
                    self.status_message.emit(f"Erro ao atualizar ferramentas do sistema: {exc}")
                    self.update_completed.emit("Ferramentas do sistema", False, str(exc))

            was_updated = audit_result["syncframe"].get("updated") or audit_result.get("tools_updated")
            if was_updated:
                msg = "Atualização concluída com sucesso! Reinicie o aplicativo para aplicar as novidades."
            else:
                msg = "Tentativa de atualização finalizada. Verifique os registros para detalhes."
        elif has_any_update and not self.auto_apply:
            msg = "Atualização disponível para um ou mais componentes do sistema."
        else:
            self.status_message.emit(f"SyncFrame (v{CURRENT_SYNCFRAME_VERSION}) está na versão mais recente.")
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
