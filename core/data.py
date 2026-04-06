"""
Data module - Stores scenarios and learning modules.
User profile data is now managed by core/database.py (cyberlab.db).
"""

# Scenarios data
# Each VM entry in 'snapshots' maps a VM name to the VirtualBox snapshot name
# that should be restored when launching that scenario.
SCENARIOS = [
    {
        'id': 'beginner-1',
        'name': 'Command Line Basics',
        'difficulty': 'Beginner',
        'description': 'Learn fundamental command line operations in a Linux environment. '
                       'A terminal is pre-opened with a practice directory ready to go.',
        'vms': ['Linux Kali'],
        'snapshots': {
            'Linux Kali': 'scenario-cmdline-kali',
        },
        'launch_instructions': (
            'A terminal has been opened for you.\n'
            'Your working directory is ~/practice.\n'
            'Try: ls, pwd, cd, mkdir, and cat to get started.'
        )
    },
    {
        'id': 'beginner-2',
        'name': 'Network Fundamentals',
        'difficulty': 'Beginner',
        'description': 'Explore basic networking concepts. '
                       'Wireshark and a terminal are ready to capture traffic.',
        'vms': ['Linux Ubuntu'],
        'snapshots': {
            'Linux Ubuntu': 'scenario-networking-ubuntu',
        },
        'launch_instructions': (
            'Wireshark is open and ready to capture.\n'
            'A terminal is also available.\n'
            'Try capturing traffic on the loopback interface first.'
        )
    },
    {
        'id': 'intermediate-1',
        'name': 'Web Application Security',
        'difficulty': 'Intermediate',
        'description': 'Identify and exploit common web vulnerabilities. '
                       'A vulnerable web app (DVWA) is running on Windows, '
                       'and Kali has Burp Suite open and pointed at it.',
        'vms': ['Windows 11', 'Linux Kali'],
        'snapshots': {
            'Windows 11':  'scenario-webapp-win11',
            'Linux Kali':  'scenario-webapp-kali',
        },
        'launch_instructions': (
            'Windows 11: DVWA is running. Open Chrome — it loads http://localhost/dvwa.\n'
            'Kali: Burp Suite is open with the proxy listener active on port 8080.\n'
            'Default DVWA login: admin / password'
        )
    },
    {
        'id': 'intermediate-2',
        'name': 'Password Cracking',
        'difficulty': 'Intermediate',
        'description': 'Learn password attack techniques using Hashcat and John the Ripper. '
                       'A set of hashed passwords is waiting in ~/hashes.',
        'vms': ['Linux Kali', 'Linux Ubuntu'],
        'snapshots': {
            'Linux Kali':    'scenario-passwords-kali',
            'Linux Ubuntu':  'scenario-passwords-ubuntu',
        },
        'launch_instructions': (
            'Kali: A terminal is open in ~/hashes with sample hash files.\n'
            'Ubuntu: SSH is running on port 22. Target user: "victim".\n'
            'Try: hashcat -m 0 hashes/md5.txt ~/wordlists/rockyou.txt'
        )
    },
    {
        'id': 'hard-1',
        'name': 'Metasploit Exploitation',
        'difficulty': 'Hard',
        'description': 'Advanced exploitation using the Metasploit framework. '
                       'A deliberately vulnerable target (Metasploitable) is running on Ubuntu, '
                       'and Kali has msfconsole pre-loaded.',
        'vms': ['Windows 11', 'Linux Kali', 'Linux Ubuntu'],
        'snapshots': {
            'Windows 11':    'scenario-msf-win11',
            'Linux Kali':    'scenario-msf-kali',
            'Linux Ubuntu':  'scenario-msf-ubuntu',
        },
        'launch_instructions': (
            'Kali: msfconsole is open. Run "workspace capstone" to start.\n'
            'Ubuntu target IP is noted in /root/targets.txt on Kali.\n'
            'Windows 11 target is also listed. Try ms17_010_eternalblue for Windows.'
        )
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