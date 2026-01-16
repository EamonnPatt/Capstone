"""
VM Manager - Handles VirtualBox VM operations
"""

import subprocess
import platform


class VMManager:
    """Manages virtual machine operations using VirtualBox"""
    
    def __init__(self):
        self.vbox_manage = self._get_vboxmanage_path()
    
    def _get_vboxmanage_path(self):
        """Get the VBoxManage executable path based on OS"""
        system = platform.system()
        
        if system == "Windows":
            # Try common Windows paths
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
                except:
                    continue
            return "VBoxManage.exe"  # Fallback to PATH
        else:
            # Linux/Mac - should be in PATH
            return "VBoxManage"
    
    def list_vms(self):
        """List all VirtualBox VMs"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'list', 'vms'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"Error listing VMs: {result.stderr}")
                return []
            
            vms = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Parse: "VM Name" {uuid}
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
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"Error getting VM state: {result.stderr}")
                return "unknown"
            
            for line in result.stdout.split('\n'):
                if line.startswith('VMState='):
                    state = line.split('=')[1].strip('"')
                    return state
            return "unknown"
        except Exception as e:
            print(f"Error getting VM state: {e}")
            return "unknown"
    
    def start_vm(self, vm_name, headless=True):
        """Start a VM"""
        try:
            vm_type = 'headless' if headless else 'gui'
            result = subprocess.run(
                [self.vbox_manage, 'startvm', vm_name, '--type', vm_type],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Error starting VM: {result.stderr}")
                return False
            
            print(f"VM '{vm_name}' started successfully")
            return True
        except Exception as e:
            print(f"Error starting VM: {e}")
            return False
    
    def stop_vm(self, vm_name, force=False):
        """Stop a VM"""
        try:
            command = 'poweroff' if force else 'acpipowerbutton'
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Error stopping VM: {result.stderr}")
                return False
            
            print(f"VM '{vm_name}' stopped successfully")
            return True
        except Exception as e:
            print(f"Error stopping VM: {e}")
            return False
    
    def pause_vm(self, vm_name):
        """Pause a VM"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, 'pause'],
                capture_output=True,
                text=True,
                timeout=10
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
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error resuming VM: {e}")
            return False
    
    def reset_vm(self, vm_name):
        """Reset (restart) a VM"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'controlvm', vm_name, 'reset'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error resetting VM: {e}")
            return False
    
    def get_vm_info(self, vm_name):
        """Get detailed VM information"""
        try:
            result = subprocess.run(
                [self.vbox_manage, 'showvminfo', vm_name, '--machinereadable'],
                capture_output=True,
                text=True,
                timeout=10
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
        """Check if a VM exists"""
        vms = self.list_vms()
        return vm_name in vms