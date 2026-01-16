"""
Scenarios view with VM display area
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from UI.widgets import ScenarioItem, VMControl
from utils.styles import VM_DISPLAY_AREA_STYLE, LAUNCH_BUTTON_STYLE, COLORS


class ScenarioView(QWidget):
    def __init__(self, scenarios, vm_manager, user_data, parent=None):
        super().__init__(parent)
        self.scenarios = scenarios
        self.vm_manager = vm_manager
        self.user_data = user_data
        self.current_scenario = None
        
        self.setup_ui()
    
    def setup_ui(self):
        main_container = QHBoxLayout()
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)
        
        # Left side - Scenarios list
        left_panel = QWidget()
        left_panel.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(30, 30, 15, 30)
        left_layout.setSpacing(20)
        
        # Header
        header = QLabel("Scenarios")
        header.setFont(QFont('Arial', 28, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        left_layout.addWidget(header)
        
        subtitle = QLabel("Select a scenario to view settings and virtual machines")
        subtitle.setFont(QFont('Arial', 13))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(subtitle)
        
        # Scroll area for scenarios
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        # Create expandable scenario items
        for scenario in self.scenarios:
            item = ScenarioItem(scenario, self.vm_manager, self)
            scroll_layout.addWidget(item)
        
        scroll_layout.addStretch()
        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)
        
        left_panel.setLayout(left_layout)
        main_container.addWidget(left_panel, stretch=2)
        
        # Right side - VM Display Area
        self.vm_display_area = QFrame()
        self.vm_display_area.setStyleSheet(VM_DISPLAY_AREA_STYLE)
        
        self.vm_area_layout = QVBoxLayout()
        self.vm_area_layout.setContentsMargins(30, 30, 30, 30)
        self.vm_area_layout.setSpacing(20)
        
        # Placeholder content
        vm_header = QLabel("VM Display Area")
        vm_header.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        vm_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.vm_area_layout.addWidget(vm_header)
        
        placeholder = QLabel("Select and expand a scenario to control virtual machines")
        placeholder.setFont(QFont('Arial', 12))
        placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vm_area_layout.addWidget(placeholder)
        self.vm_area_layout.addStretch()
        
        self.vm_display_area.setLayout(self.vm_area_layout)
        main_container.addWidget(self.vm_display_area, stretch=3)
        
        self.setLayout(main_container)
    
    def show_scenario_vms(self, scenario):
        """Display VMs in the VM area when scenario is selected"""
        self.current_scenario = scenario
        
        # Clear VM area
        while self.vm_area_layout.count():
            item = self.vm_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Header
        header = QLabel(f"{scenario['name']}")
        header.setFont(QFont('Arial', 22, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {COLORS['text_primary']};")
        header.setWordWrap(True)
        self.vm_area_layout.addWidget(header)
        
        desc = QLabel(scenario['description'])
        desc.setFont(QFont('Arial', 12))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        self.vm_area_layout.addWidget(desc)
        
        # VM section
        vm_section_label = QLabel("Virtual Machines")
        vm_section_label.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        vm_section_label.setStyleSheet(f"color: {COLORS['text_primary']}; margin-top: 20px;")
        self.vm_area_layout.addWidget(vm_section_label)
        
        # VM controls
        for vm_name in scenario['vms']:
            vm_control = VMControl(vm_name, self.vm_manager)
            self.vm_area_layout.addWidget(vm_control)
        
        self.vm_area_layout.addStretch()
        
        # Launch button
        launch_btn = QPushButton("Launch Scenario")
        launch_btn.setFont(QFont('Arial', 13, QFont.Weight.Bold))
        launch_btn.setStyleSheet(LAUNCH_BUTTON_STYLE)
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.clicked.connect(lambda: self.launch_scenario(scenario))
        launch_btn.setMinimumHeight(50)
        self.vm_area_layout.addWidget(launch_btn)
    
    def clear_vm_area(self):
        """Clear the VM display area"""
        self.current_scenario = None
        
        # Clear VM area
        while self.vm_area_layout.count():
            item = self.vm_area_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Restore placeholder
        vm_header = QLabel("VM Display Area")
        vm_header.setFont(QFont('Arial', 24, QFont.Weight.Bold))
        vm_header.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.vm_area_layout.addWidget(vm_header)
        
        placeholder = QLabel("Select and expand a scenario to control virtual machines")
        placeholder.setFont(QFont('Arial', 12))
        placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']};")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vm_area_layout.addWidget(placeholder)
        self.vm_area_layout.addStretch()
    
    def launch_scenario(self, scenario):
        QMessageBox.information(
            self,
            "Scenario Launched",
            f"Launching {scenario['name']}!\n\nMake sure all required VMs are running."
        )