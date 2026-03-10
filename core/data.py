"""
Data module - Stores scenarios and user data
"""

# User data
USER_DATA = {
    'username': 'CyberStudent',
    'completed_scenarios': ['beginner-1'],
    'learning_modules_completed': 3
}

# Scenarios data
SCENARIOS = [
    {
        'id': 'beginner-1',
        'name': 'Command Line Basics',
        'difficulty': 'Beginner',
        'description': 'Learn fundamental command line operations',
        'vms': ['Linux Kali']
    },
    {
        'id': 'beginner-2',
        'name': 'Network Fundamentals',
        'difficulty': 'Beginner',
        'description': 'Understanding basic networking concepts',
        'vms': ['linux ubuntu']
    },
    {
        'id': 'intermediate-1',
        'name': 'Web Application Security',
        'difficulty': 'Intermediate',
        'description': 'Identify and exploit web vulnerabilities',
        'vms': ['Windows 11', 'Linux Kali']
    },
    {
        'id': 'intermediate-2',
        'name': 'Password Cracking',
        'difficulty': 'Intermediate',
        'description': 'Learn password attack techniques',
        'vms': ['Linux Kali', 'Linux Ubuntu']
    },
    {
        'id': 'hard-1',
        'name': 'Metasploit Exploitation',
        'difficulty': 'Hard',
        'description': 'Advanced exploitation using Metasploit framework',
        'vms': ['Windows 11', 'Linux Kali', 'Linux Ubuntu']
    }
]

# Learning modules
LEARNING_MODULES = [
    {
        'id': 'linux-basics',
        'name': 'Linux Basics',
        'description': 'Comprehensive guide covering essential concepts and practical exercises.',
        'icon': '📚'
    },
    {
        'id': 'network-security',
        'name': 'Network Security',
        'description': 'Comprehensive guide covering essential concepts and practical exercises.',
        'icon': '📚'
    },
    {
        'id': 'web-security',
        'name': 'Web Security',
        'description': 'Comprehensive guide covering essential concepts and practical exercises.',
        'icon': '📚'
    },
    {
        'id': 'exploitation',
        'name': 'Exploitation Techniques',
        'description': 'Comprehensive guide covering essential concepts and practical exercises.',
        'icon': '📚'
    }
]


def get_difficulty_color(difficulty):
    """Get color for difficulty badge"""
    colors = {
        'Beginner': '#10b981',
        'Intermediate': '#f59e0b',
        'Hard': '#ef4444'
    }
    return colors.get(difficulty, '#6b7280')