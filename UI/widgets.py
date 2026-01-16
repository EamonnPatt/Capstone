"""
Reusable UI widgets
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from utils.styles import (VM_CONTROL_STYLE, START_BUTTON_STYLE, STOP_BUTTON_STYLE,
                          SCENARIO_ITEM_STYLE, SCENARIO_ITEM_EXPANDED_STYLE,
                          SCENARIO_HEADER_STYLE, SCENARIO_CONTENT_STYLE, COLORS)
from core.data import get_difficulty_color


class VMControl(QFrame):
    """Individual VM control widget"""
    
    def __init__(self, vm_name, vm_manager, parent=None):
        super().__init__(parent)
        self.vm_name = vm_name
        self.vm_manager = vm_manager
        self.setup_ui()
        
        # Update status every 5 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)
        
        # Initial status update
        self.update_status()
        
    def setup_ui(self):
        self.setStyleSheet(VM_CONTROL_STYLE)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        # VM name
        self.name_label = QLabel(self.vm_name)
        self.name_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Status
        self.status_label = QLabel("Checking...")
        self.status_label.setFont(QFont('Arial', 10))
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.status_label)
        
        # Start button
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self.start_btn.setStyleSheet(START_BUTTON_STYLE)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_vm)
        layout.addWidget(self.start_btn)
        
        # Stop button
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self.stop_btn.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_vm)
        layout.addWidget(self.stop_btn)
        
        self.setLayout(layout)
    
    def update_status(self):
        state = self.vm_manager.get_vm_state(self.vm_name)
        
        if state == "running":
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        elif state == "poweroff":
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        else:
            self.status_label.setText("● Unknown")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
    
    def start_vm(self):
        self.status_label.setText("Starting...")
        self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
        QApplication.processEvents()
        
        if self.vm_manager.start_vm(self.vm_name):
            QMessageBox.information(self, "Success", f"VM '{self.vm_name}' started successfully!")
        else:
            QMessageBox.critical(self, "Error", f"Failed to start VM '{self.vm_name}'")
        
        self.update_status()
    
    def stop_vm(self):
        self.status_label.setText("Stopping...")
        self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
        QApplication.processEvents()
        
        if self.vm_manager.stop_vm(self.vm_name):
            QMessageBox.information(self, "Success", f"VM '{self.vm_name}' stopped successfully!")
        else:
            QMessageBox.critical(self, "Error", f"Failed to stop VM '{self.vm_name}'")
        
        self.update_status()


class ScenarioItem(QFrame):
    """Expandable scenario item"""
    
    def __init__(self, scenario, vm_manager, parent=None):
        super().__init__(parent)
        self.scenario = scenario
        self.vm_manager = vm_manager
        self.parent_window = parent
        self.is_expanded = False
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(SCENARIO_ITEM_STYLE)
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header (clickable)
        self.header = QFrame()
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet(SCENARIO_HEADER_STYLE)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)
        header_layout.setSpacing(15)
        
        # Left side - scenario info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        
        # Title row
        title_row = QHBoxLayout()
        
        # Expand arrow
        self.arrow_label = QLabel("▶")
        self.arrow_label.setFont(QFont('Arial', 10))
        self.arrow_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.arrow_label.setFixedWidth(20)
        title_row.addWidget(self.arrow_label)
        
        title = QLabel(self.scenario['name'])
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        title.setWordWrap(True)
        title_row.addWidget(title)
        
        title_row.addStretch()
        
        # Difficulty badge
        diff_color = get_difficulty_color(self.scenario['difficulty'])
        diff_badge = QLabel(self.scenario['difficulty'])
        diff_badge.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        diff_badge.setStyleSheet(f"""
            background-color: {diff_color};
            color: white;
            padding: 4px 12px;
            border-radius: 10px;
        """)
        diff_badge.setFixedHeight(24)
        title_row.addWidget(diff_badge)
        
        info_layout.addLayout(title_row)
        
        # Description
        desc = QLabel(self.scenario['description'])
        desc.setFont(QFont('Arial', 10))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-left: 20px;")
        desc.setWordWrap(True)
        info_layout.addWidget(desc)
        
        header_layout.addLayout(info_layout)
        self.header.setLayout(header_layout)
        
        # Make header clickable
        self.header.mousePressEvent = lambda e: self.toggle_expanded()
        
        self.main_layout.addWidget(self.header)
        
        # Expandable content area (Settings and VM section)
        self.content_area = QFrame()
        self.content_area.setStyleSheet(SCENARIO_CONTENT_STYLE)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(15)
        
        # Settings label
        settings_label = QLabel("Settings")
        settings_label.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        settings_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        content_layout.addWidget(settings_label)
        
        # VM section label
        vm_label = QLabel("VM")
        vm_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        vm_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        content_layout.addWidget(vm_label)
        
        # VM list with labels
        for vm_name in self.scenario['vms']:
            vm_item_layout = QHBoxLayout()
            
            vm_name_label = QLabel(vm_name)
            vm_name_label.setFont(QFont('Arial', 11))
            vm_name_label.setStyleSheet("color: #cbd5e1;")
            vm_item_layout.addWidget(vm_name_label)
            vm_item_layout.addStretch()
            
            content_layout.addLayout(vm_item_layout)
        
        self.content_area.setLayout(content_layout)
        self.content_area.hide()  # Hidden by default
        
        self.main_layout.addWidget(self.content_area)
        self.setLayout(self.main_layout)
    
    def toggle_expanded(self):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.arrow_label.setText("▼")
            self.content_area.show()
            self.setStyleSheet(SCENARIO_ITEM_EXPANDED_STYLE)
            # Notify parent to show VMs in the VM area
            if self.parent_window:
                self.parent_window.show_scenario_vms(self.scenario)
        else:
            self.arrow_label.setText("▶")
            self.content_area.hide()
            self.setStyleSheet(SCENARIO_ITEM_STYLE)
            # Clear VM area
            if self.parent_window:
                self.parent_window.clear_vm_area()