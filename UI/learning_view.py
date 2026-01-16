"""
Learning resources view
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QFont
from core.data import LEARNING_MODULES
from utils.styles import MODULE_CARD_STYLE, COLORS


class LearningView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Learning Resources")
        header.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(header)
        
        # Module cards
        for module in LEARNING_MODULES:
            frame = QFrame()
            frame.setStyleSheet(MODULE_CARD_STYLE)
            
            module_layout = QVBoxLayout()
            module_layout.setContentsMargins(25, 20, 25, 20)
            
            title = QLabel(f"{module['icon']} {module['name']}")
            title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {COLORS['text_primary']};")
            module_layout.addWidget(title)
            
            desc = QLabel(module['description'])
            desc.setFont(QFont('Arial', 11))
            desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
            module_layout.addWidget(desc)
            
            frame.setLayout(module_layout)
            layout.addWidget(frame)
        
        layout.addStretch()
        self.setLayout(layout)