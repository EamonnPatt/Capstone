CyberLab ISO Storage
=====================

Place your virtual machine ISO files in this folder.

Recommended ISOs for each scenario:
-------------------------------------

  Kali Linux   → https://www.kali.org/get-kali/#kali-virtual-machines
                 Filename example: kali-linux-2024.4-virtualbox-amd64.iso

  Ubuntu       → https://ubuntu.com/download/server
                 Filename example: ubuntu-24.04-live-server-amd64.iso

  Windows 11   → https://www.microsoft.com/software-download/windows11
                 Filename example: Win11_23H2_English_x64.iso

How to use an ISO to create a VM in VirtualBox:
------------------------------------------------
  1. Open VirtualBox
  2. Click "New"
  3. Set the name (must match the name in core/data.py)
  4. Under "ISO Image", browse to this folder and select your ISO
  5. Complete the wizard and start the VM to install the OS

Tip:
----
  After running the app once, check the console output for:
    [VMManager] Registered VMs: [...]
  This shows the exact VM names VirtualBox knows about.
  Copy those names into core/data.py under each scenario's 'vms' list.