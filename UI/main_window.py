"""
Main application window
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.vm_manager import VMManager
from core.vagrant_manager import VagrantManager
from core.data import USER_DATA, SCENARIOS
from core.progress import load_progress
from UI.scenario_view_v2 import ScenarioView
from UI.learning_view import LearningView
from UI.profile_view import ProfileView
from utils.styles import MAIN_WINDOW_STYLE, NAV_BAR_STYLE, get_nav_button_style, COLORS, FONT


class CyberTrainingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vm_manager      = VMManager()
        self.vagrant_manager = VagrantManager()
        self.user_data    = USER_DATA
        self.scenarios    = SCENARIOS
        load_progress(self.user_data)   # restore saved progress on startup
        self.current_view = "scenarios"
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("CyberLab Training Platform")
        self.setMinimumSize(800, 560)
        self.resize(1280, 800)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._build_nav_bar())
        self.content_area = QWidget()
        self.content_area.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        main_layout.addWidget(self.content_area)
        self.show_scenarios_view()

    def _build_nav_bar(self):
        nav_bar = QFrame()
        nav_bar.setStyleSheet(NAV_BAR_STYLE)
        nav_bar.setFixedHeight(64)

        layout = QHBoxLayout(nav_bar)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(0)

        # Brand
        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        shield = QLabel("🛡")
        shield.setFont(QFont(FONT, 18))
        brand_row.addWidget(shield)

        title = QLabel("CyberLab")
        title.setFont(QFont(FONT, 17, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        brand_row.addWidget(title)

        subtitle = QLabel("Training Platform")
        subtitle.setFont(QFont(FONT, 11))
        subtitle.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignBottom)
        brand_row.addWidget(subtitle)

        layout.addLayout(brand_row)
        layout.addStretch()

        # Nav buttons
        self.nav_buttons = {}
        for text, view in [("Scenarios", "scenarios"),
                            ("Learning",  "learning"),
                            ("Profile",   "profile")]:
            btn = QPushButton(text)
            btn.setFont(QFont(FONT, 11))
            btn.setStyleSheet(get_nav_button_style(view == self.current_view))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, v=view: self.switch_view(v))
            btn.setFixedHeight(38)
            btn.setMinimumWidth(110)
            layout.addWidget(btn)
            self.nav_buttons[view] = btn

        return nav_bar

    def switch_view(self, view):
        self.current_view = view
        for v, btn in self.nav_buttons.items():
            btn.setStyleSheet(get_nav_button_style(v == view))
        if view == "scenarios":
            self.show_scenarios_view()
        elif view == "learning":
            self.show_learning_view()
        elif view == "profile":
            self.show_profile_view()

    def _clear_content(self):
        if self.content_area.layout():
            QWidget().setLayout(self.content_area.layout())

    def show_scenarios_view(self):
        self._clear_content()
        view = ScenarioView(self.scenarios, self.vm_manager, self.user_data,
                            vagrant_manager=self.vagrant_manager)
        layout = QVBoxLayout(self.content_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(view)

    def show_learning_view(self):
        self._clear_content()
        view = LearningView()
        layout = QVBoxLayout(self.content_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(view)

    def show_profile_view(self):
        self._clear_content()
        view = ProfileView(self.user_data, self.scenarios)
        layout = QVBoxLayout(self.content_area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(view)
