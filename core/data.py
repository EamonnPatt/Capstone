"""
Data module - Stores scenarios, user data, and snapshot mappings
"""

# User data
USER_DATA = {
    'username': 'CyberStudent',
    'completed_scenarios': ['beginner-1'],
    'learning_modules_completed': 3
}

# Scenarios data
# Each VM entry in 'snapshots' maps a VM name to the VirtualBox snapshot name
# that should be restored when launching that scenario.
# Snapshot names must exactly match what you named them in VirtualBox.
#
# One-time setup per scenario:
#   1. Boot the base VM
#   2. Configure the desired state (open apps, position windows, etc.)
#   3. Run: VBoxManage snapshot "<VMName>" take "<snapshot-name>" --pause
#   4. Add that snapshot name here
SCENARIOS = [
    {
        'id': 'beginner-1',
        'name': 'Command Line Basics',
        'difficulty': 'Beginner',
        'description': 'Learn fundamental command line operations in a Linux environment. '
                       'A terminal is pre-opened with a practice directory ready to go.',
        'vms': ['Linux Kali'],
        # VirtualBox VM names as set by vb.name in each Vagrantfile
        'vbox_names': {
            'Linux Kali': 'cyberlab-beginner1-kali',
        },
        'snapshots': {
            # Kali boots with a terminal open in ~/practice, ls output visible
            'Linux Kali': 'scenario-cmdline-kali',
        },
        'launch_instructions': (
            'A terminal has been opened for you.\n'
            'Your working directory is ~/practice.\n'
            'Try: ls, pwd, cd, mkdir, and cat to get started.'
        ),
        # Flag hidden in ~/practice/.hidden_flag — found by running: cat .hidden_flag
        'flag': 'CL-BASICS-COMPLETE',
        'flag_hint': 'List all files including hidden ones in ~/practice, then read the hidden flag file.',
    },
    {
        'id': 'beginner-2',
        'name': 'Network Fundamentals',
        'difficulty': 'Beginner',
        'description': 'Explore basic networking concepts. '
                       'Wireshark and a terminal are ready to capture traffic.',
        'vms': ['Linux Ubuntu'],
        'vbox_names': {
            'Linux Ubuntu': 'cyberlab-beginner2-ubuntu',
        },
        'snapshots': {
            # Ubuntu boots with Wireshark open and a terminal showing ifconfig
            'Linux Ubuntu': 'scenario-networking-ubuntu',
        },
        'launch_instructions': (
            'Wireshark is open and ready to capture.\n'
            'A terminal is also available.\n'
            'Try capturing traffic on the loopback interface first.'
        ),
        # Flag accessible via HTTP server: curl http://localhost:8080/flag.txt
        # Also hidden in ~/practice/.network_flag
        'flag': 'NET-FUND-COMPLETE',
        'flag_hint': 'Check the HTTP server — try: curl http://localhost:8080/flag.txt',
    },
    {
        'id': 'intermediate-1',
        'name': 'Web Application Security',
        'difficulty': 'Intermediate',
        'description': 'Identify and exploit common web vulnerabilities. '
                       'A vulnerable web app (DVWA) is running on Windows, '
                       'and Kali has Burp Suite open and pointed at it.',
        'vms': ['Windows 11', 'Linux Kali'],
        'vbox_names': {
            'Windows 11': 'cyberlab-intermediate1-windows11',
            'Linux Kali': 'cyberlab-intermediate1-kali',
        },
        'snapshots': {
            # Windows 11: DVWA running in Chrome at http://localhost/dvwa
            'Windows 11':  'scenario-webapp-win11',
            # Kali: Burp Suite open, browser proxy configured to 127.0.0.1:8080
            'Linux Kali':  'scenario-webapp-kali',
        },
        'launch_instructions': (
            'Windows 11: DVWA is running. Open Chrome — it loads http://localhost/dvwa.\n'
            'Kali: Burp Suite is open with the proxy listener active on port 8080.\n'
            'Default DVWA login: admin / password'
        ),
        # Flag revealed after exploiting a DVWA vulnerability (stored in /var/www/html/flag.txt)
        'flag': 'WEBAPP-SEC-COMPLETE',
        'flag_hint': 'Exploit DVWA to gain access, then read /var/www/html/flag.txt on Windows.',
    },
    {
        'id': 'intermediate-2',
        'name': 'Password Cracking',
        'difficulty': 'Intermediate',
        'description': 'Learn password attack techniques using Hashcat and John the Ripper. '
                       'A set of hashed passwords is waiting in ~/hashes.',
        'vms': ['Linux Kali', 'Linux Ubuntu'],
        'vbox_names': {
            'Linux Kali':   'cyberlab-intermediate2-kali',
            'Linux Ubuntu': 'cyberlab-intermediate2-ubuntu',
        },
        'snapshots': {
            # Kali: terminal open in ~/hashes, hashcat and john installed, wordlists in ~/wordlists
            'Linux Kali':    'scenario-passwords-kali',
            # Ubuntu: SSH server running with a locked user account for practice
            'Linux Ubuntu':  'scenario-passwords-ubuntu',
        },
        'launch_instructions': (
            'Kali: A terminal is open in ~/hashes with sample hash files.\n'
            'Ubuntu: SSH is running on port 22. Target user: "victim".\n'
            'Try: hashcat -m 0 hashes/md5.txt ~/wordlists/rockyou.txt'
        ),
        # Flag in ~/hashes/flag.txt, revealed after cracking the hashes
        'flag': 'PASS-CRACK-COMPLETE',
        'flag_hint': 'Crack the hashes in ~/hashes, then SSH into Ubuntu as "victim" and read ~/flag.txt.',
    },
    {
        'id': 'hard-1',
        'name': 'Metasploit Exploitation',
        'difficulty': 'Hard',
        'description': 'Advanced exploitation using the Metasploit framework. '
                       'A deliberately vulnerable target (Metasploitable) is running on Ubuntu, '
                       'and Kali has msfconsole pre-loaded.',
        'vms': ['Windows 11', 'Linux Kali', 'Linux Ubuntu'],
        'vbox_names': {
            'Windows 11':   'cyberlab-hard1-windows11',
            'Linux Kali':   'cyberlab-hard1-kali',
            'Linux Ubuntu': 'cyberlab-hard1-ubuntu',
        },
        'snapshots': {
            # Windows 11: vulnerable SMB service running (EternalBlue practice)
            'Windows 11':    'scenario-msf-win11',
            # Kali: msfconsole open, db connected, target IPs noted in /root/targets.txt
            'Linux Kali':    'scenario-msf-kali',
            # Ubuntu: Metasploitable services running (vsftpd, distcc, etc.)
            'Linux Ubuntu':  'scenario-msf-ubuntu',
        },
        'launch_instructions': (
            'Kali: msfconsole is open. Run "workspace capstone" to start.\n'
            'Ubuntu target IP is noted in /root/targets.txt on Kali.\n'
            'Windows 11 target is also listed. Try ms17_010_eternalblue for Windows.'
        ),
        # Flag at /root/proof.txt on Ubuntu after gaining root shell via Metasploit
        'flag': 'MSF-EXPLOIT-COMPLETE',
        'flag_hint': 'Exploit a vulnerability on Ubuntu or Windows, get a shell, and read /root/proof.txt.',
    }
]

