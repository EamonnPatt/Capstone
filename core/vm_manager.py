"""
VM Manager - Handles VirtualBox VM operations
Runs all VM operations in background threads to keep UI responsive.
"""

import subprocess
import platform
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QObject


# ---------------------------------------------------------------------------
# ISO folder – always at <project root>/isos/
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ISO_FOLDER = PROJECT_ROOT / "isos"


def get_iso_folder() -> Path:
    """Return the project-local ISO folder, creating it if missing."""
    ISO_FOLDER.mkdir(exist_ok=True)
    return ISO_FOLDER


def list_isos() -> list:
    """Return filenames of all ISO files found in the isos/ folder."""
    return [f.name for f in sorted(get_iso_folder().glob("*.iso"))]


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

class VMWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, vbox_manage, args, parent=None):
        super().__init__(parent)
        self.vbox_manage = vbox_manage
        self.args = args

    def run(self):
        try:
            result = subprocess.run(
                [self.vbox_manage] + self.args,
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                self.finished.emit(True, result.stdout.strip())
            else:
                self.finished.emit(False, result.stderr.strip() or "Unknown error")
        except FileNotFoundError:
            self.finished.emit(False, "VBoxManage not found. Is VirtualBox installed?")
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Operation timed out after 60 seconds.")
        except Exception as e:
            self.finished.emit(False, str(e))


# ---------------------------------------------------------------------------
# State poller
# ---------------------------------------------------------------------------

class VMStatePoller(QThread):
    state_ready = pyqtSignal(str)

    def __init__(self, vbox_manage, vm_name, parent=None):
        super().__init__(parent)
        self.vbox_manage = vbox_manage
        self.vm_name = vm_name

    def run(self):
        try:
            result = subprocess.run(
                [self.vbox_manage, 'showvminfo', self.vm_name, '--machinereadable'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                self.state_ready.emit("unknown")
                return
            for line in result.stdout.split('\n'):
                if line.startswith('VMState='):
                    self.state_ready.emit(line.split('=')[1].strip('"'))
                    return
            self.state_ready.emit("unknown")
        except Exception:
            self.state_ready.emit("unknown")


# ---------------------------------------------------------------------------
# VMManager
# ---------------------------------------------------------------------------

class VMManager(QObject):
    """Manages virtual machine operations using VirtualBox."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vbox_manage = self._get_vboxmanage_path()
        self._workers = []
        self._vm_cache = []

        if self.is_available():
            self._vm_cache = self.list_vms()
            print(f"[VMManager] VirtualBox found: {self.vbox_manage}")
            print(f"[VMManager] Registered VMs: {self._vm_cache}")
            print(f"[VMManager] ISO folder: {get_iso_folder()}")
            isos = list_isos()
            print(f"[VMManager] ISOs found: {isos}" if isos else
                  f"[VMManager] No ISOs in {get_iso_folder()} — add .iso files there.")
        else:
            print("[VMManager] WARNING: VBoxManage not found. Install VirtualBox.")

    def _get_vboxmanage_path(self):
        if platform.system() == "Windows":
            for path in [
                r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
                r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
            ]:
                try:
                    r = subprocess.run([path, "--version"], capture_output=True, timeout=5)
                    if r.returncode == 0:
                        return path
                except Exception:
                    continue
            return "VBoxManage.exe"
        return "VBoxManage"

    def is_available(self):
        try:
            return subprocess.run(
                [self.vbox_manage, "--version"],
                capture_output=True, timeout=5
            ).returncode == 0
        except Exception:
            return False

    def list_vms(self):
        """Return all VM names registered in VirtualBox."""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'list', 'vms'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
            vms = []
            for line in result.stdout.strip().split('\n'):
                if '"' in line:
                    name = line.split('"')[1]
                    if name:
                        vms.append(name)
            self._vm_cache = vms
            return vms
        except Exception as e:
            print(f"[VMManager] list_vms error: {e}")
            return []

    def resolve_vm_name(self, name_hint):
        """
        Fuzzy-match a friendly name (e.g. "Linux Kali") against the actual
        registered VirtualBox VM names.

        Priority:
          1. Exact match
          2. Case-insensitive exact
          3. All hint words found in VM name
          4. Any hint word found in VM name

        Returns the matched VM name, or None if nothing found.
        Logs the mapping so you can see what got resolved in the console.
        """
        vms = self._vm_cache or self.list_vms()
        if not vms:
            return None

        hint_lower = name_hint.lower()
        hint_words = hint_lower.split()

        # 1. Exact
        if name_hint in vms:
            return name_hint

        # 2. Case-insensitive exact
        for vm in vms:
            if vm.lower() == hint_lower:
                print(f"[VMManager] Resolved '{name_hint}' → '{vm}'")
                return vm

        # 3. All words present
        for vm in vms:
            if all(w in vm.lower() for w in hint_words):
                print(f"[VMManager] Resolved '{name_hint}' → '{vm}'")
                return vm

        # 4. Any word present
        for vm in vms:
            if any(w in vm.lower() for w in hint_words):
                print(f"[VMManager] Resolved '{name_hint}' → '{vm}' (partial match)")
                return vm

        print(f"[VMManager] WARNING: No VM found matching '{name_hint}'. "
              f"Available VMs: {vms}")
        return None

    def get_vm_state(self, vm_name):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        try:
            result = subprocess.run(
                [self.vbox_manage, 'showvminfo', resolved, '--machinereadable'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return "unknown"
            for line in result.stdout.split('\n'):
                if line.startswith('VMState='):
                    return line.split('=')[1].strip('"')
            return "unknown"
        except Exception as e:
            print(f"[VMManager] get_vm_state error: {e}")
            return "unknown"

    def vm_exists(self, vm_name):
        return self.resolve_vm_name(vm_name) is not None

    # ------------------------------------------------------------------
    # Async operations
    # ------------------------------------------------------------------

    def _make_worker(self, args):
        worker = VMWorker(self.vbox_manage, args)
        self._workers.append(worker)
        worker.finished.connect(lambda *_: self._cleanup_worker(worker))
        return worker

    def _cleanup_worker(self, worker):
        try:
            self._workers.remove(worker)
        except ValueError:
            pass

    def start_vm_async(self, vm_name, headless=False):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        return self._make_worker(['startvm', resolved, '--type', 'headless' if headless else 'gui'])

    def stop_vm_async(self, vm_name, force=False):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        return self._make_worker(['controlvm', resolved, 'poweroff' if force else 'acpipowerbutton'])

    def pause_vm_async(self, vm_name):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        return self._make_worker(['controlvm', resolved, 'pause'])

    def resume_vm_async(self, vm_name):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        return self._make_worker(['controlvm', resolved, 'resume'])

    def reset_vm_async(self, vm_name):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        return self._make_worker(['controlvm', resolved, 'reset'])

    def poll_state_async(self, vm_name):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        return VMStatePoller(self.vbox_manage, resolved)

    # ------------------------------------------------------------------
    # Sync versions (backward compat)
    # ------------------------------------------------------------------

    def start_vm(self, vm_name, headless=False):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        try:
            r = subprocess.run(
                [self.vbox_manage, 'startvm', resolved, '--type', 'headless' if headless else 'gui'],
                capture_output=True, text=True, timeout=30
            )
            return r.returncode == 0
        except Exception as e:
            print(f"[VMManager] start_vm error: {e}")
            return False

    def stop_vm(self, vm_name, force=False):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        try:
            r = subprocess.run(
                [self.vbox_manage, 'controlvm', resolved, 'poweroff' if force else 'acpipowerbutton'],
                capture_output=True, text=True, timeout=30
            )
            return r.returncode == 0
        except Exception as e:
            print(f"[VMManager] stop_vm error: {e}")
            return False

    def get_vm_info(self, vm_name):
        resolved = self.resolve_vm_name(vm_name) or vm_name
        try:
            r = subprocess.run(
                [self.vbox_manage, 'showvminfo', resolved, '--machinereadable'],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode != 0:
                return {}
            info = {}
            for line in r.stdout.split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    info[k] = v.strip('"')
            return info
        except Exception as e:
            print(f"[VMManager] get_vm_info error: {e}")
            return {}