"""
Styles and UI constants
"""

FONT = "Segoe UI"   # native Windows system font

# Color palette
COLORS = {
    'bg_primary':         '#0b1120',
    'bg_secondary':       '#111827',
    'bg_tertiary':        '#1e2d42',
    'bg_card':            '#141d2e',
    'bg_hover':           '#1a2640',
    'text_primary':       '#eef2ff',
    'text_secondary':     '#8899aa',
    'text_tertiary':      '#4a5568',
    'accent_blue':        '#3b82f6',
    'accent_blue_hover':  '#2563eb',
    'border':             '#1e2d42',
    'border_hover':       '#2d4261',
    'border_active':      '#3b82f6',
    'success':            '#10b981',
    'success_hover':      '#059669',
    'danger':             '#ef4444',
    'danger_hover':       '#dc2626',
    'warning':            '#f59e0b',
}

# Accent color per learning module id
MODULE_ACCENT_COLORS = {
    'linux-basics':       '#10b981',   # emerald
    'network-security':   '#3b82f6',   # blue
    'web-security':       '#f59e0b',   # amber
    'exploitation':       '#ef4444',   # red
}

# ── Main window ──────────────────────────────────────────────────────────────

MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background-color: {COLORS['bg_secondary']};
        width: 8px;
        border-radius: 4px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLORS['bg_tertiary']};
        border-radius: 4px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['border_hover']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""

# ── Navigation bar ───────────────────────────────────────────────────────────

NAV_BAR_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-bottom: 1px solid {COLORS['border']};
    }}
"""

def get_nav_button_style(active=False):
    if active:
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 22px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue_hover']};
            }}
        """
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLORS['text_secondary']};
            border: none;
            border-radius: 8px;
            padding: 8px 22px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
        }}
    """

# ── VM controls ──────────────────────────────────────────────────────────────

VM_CONTROL_STYLE = f"""
    VMControl {{
        background-color: {COLORS['bg_tertiary']};
        border-radius: 8px;
        border: 1px solid {COLORS['border']};
    }}
"""

START_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['success']};
        color: white;
        border: none;
        padding: 6px 16px;
        border-radius: 6px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {COLORS['success_hover']};
    }}
    QPushButton:disabled {{
        background-color: #2d3748;
        color: #6b7280;
    }}
"""

STOP_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['danger']};
        color: white;
        border: none;
        padding: 6px 16px;
        border-radius: 6px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {COLORS['danger_hover']};
    }}
    QPushButton:disabled {{
        background-color: #2d3748;
        color: #6b7280;
    }}
"""

LAUNCH_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['accent_blue']};
        color: white;
        border: none;
        padding: 14px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_blue_hover']};
    }}
    QPushButton:disabled {{
        background-color: #1e2d42;
        color: #4a5568;
    }}
"""

# ── Scenario items (left panel) ───────────────────────────────────────────────

SCENARIO_ITEM_STYLE = f"""
    ScenarioItem {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 10px;
        border: 1px solid {COLORS['border']};
    }}
"""

SCENARIO_ITEM_EXPANDED_STYLE = f"""
    ScenarioItem {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 10px;
        border: 1px solid {COLORS['border_active']};
    }}
"""

SCENARIO_HEADER_STYLE = f"""
    QFrame {{
        background-color: transparent;
        border-radius: 10px;
    }}
    QFrame:hover {{
        background-color: {COLORS['bg_hover']};
    }}
"""

SCENARIO_CONTENT_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_card']};
        border-radius: 0px;
        border-top: 1px solid {COLORS['border']};
    }}
"""

# ── Right panel (VM display area) ────────────────────────────────────────────

VM_DISPLAY_AREA_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-left: 1px solid {COLORS['border']};
    }}
"""

# ── Splitter ─────────────────────────────────────────────────────────────────

SPLITTER_STYLE = f"""
    QSplitter::handle {{
        background-color: {COLORS['border']};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    QSplitter::handle:hover {{
        background-color: {COLORS['accent_blue']};
    }}
"""

# ── Learning module cards ─────────────────────────────────────────────────────

def get_module_card_style(accent_color: str) -> str:
    """Card style with a coloured left border accent."""
    return f"""
        QFrame {{
            background-color: {COLORS['bg_secondary']};
            border-radius: 12px;
            border: 1px solid {COLORS['border']};
            border-left: 4px solid {accent_color};
        }}
        QFrame:hover {{
            background-color: {COLORS['bg_hover']};
            border-color: {COLORS['border_hover']};
            border-left-color: {accent_color};
        }}
    """

# Legacy — kept so existing imports don't break
MODULE_CARD_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
    }}
"""

# ── Profile cards ────────────────────────────────────────────────────────────

PROFILE_CARD_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_secondary']};
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
    }}
"""

PROGRESS_BAR_STYLE = f"""
    QProgressBar {{
        background-color: {COLORS['bg_tertiary']};
        border-radius: 5px;
        border: none;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent_blue']};
        border-radius: 5px;
    }}
"""