# Learning modules
LEARNING_MODULES = [
    {
        'id': 'linux-basics',
        'name': 'Linux Basics',
        'description': 'Filesystem navigation, permissions, processes, and shell scripting.',
        'icon': '🐧',
        'topics': ['Filesystem & Navigation', 'File Permissions', 'Processes & Jobs', 'Shell Scripting Basics']
    },
    {
        'id': 'network-security',
        'name': 'Network Security',
        'description': 'TCP/IP fundamentals, packet analysis, port scanning, and network attacks.',
        'icon': '🌐',
        'topics': ['TCP/IP Model', 'Wireshark & Packet Analysis', 'Nmap Scanning', 'Common Network Attacks']
    },
    {
        'id': 'web-security',
        'name': 'Web Security',
        'description': 'OWASP Top 10, SQL injection, XSS, CSRF, and web exploitation tools.',
        'icon': '🕸️',
        'topics': ['OWASP Top 10', 'SQL Injection', 'Cross-Site Scripting (XSS)', 'Burp Suite Basics']
    },
    {
        'id': 'exploitation',
        'name': 'Exploitation Techniques',
        'description': 'Vulnerability research, Metasploit framework, payloads, and post-exploitation.',
        'icon': '⚔️',
        'topics': ['Vulnerability Research', 'Metasploit Framework', 'Payloads & Listeners', 'Post-Exploitation']
    }
]


def get_difficulty_color(difficulty):
    """Get color for difficulty badge"""
    colors = {
        'Beginner':     '#10b981',
        'Intermediate': '#f59e0b',
        'Hard':         '#ef4444'
    }
    return colors.get(difficulty, '#6b7280')


def get_scenario_by_id(scenario_id):
    """Look up a scenario by its ID"""
    return next((s for s in SCENARIOS if s['id'] == scenario_id), None)