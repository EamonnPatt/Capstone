"""
Vagrant Manager - Handles VM provisioning via Vagrant
Sits alongside vm_manager.py; handles lifecycle before VBoxManage takes over.
"""

import json
import subprocess
import os
import platform
import threading
from pathlib import Path


# Map VM display names → Vagrant machine names (defined in Vagrantfiles)
VM_NAME_MAP = {
    "Linux Kali":   "kali",
    "Linux Ubuntu": "ubuntu",
    "Windows 11":   "windows11",
}

# Where scenario Vagrantfiles live, relative to project root
SCENARIOS_DIR = Path(__file__).parent.parent / "scenarios"
CONFIG_PATH   = Path(__file__).parent.parent / "config.json"


def _read_vagrant_home() -> str | None:
    """Read the configured VAGRANT_HOME from config.json."""
    try:
        return json.loads(CONFIG_PATH.read_text()).get("vagrant_home")
    except Exception:
        return None


def _get_vboxmanage() -> str:
    if platform.system() == "Windows":
        for p in [r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
                  r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe"]:
            if os.path.exists(p):
                return p
    return "VBoxManage"


def _set_vbox_machine_folder(folder: str):
    """Point VirtualBox's default VM folder to the chosen drive."""
    vbm = _get_vboxmanage()
    try:
        result = subprocess.run(
            [vbm, "setproperty", "machinefolder", folder],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"[VagrantManager] VirtualBox machine folder → {folder}")
        else:
            print(f"[VagrantManager] setproperty failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"[VagrantManager] Could not set VirtualBox machine folder: {e}")


class VagrantManager:
    """
    Manages Vagrant-based VM provisioning.
    Each scenario has its own subdirectory under /scenarios/ with a Vagrantfile.
    """

    def __init__(self):
        self.vagrant_path = self._find_vagrant()
        self._output_callbacks = {}   # scenario_id → callable(line: str)

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _find_vagrant(self) -> str:
        """Return the vagrant executable path."""
        if platform.system() == "Windows":
            candidates = [
                r"C:\HashiCorp\Vagrant\bin\vagrant.exe",
                r"C:\Program Files\Vagrant\bin\vagrant.exe",
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c
        return "vagrant"   # assume on PATH (Linux / macOS)

    def is_vagrant_installed(self) -> bool:
        try:
            result = subprocess.run(
                [self.vagrant_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_vagrant_version(self) -> str:
        try:
            result = subprocess.run(
                [self.vagrant_path, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except Exception:
            return "Not installed"

    # ------------------------------------------------------------------
    # Scenario directory helpers
    # ------------------------------------------------------------------

    def get_scenario_dir(self, scenario_id: str) -> Path:
        return SCENARIOS_DIR / scenario_id

    def scenario_has_vagrantfile(self, scenario_id: str) -> bool:
        return (self.get_scenario_dir(scenario_id) / "Vagrantfile").exists()

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_vm_status(self, scenario_id: str, vm_display_name: str) -> str:
        """
        Returns: 'running', 'poweroff', 'not created', 'saved', or 'unknown'
        """
        machine = VM_NAME_MAP.get(vm_display_name, vm_display_name.lower().replace(" ", "_"))
        scenario_dir = self.get_scenario_dir(scenario_id)

        if not scenario_dir.exists() or not self.scenario_has_vagrantfile(scenario_id):
            return "not created"

        try:
            result = subprocess.run(
                [self.vagrant_path, "status", machine, "--machine-readable"],
                capture_output=True, text=True, timeout=15,
                cwd=str(scenario_dir)
            )
            for line in result.stdout.splitlines():
                parts = line.split(",")
                # Format: timestamp,target,type,data
                if len(parts) >= 4 and parts[1] == machine and parts[2] == "state":
                    return parts[3].strip()
            return "unknown"
        except Exception as e:
            print(f"[VagrantManager] status error: {e}")
            return "unknown"

    def get_all_statuses(self, scenario_id: str) -> dict:
        """Return {machine_name: state} for all machines in a scenario."""
        scenario_dir = self.get_scenario_dir(scenario_id)
        statuses = {}

        if not scenario_dir.exists() or not self.scenario_has_vagrantfile(scenario_id):
            return statuses

        try:
            result = subprocess.run(
                [self.vagrant_path, "status", "--machine-readable"],
                capture_output=True, text=True, timeout=15,
                cwd=str(scenario_dir)
            )
            for line in result.stdout.splitlines():
                parts = line.split(",")
                if len(parts) >= 4 and parts[2] == "state":
                    statuses[parts[1]] = parts[3].strip()
        except Exception as e:
            print(f"[VagrantManager] all-statuses error: {e}")

        return statuses

    # ------------------------------------------------------------------
    # Lifecycle (blocking — wrap in thread for GUI use)
    # ------------------------------------------------------------------

    def _run_vagrant(self, scenario_id: str, args: list, output_cb=None) -> bool:
        """Run a vagrant command in the scenario directory, streaming output."""
        scenario_dir = self.get_scenario_dir(scenario_id)

        if not self.scenario_has_vagrantfile(scenario_id):
            msg = f"No Vagrantfile found for scenario '{scenario_id}' in {scenario_dir}"
            print(f"[VagrantManager] {msg}")
            if output_cb:
                output_cb(msg)
            return False

        cmd = [self.vagrant_path] + args

        env = os.environ.copy()
        vagrant_home = _read_vagrant_home()
        if vagrant_home:
            env["VAGRANT_HOME"] = vagrant_home
            print(f"[VagrantManager] VAGRANT_HOME={vagrant_home}")
            # Also redirect VirtualBox VM files to the same drive
            drive = Path(vagrant_home).anchor  # e.g. "D:\\"
            vbox_folder = str(Path(drive) / "VirtualBox VMs")
            _set_vbox_machine_folder(vbox_folder)

        try:
            process = subprocess.Popen(
                cmd, cwd=str(scenario_dir), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            for line in process.stdout:
                line = line.rstrip()
                print(f"[Vagrant:{scenario_id}] {line}")
                if output_cb:
                    output_cb(line)
            process.wait()
            return process.returncode == 0
        except FileNotFoundError:
            msg = "Vagrant not found. Please install Vagrant from https://www.vagrantup.com"
            print(f"[VagrantManager] {msg}")
            if output_cb:
                output_cb(msg)
            return False
        except Exception as e:
            print(f"[VagrantManager] run error: {e}")
            if output_cb:
                output_cb(str(e))
            return False

    def up(self, scenario_id: str, vm_display_name: str = None, output_cb=None) -> bool:
        """vagrant up [machine] — provision and start."""
        args = ["up"]
        if vm_display_name:
            args.append(VM_NAME_MAP.get(vm_display_name, vm_display_name))
        args += ["--no-color"]
        return self._run_vagrant(scenario_id, args, output_cb)

    def halt(self, scenario_id: str, vm_display_name: str = None, output_cb=None) -> bool:
        """vagrant halt [machine]"""
        args = ["halt"]
        if vm_display_name:
            args.append(VM_NAME_MAP.get(vm_display_name, vm_display_name))
        args += ["--no-color"]
        return self._run_vagrant(scenario_id, args, output_cb)

    def destroy(self, scenario_id: str, vm_display_name: str = None, output_cb=None) -> bool:
        """vagrant destroy -f [machine]"""
        args = ["destroy", "-f"]
        if vm_display_name:
            args.append(VM_NAME_MAP.get(vm_display_name, vm_display_name))
        return self._run_vagrant(scenario_id, args, output_cb)

    def reload(self, scenario_id: str, vm_display_name: str = None, output_cb=None) -> bool:
        """vagrant reload [machine] — restart with re-provisioning."""
        args = ["reload"]
        if vm_display_name:
            args.append(VM_NAME_MAP.get(vm_display_name, vm_display_name))
        args += ["--no-color"]
        return self._run_vagrant(scenario_id, args, output_cb)

    def snapshot_save(self, scenario_id: str, vm_display_name: str, name: str) -> bool:
        machine = VM_NAME_MAP.get(vm_display_name, vm_display_name)
        return self._run_vagrant(scenario_id, ["snapshot", "save", machine, name])

    def snapshot_restore(self, scenario_id: str, vm_display_name: str, name: str) -> bool:
        machine = VM_NAME_MAP.get(vm_display_name, vm_display_name)
        return self._run_vagrant(scenario_id, ["snapshot", "restore", machine, name])

    # ------------------------------------------------------------------
    # Async wrappers (non-blocking for GUI)
    # ------------------------------------------------------------------

    def up_async(self, scenario_id: str, vm_display_name: str = None,
                 output_cb=None, done_cb=None):
        def _worker():
            ok = self.up(scenario_id, vm_display_name, output_cb)
            if done_cb:
                done_cb(ok)
        threading.Thread(target=_worker, daemon=True).start()

    def halt_async(self, scenario_id: str, vm_display_name: str = None,
                   output_cb=None, done_cb=None):
        def _worker():
            ok = self.halt(scenario_id, vm_display_name, output_cb)
            if done_cb:
                done_cb(ok)
        threading.Thread(target=_worker, daemon=True).start()

    def destroy_async(self, scenario_id: str, vm_display_name: str = None,
                      output_cb=None, done_cb=None):
        def _worker():
            ok = self.destroy(scenario_id, vm_display_name, output_cb)
            if done_cb:
                done_cb(ok)
        threading.Thread(target=_worker, daemon=True).start()