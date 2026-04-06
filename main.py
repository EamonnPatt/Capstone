import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from UI.login_view import LoginWindow
from UI.main_window import CyberTrainingApp


def main():
    app = QApplication(sys.argv)

    font = QFont("Consolas", 10)
    app.setFont(font)

    login_win = LoginWindow()
    main_win  = None

    def on_login_success(user_doc):
        nonlocal main_win
        login_win.hide()

        main_win = CyberTrainingApp(user_id=user_doc["user_id"])
        main_win.show()

    login_win.login_success.connect(on_login_success)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()