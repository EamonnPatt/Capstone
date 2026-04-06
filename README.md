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


  CyberLab — Scenario Vagrantfiles
Each subdirectory here maps 1-to-1 with a scenario ID in core/data.py
and contains a Vagrantfile that defines all VMs for that scenario.
scenarios/
  beginner-1/     Vagrantfile   # Kali Linux only
  beginner-2/     Vagrantfile   # Ubuntu only
  intermediate-1/ Vagrantfile   # Windows 11 + Kali
  intermediate-2/ Vagrantfile   # Kali + Ubuntu
  hard-1/         Vagrantfile   # Kali + Ubuntu + Windows 11
Prerequisites
ToolDownloadNotesVirtualBoxhttps://virtualbox.org7.x recommendedVagranthttps://vagrantup.com2.4+
Linux / Kali boxes
These are pulled automatically from Vagrant Cloud on first vagrant up:
Display nameVagrant boxLinux Kalikalilinux/rollingLinux Ubuntuubuntu/jammy64
First boot downloads ~2–4 GB. Subsequent starts are instant.
Windows 11 box (manual step — required once)
Microsoft does not permit redistribution of Windows images, so the
Windows 11 box cannot be downloaded automatically.
Option A — Export your own VM (recommended for a lab setting)

Install Windows 11 in VirtualBox manually (or use an existing VM).
Install the VirtualBox Guest Additions inside Windows.
Enable WinRM so Vagrant can communicate:

powershell   # Run in Windows as Administrator
   winrm quickconfig -q
   winrm set winrm/config/winrs '@{MaxMemoryPerShellMB="512"}'
   winrm set winrm/config '@{MaxTimeoutms="1800000"}'
   winrm set winrm/config/service '@{AllowUnencrypted="true"}'
   winrm set winrm/config/service/auth '@{Basic="true"}'

Package and register the box:

bash   vagrant package --base "Your VirtualBox VM Name" --output windows11.box
   vagrant box add cyberlab/windows11 windows11.box
Option B — Use a shared network box
If your institution hosts a box internally:
bashvagrant box add cyberlab/windows11 http://your-server/windows11.box
Verify
bashvagrant box list
# Should include: cyberlab/windows11
Quick start
bash# Start all VMs for a scenario
cd scenarios/beginner-1
vagrant up

# Check status
vagrant status

# Stop all VMs
vagrant halt

# Destroy and start fresh
vagrant destroy -f && vagrant up
The CyberLab app handles all of this for you via the Start / Stop buttons.
vagrant up is only needed manually if you want to interact with the VMs
outside the app.
Network layout
Each scenario uses an isolated private network so VMs can reach each other
but are isolated from other scenarios.
ScenarioNetworkIPs assignedbeginner-1192.168.56.0/24Kali .10beginner-2192.168.56.0/24Ubuntu .20intermediate-1192.168.57.0/24Kali .10, Win11 .20intermediate-2192.168.58.0/24Kali .10, Ubuntu .20hard-1192.168.59.0/24Kali .10, Ubuntu .20, Win11 .30






# beginner-1
VBoxManage snapshot "cyberlab-beginner1-kali" take "scenario-cmdline-kali" --pause

# beginner-2
VBoxManage snapshot "cyberlab-beginner2-ubuntu" take "scenario-networking-ubuntu" --pause

# intermediate-1
VBoxManage snapshot "cyberlab-intermediate1-windows11" take "scenario-webapp-win11" --pause
VBoxManage snapshot "cyberlab-intermediate1-kali" take "scenario-webapp-kali" --pause

# intermediate-2
VBoxManage snapshot "cyberlab-intermediate2-kali" take "scenario-passwords-kali" --pause
VBoxManage snapshot "cyberlab-intermediate2-ubuntu" take "scenario-passwords-ubuntu" --pause

# hard-1
VBoxManage snapshot "cyberlab-hard1-windows11" take "scenario-msf-win11" --pause
VBoxManage snapshot "cyberlab-hard1-kali" take "scenario-msf-kali" --pause
VBoxManage snapshot "cyberlab-hard1-ubuntu" take "scenario-msf-ubuntu" --pause








add a score taker where the user can add the "flag" from the scenario to test if they got it right and if they did they "complete" the scenario and it gets saved to their profile. 

add the ability to go fullscreen on just the vm

add the snapshots for the rest of the scenarios

integrate joels code