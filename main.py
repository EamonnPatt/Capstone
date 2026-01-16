import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from UI.main_window import CyberTrainingApp


def main():
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # Create and show main window
    window = CyberTrainingApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()