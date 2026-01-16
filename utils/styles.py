"""
Styles and UI constants
"""

# Color palette
COLORS = {
    'bg_primary': '#0f172a',
    'bg_secondary': '#1e293b',
    'bg_tertiary': '#334155',
    'text_primary': '#f8fafc',
    'text_secondary': '#94a3b8',
    'text_tertiary': '#64748b',
    'accent_blue': '#3b82f6',
    'accent_blue_hover': '#2563eb',
    'border': '#334155',
    'border_hover': '#475569',
    'border_active': '#3b82f6',
    'success': '#10b981',
    'success_hover': '#059669',
    'danger': '#ef4444',
    'danger_hover': '#dc2626',
    'warning': '#f59e0b',
}

# Main window style
MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}
    QScrollArea {{
        border: none;
        background-color: {COLORS['bg_primary']};
    }}
    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 12px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLORS['bg_tertiary']};
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['border_hover']};
    }}
"""

# Navigation bar style
NAV_BAR_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-bottom: 2px solid {COLORS['border']};
    }}
"""

def get_nav_button_style(active=False):
    """Get navigation button style"""
    if active:
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue_hover']};
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
            }}
        """

# VM Control styles
VM_CONTROL_STYLE = f"""
    VMControl {{
        background-color: {COLORS['bg_tertiary']};
        border-radius: 6px;
    }}
"""

START_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['success']};
        color: white;
        border: none;
        padding: 6px 15px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['success_hover']};
    }}
    QPushButton:disabled {{
        background-color: #4b5563;
        color: #9ca3af;
    }}
"""

STOP_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['danger']};
        color: white;
        border: none;
        padding: 6px 15px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['danger_hover']};
    }}
    QPushButton:disabled {{
        background-color: #4b5563;
        color: #9ca3af;
    }}
"""

LAUNCH_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['accent_blue']};
        color: white;
        border: none;
        padding: 15px;
        border-radius: 8px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_blue_hover']};
    }}
"""

# Scenario item styles
SCENARIO_ITEM_STYLE = f"""
    ScenarioItem {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 8px;
        border: 2px solid {COLORS['border']};
    }}
"""

SCENARIO_ITEM_EXPANDED_STYLE = f"""
    ScenarioItem {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 8px;
        border: 2px solid {COLORS['border_active']};
    }}
"""

SCENARIO_HEADER_STYLE = """
    QFrame {
        background-color: transparent;
        border-radius: 8px;
    }
    QFrame:hover {
        background-color: #253449;
    }
"""

SCENARIO_CONTENT_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_primary']};
        border-radius: 0px;
    }}
"""

# VM Display Area style
VM_DISPLAY_AREA_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-left: 2px solid {COLORS['border']};
    }}
"""

# Module card style
MODULE_CARD_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 12px;
        border: 2px solid {COLORS['border']};
    }}
"""

# Profile card style
PROFILE_CARD_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 12px;
    }}
"""