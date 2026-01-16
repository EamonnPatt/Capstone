"""
User profile view
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from utils.styles import PROFILE_CARD_STYLE, COLORS


class ProfileView(QWidget):
    def __init__(self, user_data, scenarios, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.scenarios = scenarios
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)
        
        # Profile header
        header_frame = QFrame()
        header_frame.setStyleSheet(PROFILE_CARD_STYLE)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(30, 30, 30, 30)
        
        username = QLabel(f"👤 {self.user_data['username']}")
        username.setFont(QFont('Arial', 26, QFont.Weight.Bold))
        username.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(username)
        
        role = QLabel("Cybersecurity Student")
        role.setFont(QFont('Arial', 13))
        role.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(role)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
        
        # Stats
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        stats = [
            ("🏆 Completed Scenarios", f"{len(self.user_data['completed_scenarios'])}/{len(self.scenarios)}"),
            ("📚 Learning Modules", str(self.user_data['learning_modules_completed'])),
            ("🛡️ Skill Level", "Beginner")
        ]
        
        for label, value in stats:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(PROFILE_CARD_STYLE)
            
            stat_layout = QVBoxLayout()
            stat_layout.setContentsMargins(25, 25, 25, 25)
            
            stat_label = QLabel(label)
            stat_label.setFont(QFont('Arial', 11))
            stat_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            stat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_label)
            
            stat_value = QLabel(value)
            stat_value.setFont(QFont('Arial', 22, QFont.Weight.Bold))
            stat_value.setStyleSheet(f"color: {COLORS['text_primary']};")
            stat_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_layout.addWidget(stat_value)
            
            stat_frame.setLayout(stat_layout)
            stats_layout.addWidget(stat_frame)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
        self.setLayout(layout)