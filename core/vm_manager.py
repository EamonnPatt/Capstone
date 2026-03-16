"""
VM Manager - Handles VirtualBox VM operations including snapshot management
"""

import subprocess
import platform
import time


class VMManager:
    """Manages virtual machine operations using VirtualBox"""

    def __init__(self):
        self.vbox_manage = self._get_vboxmanage_path()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _get_vboxmanage_path(self):
        """Get the VBoxManage executable path based on OS"""
        system = platform.system()

        if system == "Windows":
            paths = [
                r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
                r"C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe",
            ]
            for path in paths:
                try:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return path
                except Exception:
                    continue
            return "VBoxManage.exe"
        else:
            return "VBoxManage"

    # ------------------------------------------------------------------
    # VM Listing & Info
    # ------------------------------------------------------------------

    def list_vms(self):
        """List all VirtualBox VMs"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'list', 'vms'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                print(f"Error listing VMs: {result.stderr}")
                return []
            vms = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    name = line.split('"')[1] if '"' in line else line
                    vms.append(name)
            return vms
        except FileNotFoundError:
            print("VBoxManage not found. Is VirtualBox installed?")
            return []
        except Exception as e:
            print(f"Error listing VMs: {e}")
            return []

    def get_vm_state(self, vm_name):
        """Get the current state of a VM"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'showvminfo', vm_name, '--machinereadable'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return "unknown"
            for line in result.stdout.split('\n'):
                if line.startswith('VMState='):
                    return line.split('=')[1].strip('"')
            return "unknown"
        except Exception as e:
            print(f"Error getting VM state: {e}")
            return "unknown"

    def get_vm_info(self, vm_name):
        """Get detailed VM information as a dict"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'showvminfo', vm_name, '--machinereadable'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return {}
            info = {}
            for line in result.stdout.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key] = value.strip('"')
            return info
        except Exception as e:
            print(f"Error getting VM info: {e}")
            return {}

    def vm_exists(self, vm_name):
        """Check if a VM exists in VirtualBox"""
        return vm_name in self.list_vms()

    # ------------------------------------------------------------------
    # Basic VM Control
    # ------------------------------------------------------------------

    def start_vm(self, vm_name, headless=False):
        """Start a VM (GUI mode by default so the user can see it)"""
        try:
            vm_type = 'headless' if headless else 'gui'
            result = subprocess.run(
                [self.vbox_manage, 'startvm', vm_name, '--type', vm_type],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                print(f"Error starting VM '{vm_name}': {result.stderr}")
                return False
            print(f"VM '{vm_name}' started successfully")
            return True
        except Exception as e:
            print(f"Error starting VM: {e}")
            return False

    def stop_vm(self, vm_name, force=False):
        """Stop a VM via ACPI power button (or force poweroff)"""
        try:
            command = 'poweroff' if force else 'acpipowerbutton'
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, command],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                print(f"Error stopping VM '{vm_name}': {result.stderr}")
                return False
            print(f"VM '{vm_name}' stopped")
            return True
        except Exception as e:
            print(f"Error stopping VM: {e}")
            return False

    def pause_vm(self, vm_name):
        """Pause a running VM"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, 'pause'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error pausing VM: {e}")
            return False

    def resume_vm(self, vm_name):
        """Resume a paused VM"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, 'resume'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error resuming VM: {e}")
            return False

    def reset_vm(self, vm_name):
        """Hard reset a VM"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, 'reset'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error resetting VM: {e}")
            return False

    # ------------------------------------------------------------------
    # Snapshot Management
    # ------------------------------------------------------------------

    def list_snapshots(self, vm_name):
        """
        Return a list of snapshot names for a given VM.
        Returns [] if the VM has no snapshots or doesn't exist.
        """
        try:
            result = subprocess.run(
                [self.vbox_manage, 'snapshot', vm_name, 'list', '--machinereadable'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                # "This machine does not have any snapshots" is returncode 1
                return []
            snapshots = []
            for line in result.stdout.split('\n'):
                # Lines look like: SnapshotName="scenario-webapp-kali"
                if line.startswith('SnapshotName='):
                    name = line.split('=', 1)[1].strip('"')
                    snapshots.append(name)
            return snapshots
        except Exception as e:
            print(f"Error listing snapshots for '{vm_name}': {e}")
            return []

    def snapshot_exists(self, vm_name, snapshot_name):
        """Check whether a named snapshot exists for a VM"""
        return snapshot_name in self.list_snapshots(vm_name)

    def take_snapshot(self, vm_name, snapshot_name, description=""):
        """
        Take a snapshot of a VM with the given name.
        The VM can be running or powered off.
        If running, pass --pause to freeze it while snapshotting.
        """
        try:
            cmd = [self.vbox_manage, 'snapshot', vm_name, 'take', snapshot_name]
            if description:
                cmd += ['--description', description]
            # --pause only works on a running VM; ignore error if already stopped
            cmd.append('--pause')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                # Retry without --pause (VM was probably already stopped)
                cmd.remove('--pause')
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"Error taking snapshot '{snapshot_name}': {result.stderr}")
                return False
            print(f"Snapshot '{snapshot_name}' taken for VM '{vm_name}'")
            return True
        except Exception as e:
            print(f"Error taking snapshot: {e}")
            return False

    def restore_snapshot(self, vm_name, snapshot_name):
        """
        Restore a VM to a named snapshot.
        The VM must be powered off first — this method handles that automatically.
        Returns True on success, False on failure.
        """
        # Power off the VM if it's running
        state = self.get_vm_state(vm_name)
        if state in ('running', 'paused', 'saved'):
            print(f"Powering off '{vm_name}' before restoring snapshot...")
            self.stop_vm(vm_name, force=True)
            # Give VirtualBox a moment to fully shut down
            time.sleep(3)

        try:
            result = subprocess.run(
                [self.vbox_manage, 'snapshot', vm_name, 'restore', snapshot_name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                print(f"Error restoring snapshot '{snapshot_name}' on '{vm_name}': {result.stderr}")
                return False
            print(f"Snapshot '{snapshot_name}' restored on '{vm_name}'")
            return True
        except Exception as e:
            print(f"Error restoring snapshot: {e}")
            return False

    def delete_snapshot(self, vm_name, snapshot_name):
        """Delete a named snapshot (does NOT delete the VM or its disk)"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'snapshot', vm_name, 'delete', snapshot_name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                print(f"Error deleting snapshot '{snapshot_name}': {result.stderr}")
                return False
            print(f"Snapshot '{snapshot_name}' deleted from '{vm_name}'")
            return True
        except Exception as e:
            print(f"Error deleting snapshot: {e}")
            return False

    # ------------------------------------------------------------------
    # Scenario Launch (the main new workflow)
    # ------------------------------------------------------------------

    def launch_scenario_vm(self, vm_name, snapshot_name=None):
        """
        Launch a VM for a scenario:
          1. If a snapshot name is provided, restore it first.
          2. Start the VM in GUI mode so the user can see the pre-configured state.

        Returns (success: bool, message: str)
        """
        if snapshot_name:
            # Verify snapshot exists before trying
            if not self.snapshot_exists(vm_name, snapshot_name):
                msg = (
                    f"Snapshot '{snapshot_name}' not found on VM '{vm_name}'.\n\n"
                    f"You need to create this snapshot first:\n"
                    f"  1. Boot '{vm_name}' and configure the desired state\n"
                    f"  2. Run: VBoxManage snapshot \"{vm_name}\" take \"{snapshot_name}\" --pause\n"
                    f"  3. Try launching again"
                )
                print(msg)
                return False, msg

            print(f"Restoring snapshot '{snapshot_name}' on '{vm_name}'...")
            if not self.restore_snapshot(vm_name, snapshot_name):
                msg = f"Failed to restore snapshot '{snapshot_name}' on '{vm_name}'."
                return False, msg

        # Start the VM in GUI mode
        print(f"Starting '{vm_name}' in GUI mode...")
        if not self.start_vm(vm_name, headless=False):
            msg = f"Failed to start VM '{vm_name}'."
            return False, msg

        return True, f"VM '{vm_name}' launched successfully."

    def launch_scenario(self, scenario):
        """
        Launch all VMs for a scenario, restoring their respective snapshots.

        scenario dict must have:
          'vms'       : list of VM names
          'snapshots' : dict mapping vm_name -> snapshot_name  (optional per VM)

        Returns a list of (vm_name, success, message) tuples.
        """
        snapshots = scenario.get('snapshots', {})
        results = []

        for vm_name in scenario.get('vms', []):
            snapshot_name = snapshots.get(vm_name)
            success, message = self.launch_scenario_vm(vm_name, snapshot_name)
            results.append((vm_name, success, message))

        return results