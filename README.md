# CyberLab

A Python/PyQt6 desktop application for guided cybersecurity training. Users log in, select scenarios at varying difficulty levels, and work inside live VirtualBox VMs that are managed automatically through Vagrant. Progress is tracked per user in a local SQLite database.

---

## Project Structure

```
Capstone/
├── main.py                  # Entry point
├── config.json              # Vagrant home path override
├── core/
│   ├── data.py              # Scenario and learning module definitions
│   ├── database.py          # SQLite user/progress persistence
│   ├── progress.py          # Progress tracking helpers
│   ├── vagrant_manager.py   # Vagrant VM lifecycle (up/halt/destroy)
│   └── vm_manager.py        # VirtualBox VM registration/snapshot restore
├── UI/
│   ├── main_window.py       # App shell and navigation
│   ├── login_view.py        # Login / registration screen
│   ├── scenario_view_v2.py  # Scenario browser and launcher
│   ├── learning_view.py     # Learning modules browser
│   ├── lesson_view.py       # Individual lesson content
│   ├── profile_view.py      # User profile and stats
│   ├── flag_dialog.py       # Flag submission dialog
│   ├── vm_embed.py          # Embedded VM display
│   ├── vm_storage_dialog.py # ISO/box storage management
│   └── widgets.py           # Shared UI components
├── utils/
│   └── styles.py            # Global stylesheet
└── scenarios/
    ├── beginner-1/Vagrantfile
    └── beginner-2/Vagrantfile
```

---

## Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.11+ | https://python.org |
| PyQt6 | latest | `pip install PyQt6` |
| VirtualBox | 7.x | https://virtualbox.org |
| Vagrant | 2.4+ | https://vagrantup.com |

---

## Setup

```bash
# 1. Clone the repo and enter the project directory
cd Capstone

# 2. Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows
# source venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install PyQt6

# 4. Run the app
python main.py
```

---

## Scenarios

| ID | Name | Difficulty | VMs |
|----|------|-----------|-----|
| beginner-1 | Command Line Basics | Beginner | Linux Kali |
| beginner-2 | Network Fundamentals | Beginner | Linux Ubuntu |
| intermediate-1 | Web Application Security | Intermediate | Windows 11, Linux Kali |
| intermediate-2 | Password Cracking | Intermediate | Linux Kali, Linux Ubuntu |
| hard-1 | Metasploit Exploitation | Hard | Windows 11, Linux Kali, Linux Ubuntu |

Each scenario restores a pre-configured VM snapshot so the environment is always in a known state. A flag must be captured to mark the scenario complete.

### Flags (development reference)

| Scenario | Flag | Hint |
|---------|------|------|
| beginner-1 | `CL-BASICS-COMPLETE` | List all files including hidden ones in `~/practice`, then read `.hidden_flag` |
| beginner-2 | `NET-FUND-COMPLETE` | `curl http://localhost:8080/flag.txt` |
| intermediate-1 | `WEBAPP-SEC-COMPLETE` | Exploit DVWA, then read `/var/www/html/flag.txt` on Windows |
| intermediate-2 | `PASS-CRACK-COMPLETE` | Crack hashes in `~/hashes`, SSH into Ubuntu as `victim`, read `~/flag.txt` |
| hard-1 | `MSF-EXPLOIT-COMPLETE` | Exploit Ubuntu or Windows via Metasploit, read `/root/proof.txt` |

---

## VM Setup

### Linux / Kali boxes

These are pulled automatically from Vagrant Cloud on first `vagrant up`:

| VM | Vagrant box |
|----|------------|
| Linux Kali | `kalilinux/rolling` |
| Linux Ubuntu | `ubuntu/jammy64` |

First boot downloads ~2–4 GB. Subsequent starts are instant.

### Windows 11 box (one-time manual step)

Microsoft does not permit redistribution of Windows images, so the box must be added manually.

**Option A — Export your own VM (recommended)**

1. Install Windows 11 in VirtualBox manually (or use an existing VM).
2. Install VirtualBox Guest Additions inside Windows.
3. Enable WinRM so Vagrant can communicate (run in Windows as Administrator):

```powershell
winrm quickconfig -q
winrm set winrm/config/winrs '@{MaxMemoryPerShellMB="512"}'
winrm set winrm/config '@{MaxTimeoutms="1800000"}'
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
winrm set winrm/config/service/auth '@{Basic="true"}'
```

4. Package and register the box:

```bash
vagrant package --base "Your VirtualBox VM Name" --output windows11.box
vagrant box add cyberlab/windows11 windows11.box
```

**Option B — Use a shared network box**

```bash
vagrant box add cyberlab/windows11 http://your-server/windows11.box
```

**Verify:**

```bash
vagrant box list
# Should include: cyberlab/windows11
```

---

## Quick Start (manual Vagrant use)

The app manages VMs automatically via the Start/Stop buttons. Use these commands only if you want to interact with VMs outside the app.

```bash
# Start all VMs for a scenario
cd scenarios/beginner-1
vagrant up

# Check status
vagrant status

# Stop all VMs
vagrant halt

# Destroy and start fresh
vagrant destroy -f && vagrant up
```

---

## Network Layout

Each scenario uses an isolated private network.

| Scenario | Network | IPs |
|---------|---------|-----|
| beginner-1 | 192.168.56.0/24 | Kali .10 |
| beginner-2 | 192.168.56.0/24 | Ubuntu .20 |
| intermediate-1 | 192.168.57.0/24 | Kali .10, Win11 .20 |
| intermediate-2 | 192.168.58.0/24 | Kali .10, Ubuntu .20 |
| hard-1 | 192.168.59.0/24 | Kali .10, Ubuntu .20, Win11 .30 |

---

## VM Name Registration

After running the app once, check the console for:

```
[VMManager] Registered VMs: [...]
```

Copy those names into `core/data.py` under each scenario's `'vms'` list if they differ from the defaults.

---

## Taking Snapshots

Run these commands after provisioning each VM and verifying the scenario environment is ready. The `--pause` flag ensures a consistent snapshot state.

```bash
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
```
