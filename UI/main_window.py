"""
Main application window
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import core.database as db
from core.vm_manager import VMManager
from core.data import SCENARIOS
from UI.scenario_view_v2 import ScenarioView
from UI.learning_view import LearningView
from UI.profile_view import ProfileView
from utils.styles import MAIN_WINDOW_STYLE, NAV_BAR_STYLE, get_nav_button_style, COLORS, FONT


class CyberTrainingApp(QMainWindow):
    def __init__(self, user_id: str):
        """
        Parameters
        ----------
        user_id : the logged-in user's user_id returned by loginUser()
        """
        super().__init__()

        self.user_id = user_id
        self.vm_manager = VMManager()
        self.scenarios = SCENARIOS
        self.current_view = "scenarios"

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("CyberLab Training Platform")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav_bar = self._build_nav_bar()
        main_layout.addWidget(nav_bar)

        self.content_area = QWidget()
        self.content_area.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        main_layout.addWidget(self.content_area)

        central_widget.setLayout(main_layout)
        self.show_scenarios_view()

    def _build_nav_bar(self):
        nav_bar = QFrame()
        nav_bar.setStyleSheet(NAV_BAR_STYLE)
        nav_bar.setFixedHeight(70)

        layout = QHBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("🛡️ CyberLab Training")
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #f8fafc;")
        layout.addWidget(title)

        layout.addStretch()

        self.nav_buttons = {}
        for text, view in [("Scenarios", "scenarios"), ("Learning", "learning"), ("Profile", "profile")]:
            btn = QPushButton(text)
            btn.setFont(QFont('Arial', 11, QFont.Weight.Medium))
            btn.setStyleSheet(get_nav_button_style(view == self.current_view))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, v=view: self.switch_view(v))
            btn.setFixedHeight(38)
            btn.setMinimumWidth(110)
            layout.addWidget(btn)
            self.nav_buttons[view] = btn

        nav_bar.setLayout(layout)
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

    # ------------------------------------------------------------------
    # View helpers
    # ------------------------------------------------------------------

    def _set_content(self, widget):
        """Replace whatever is in content_area with *widget*."""
        if self.content_area.layout():
            old_layout = self.content_area.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        self.content_area.setLayout(layout)

    def show_scenarios_view(self):
        user = db.getUser(self.user_id)
        self._set_content(ScenarioView(self.scenarios, self.vm_manager, user))

    def show_learning_view(self):
        self._set_content(LearningView())

    def show_profile_view(self):
        # Re-fetches from MongoDB each time so changes are always current
        self._set_content(ProfileView(self.user_id, self.scenarios))
