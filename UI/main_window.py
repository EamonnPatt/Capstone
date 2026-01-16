"""
Main application window
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.vm_manager import VMManager
from core.data import USER_DATA, SCENARIOS
from UI.scenario_view import ScenarioView
from UI.learning_view import LearningView
from UI.profile_view import ProfileView
from utils.styles import MAIN_WINDOW_STYLE, NAV_BAR_STYLE, get_nav_button_style


class CyberTrainingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize VM manager
        self.vm_manager = VMManager()
        
        # User data
        self.user_data = USER_DATA
        self.scenarios = SCENARIOS
        
        self.current_view = "scenarios"
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("CyberLab Training Platform")
        self.setMinimumSize(1400, 900)
        
        # Set dark theme
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Navigation bar
        nav_bar = self.create_nav_bar()
        main_layout.addWidget(nav_bar)
        
        # Content area
        self.content_area = QWidget()
        main_layout.addWidget(self.content_area)
        
        central_widget.setLayout(main_layout)
        
        # Show initial view
        self.show_scenarios_view()
    
    def create_nav_bar(self):
        nav_bar = QFrame()
        nav_bar.setStyleSheet(NAV_BAR_STYLE)
        nav_bar.setFixedHeight(70)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 0, 30, 0)
        
        # Logo and title
        title = QLabel("🛡️ CyberLab Training")
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #f8fafc;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Navigation buttons
        self.nav_buttons = {}
        for text, view in [("Scenarios", "scenarios"), ("Learning", "learning"), ("Profile", "profile")]:
            btn = QPushButton(text)
            btn.setFont(QFont('Arial', 11, QFont.Weight.Medium))
            btn.setStyleSheet(get_nav_button_style(view == self.current_view))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, v=view: self.switch_view(v))
            btn.setFixedHeight(40)
            btn.setMinimumWidth(120)
            layout.addWidget(btn)
            self.nav_buttons[view] = btn
        
        nav_bar.setLayout(layout)
        return nav_bar
    
    def switch_view(self, view):
        self.current_view = view
        
        # Update button styles
        for v, btn in self.nav_buttons.items():
            btn.setStyleSheet(get_nav_button_style(v == view))
        
        # Show appropriate view
        if view == "scenarios":
            self.show_scenarios_view()
        elif view == "learning":
            self.show_learning_view()
        elif view == "profile":
            self.show_profile_view()
    
    def show_scenarios_view(self):
        # Clear existing content
        if self.content_area.layout():
            QWidget().setLayout(self.content_area.layout())
        
        # Create scenario view
        scenario_view = ScenarioView(self.scenarios, self.vm_manager, self.user_data)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scenario_view)
        
        self.content_area.setLayout(layout)
    
    def show_learning_view(self):
        # Clear existing content
        if self.content_area.layout():
            QWidget().setLayout(self.content_area.layout())
        
        # Create learning view
        learning_view = LearningView()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(learning_view)
        
        self.content_area.setLayout(layout)
    
    def show_profile_view(self):
        # Clear existing content
        if self.content_area.layout():
            QWidget().setLayout(self.content_area.layout())
        
        # Create profile view
        profile_view = ProfileView(self.user_data, self.scenarios)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(profile_view)
        
        self.content_area.setLayout(layout)