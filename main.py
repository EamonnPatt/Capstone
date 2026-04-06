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
 
        main_win = CyberTrainingApp()
 
        # Populate user_data from the MongoDB document
        main_win.user_data['username']    = user_doc.get('username', 'User')
        main_win.user_data['skill_level'] = user_doc.get('skill_level', 'Beginner')
        main_win.user_data['user_id']     = user_doc.get('user_id', '')
        main_win.user_data['email']       = user_doc.get('email', '')
 
        main_win.show()
 
    login_win.login_success.connect(on_login_success)
    login_win.show()
 
    sys.exit(app.exec())
 
 
if __name__ == "__main__":
    main()
