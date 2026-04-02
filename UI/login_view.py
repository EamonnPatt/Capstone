"""
Login / Register / Forgot Password screen
Uses core.database for all user storage (MongoDB).
"""
 
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
 
from core.database import loginUser, addUser, resetPassword
 
 
# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------
 
DARK   = '#0a0f1e'
PANEL  = '#111827'
CARD   = '#1a2235'
BORDER = '#1e3a5f'
ACCENT = '#00d4ff'
ACCENT2= '#0066ff'
TEXT   = '#e2e8f0'
MUTED  = '#64748b'
ERROR  = '#ef4444'
 
FIELD_STYLE = f"""
    QLineEdit {{
        background-color: #0d1626;
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 12px 14px;
        font-size: 13px;
        font-family: 'Consolas', 'Courier New', monospace;
    }}
    QLineEdit:focus {{
        border: 1px solid {ACCENT};
        background-color: #0f1e35;
    }}
"""
 
PRIMARY_BTN = f"""
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT2}, stop:1 {ACCENT});
        color: #000d1a;
        border: none;
        border-radius: 6px;
        padding: 13px;
        font-size: 13px;
        font-weight: bold;
        font-family: 'Consolas', 'Courier New', monospace;
        letter-spacing: 1px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0080ff, stop:1 #00eeff);
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #004fcc, stop:1 #00aacc);
    }}
    QPushButton:disabled {{
        background: #1e3a5f;
        color: {MUTED};
    }}
"""
 
GHOST_BTN = f"""
    QPushButton {{
        background: transparent;
        color: {ACCENT};
        border: none;
        font-size: 12px;
        font-family: 'Consolas', 'Courier New', monospace;
        text-decoration: underline;
        padding: 4px;
    }}
    QPushButton:hover {{ color: #00eeff; }}
"""
 
BACK_BTN = f"""
    QPushButton {{
        background: transparent;
        color: {MUTED};
        border: 1px solid {BORDER};
        border-radius: 5px;
        font-size: 11px;
        font-family: 'Consolas', 'Courier New', monospace;
        padding: 6px 14px;
    }}
    QPushButton:hover {{
        color: {TEXT};
        border-color: {ACCENT};
    }}
"""
 
 
# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
 
def _label(text, size=12, bold=False, color=TEXT):
    lbl = QLabel(text)
    w = QFont.Weight.Bold if bold else QFont.Weight.Normal
    lbl.setFont(QFont('Consolas', size, w))
    lbl.setStyleSheet(f"color: {color}; background: transparent;")
    return lbl
 
 
def _cap_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont('Consolas', 9, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color: {MUTED}; letter-spacing: 2px; background: transparent;")
    return lbl
 
 
def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(
        f"color: {BORDER}; background-color: {BORDER}; max-height: 1px;")
    return line
 
 
def _field(placeholder, echo=False):
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setStyleSheet(FIELD_STYLE)
    f.setFixedHeight(46)
    if echo:
        f.setEchoMode(QLineEdit.EchoMode.Password)
    return f
 
 
# ---------------------------------------------------------------------------
# Login panel
# ---------------------------------------------------------------------------
 
class LoginPanel(QWidget):
    login_success = pyqtSignal(object)   # emits full MongoDB user doc
    go_register   = pyqtSignal()
    go_forgot     = pyqtSignal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
 
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
 
        lay.addSpacing(8)
        title = _label("SIGN IN", 20, bold=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
 
        sub = _label("Access your training environment", 10, color=MUTED)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        lay.addSpacing(28)
 
        lay.addWidget(_cap_label("USERNAME"))
        lay.addSpacing(5)
        self.username_field = _field("Enter username…")
        lay.addWidget(self.username_field)
        lay.addSpacing(14)
 
        lay.addWidget(_cap_label("PASSWORD"))
        lay.addSpacing(5)
        self.password_field = _field("Enter password…", echo=True)
        self.password_field.returnPressed.connect(self._attempt_login)
        lay.addWidget(self.password_field)
        lay.addSpacing(6)
 
        forgot_row = QHBoxLayout()
        forgot_row.addStretch()
        forgot_btn = QPushButton("Forgot password?")
        forgot_btn.setStyleSheet(GHOST_BTN)
        forgot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot_btn.clicked.connect(self.go_forgot.emit)
        forgot_row.addWidget(forgot_btn)
        lay.addLayout(forgot_row)
        lay.addSpacing(18)
 
        self.error_lbl = _label("", 10, color=ERROR)
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setWordWrap(True)
        self.error_lbl.hide()
        lay.addWidget(self.error_lbl)
        lay.addSpacing(4)
 
        self.login_btn = QPushButton("ACCESS SYSTEM")
        self.login_btn.setStyleSheet(PRIMARY_BTN)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setFixedHeight(48)
        self.login_btn.clicked.connect(self._attempt_login)
        lay.addWidget(self.login_btn)
        lay.addSpacing(20)
 
        lay.addWidget(_divider())
        lay.addSpacing(16)
 
        reg_row = QHBoxLayout()
        reg_row.addStretch()
        reg_row.addWidget(_label("No account?", 11, color=MUTED))
        reg_row.addSpacing(6)
        reg_btn = QPushButton("Create one →")
        reg_btn.setStyleSheet(GHOST_BTN)
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.clicked.connect(self.go_register.emit)
        reg_row.addWidget(reg_btn)
        reg_row.addStretch()
        lay.addLayout(reg_row)
        lay.addStretch()
 
    def _attempt_login(self):
        username = self.username_field.text().strip()
        password = self.password_field.text()
 
        if not username or not password:
            self._show_error("Please enter both username and password.")
            return
 
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in…")
 
        success, result = loginUser(username, password)
 
        self.login_btn.setEnabled(True)
        self.login_btn.setText("ACCESS SYSTEM")
 
        if not success:
            self._show_error(result)
            return
 
        self.error_lbl.hide()
        self.login_success.emit(result)
 
    def _show_error(self, msg):
        self.error_lbl.setText(f"⚠  {msg}")
        self.error_lbl.show()
 
    def reset(self):
        self.username_field.clear()
        self.password_field.clear()
        self.error_lbl.hide()
        self.login_btn.setEnabled(True)
        self.login_btn.setText("ACCESS SYSTEM")
 
 
# ---------------------------------------------------------------------------
# Register panel
# ---------------------------------------------------------------------------
 
SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"]
 
 
class RegisterPanel(QWidget):
    register_success = pyqtSignal(str)
    go_back          = pyqtSignal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._skill_level = "Beginner"
        self._skill_btns  = {}
        self._build()
 
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
 
        lay.addSpacing(8)
        title = _label("CREATE ACCOUNT", 20, bold=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
 
        sub = _label("Join the CyberLab training platform", 10, color=MUTED)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        lay.addSpacing(20)
 
        lay.addWidget(_cap_label("USERNAME"))
        lay.addSpacing(5)
        self.username_field = _field("Choose a username…")
        lay.addWidget(self.username_field)
        lay.addSpacing(12)
 
        lay.addWidget(_cap_label("EMAIL"))
        lay.addSpacing(5)
        self.email_field = _field("your@email.com")
        lay.addWidget(self.email_field)
        lay.addSpacing(12)
 
        lay.addWidget(_cap_label("PASSWORD"))
        lay.addSpacing(5)
        self.password_field = _field("Create a password…", echo=True)
        lay.addWidget(self.password_field)
        lay.addSpacing(12)
 
        lay.addWidget(_cap_label("CONFIRM PASSWORD"))
        lay.addSpacing(5)
        self.confirm_field = _field("Repeat your password…", echo=True)
        self.confirm_field.returnPressed.connect(self._attempt_register)
        lay.addWidget(self.confirm_field)
        lay.addSpacing(12)
 
        lay.addWidget(_cap_label("SKILL LEVEL"))
        lay.addSpacing(5)
        skill_row = QHBoxLayout()
        skill_row.setSpacing(8)
        for level in SKILL_LEVELS:
            btn = QPushButton(level)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, l=level: self._select_skill(l))
            self._skill_btns[level] = btn
            skill_row.addWidget(btn)
        self._select_skill("Beginner")
        lay.addLayout(skill_row)
        lay.addSpacing(14)
 
        self.error_lbl = _label("", 10, color=ERROR)
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setWordWrap(True)
        self.error_lbl.hide()
        lay.addWidget(self.error_lbl)
        lay.addSpacing(4)
 
        self.reg_btn = QPushButton("CREATE ACCOUNT")
        self.reg_btn.setStyleSheet(PRIMARY_BTN)
        self.reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reg_btn.setFixedHeight(48)
        self.reg_btn.clicked.connect(self._attempt_register)
        lay.addWidget(self.reg_btn)
        lay.addSpacing(12)
 
        back_btn = QPushButton("← Back to Login")
        back_btn.setStyleSheet(BACK_BTN)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back.emit)
        lay.addWidget(back_btn)
        lay.addStretch()
 
    def _select_skill(self, level):
        self._skill_level = level
        active = f"""
            QPushButton {{
                background-color: {ACCENT2};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }}
        """
        inactive = f"""
            QPushButton {{
                background-color: #0d1626;
                color: {MUTED};
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 8px 12px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {TEXT}; border-color: {ACCENT}; }}
        """
        for l, btn in self._skill_btns.items():
            btn.setStyleSheet(active if l == level else inactive)
 
    def _attempt_register(self):
        username = self.username_field.text().strip()
        email    = self.email_field.text().strip()
        password = self.password_field.text()
        confirm  = self.confirm_field.text()
 
        if not username:
            self._show_error("Username cannot be empty.")
            return
        if len(username) < 3:
            self._show_error("Username must be at least 3 characters.")
            return
        if not email or "@" not in email:
            self._show_error("Please enter a valid email address.")
            return
        if len(password) < 6:
            self._show_error("Password must be at least 6 characters.")
            return
        if password != confirm:
            self._show_error("Passwords do not match.")
            return
 
        self.reg_btn.setEnabled(False)
        self.reg_btn.setText("Creating account…")
 
        success, result = addUser(
            username=username,
            password=password,
            email=email,
            skill_level=self._skill_level,
        )
 
        self.reg_btn.setEnabled(True)
        self.reg_btn.setText("CREATE ACCOUNT")
 
        if not success:
            self._show_error(result)
            return
 
        self.error_lbl.hide()
        self.register_success.emit(username)
 
    def _show_error(self, msg):
        self.error_lbl.setText(f"⚠  {msg}")
        self.error_lbl.show()
 
    def reset(self):
        for f in (self.username_field, self.email_field,
                  self.password_field, self.confirm_field):
            f.clear()
        self._select_skill("Beginner")
        self.error_lbl.hide()
        self.reg_btn.setEnabled(True)
        self.reg_btn.setText("CREATE ACCOUNT")
 
 
# ---------------------------------------------------------------------------
# Forgot password panel
# ---------------------------------------------------------------------------
 
class ForgotPanel(QWidget):
    go_back = pyqtSignal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_user  = None
        self._target_email = None
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._render_step1()
 
    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
 
    def _render_step1(self):
        self._clear_layout()
        l = self._layout
 
        l.addSpacing(8)
        title = _label("RECOVER ACCESS", 20, bold=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(title)
 
        sub = _label("Verify your username and email", 10, color=MUTED)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(sub)
        l.addSpacing(28)
 
        l.addWidget(_cap_label("USERNAME"))
        l.addSpacing(5)
        self.recover_user = _field("Your username…")
        l.addWidget(self.recover_user)
        l.addSpacing(14)
 
        l.addWidget(_cap_label("EMAIL ADDRESS"))
        l.addSpacing(5)
        self.recover_email = _field("Email used when registering…")
        self.recover_email.returnPressed.connect(self._check_identity)
        l.addWidget(self.recover_email)
        l.addSpacing(18)
 
        self.error_lbl = _label("", 10, color=ERROR)
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setWordWrap(True)
        self.error_lbl.hide()
        l.addWidget(self.error_lbl)
        l.addSpacing(4)
 
        verify_btn = QPushButton("VERIFY IDENTITY")
        verify_btn.setStyleSheet(PRIMARY_BTN)
        verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        verify_btn.setFixedHeight(48)
        verify_btn.clicked.connect(self._check_identity)
        l.addWidget(verify_btn)
        l.addSpacing(14)
 
        back_btn = QPushButton("← Back to Login")
        back_btn.setStyleSheet(BACK_BTN)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back.emit)
        l.addWidget(back_btn)
        l.addStretch()
 
    def _render_step2(self):
        self._clear_layout()
        l = self._layout
 
        l.addSpacing(8)
        title = _label("RESET PASSWORD", 20, bold=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(title)
 
        sub = _label(f"New password for  {self._target_user}", 10, color=MUTED)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(sub)
        l.addSpacing(28)
 
        l.addWidget(_cap_label("NEW PASSWORD"))
        l.addSpacing(5)
        self.new_pw = _field("New password…", echo=True)
        l.addWidget(self.new_pw)
        l.addSpacing(14)
 
        l.addWidget(_cap_label("CONFIRM PASSWORD"))
        l.addSpacing(5)
        self.confirm_pw = _field("Confirm new password…", echo=True)
        self.confirm_pw.returnPressed.connect(self._do_reset)
        l.addWidget(self.confirm_pw)
        l.addSpacing(18)
 
        self.error_lbl2 = _label("", 10, color=ERROR)
        self.error_lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl2.setWordWrap(True)
        self.error_lbl2.hide()
        l.addWidget(self.error_lbl2)
        l.addSpacing(4)
 
        reset_btn = QPushButton("RESET PASSWORD")
        reset_btn.setStyleSheet(PRIMARY_BTN)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setFixedHeight(48)
        reset_btn.clicked.connect(self._do_reset)
        l.addWidget(reset_btn)
        l.addStretch()
 
    def _check_identity(self):
        username = self.recover_user.text().strip()
        email    = self.recover_email.text().strip()
 
        if not username or not email:
            self.error_lbl.setText("⚠  Please fill in both fields.")
            self.error_lbl.show()
            return
 
        # Verify by attempting the reset with a dummy password check
        from core.database import db as _db
        user = _db["users"].find_one({"username": username})
 
        if not user:
            self.error_lbl.setText("⚠  Username not found.")
            self.error_lbl.show()
            return
 
        if user.get("email", "").lower() != email.lower():
            self.error_lbl.setText("⚠  Email does not match our records.")
            self.error_lbl.show()
            return
 
        self._target_user  = username
        self._target_email = email
        self._render_step2()
 
    def _do_reset(self):
        pw      = self.new_pw.text()
        confirm = self.confirm_pw.text()
 
        if len(pw) < 6:
            self.error_lbl2.setText("⚠  Password must be at least 6 characters.")
            self.error_lbl2.show()
            return
        if pw != confirm:
            self.error_lbl2.setText("⚠  Passwords do not match.")
            self.error_lbl2.show()
            return
 
        success, msg = resetPassword(self._target_user, self._target_email, pw)
        if not success:
            self.error_lbl2.setText(f"⚠  {msg}")
            self.error_lbl2.show()
            return
 
        QMessageBox.information(
            self, "Password Reset",
            f"✅  Password for '{self._target_user}' has been updated.\n"
            f"You can now sign in with your new password."
        )
        self.go_back.emit()
 
    def reset(self):
        self._target_user  = None
        self._target_email = None
        self._render_step1()
 
 
# ---------------------------------------------------------------------------
# LoginWindow
# ---------------------------------------------------------------------------
 
class LoginWindow(QWidget):
    """
    Top-level window shown before the main app.
    Emits login_success(user_doc) with the full MongoDB user document.
    """
    login_success = pyqtSignal(object)
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CyberLab — Sign In")
        self.setMinimumSize(1100, 700)
        self._build_ui()
 
    def _build_ui(self):
        self.setStyleSheet(f"background-color: {DARK};")
 
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
 
        # ── Left decorative panel ────────────────────────────────────
        left = QFrame()
        left.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #03070f, stop:0.5 #061428, stop:1 #040c1e
                );
                border-right: 1px solid {BORDER};
            }}
        """)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(60, 60, 60, 60)
        ll.setSpacing(0)
 
        shield = _label("🛡️", 64)
        shield.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ll.addWidget(shield)
        ll.addSpacing(24)
 
        brand = _label("CyberLab", 36, bold=True)
        brand.setFont(QFont('Consolas', 36, QFont.Weight.Bold))
        ll.addWidget(brand)
 
        tagline = _label("Training Platform", 14, color=ACCENT)
        tagline.setFont(QFont('Consolas', 14))
        ll.addWidget(tagline)
        ll.addSpacing(50)
 
        for icon, text in [
            ("◈", "Hands-on VM scenarios"),
            ("◈", "Snapshot-backed environments"),
            ("◈", "Beginner to advanced tracks"),
            ("◈", "Real tools, real techniques"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(12)
            icon_lbl = _label(icon, 11, color=ACCENT)
            icon_lbl.setFixedWidth(18)
            row.addWidget(icon_lbl)
            row.addWidget(_label(text, 11, color=MUTED))
            row.addStretch()
            ll.addLayout(row)
            ll.addSpacing(10)
 
        ll.addStretch()
        ll.addWidget(_label("v1.0.0  ·  © 2025 CyberLab", 9, color='#1e3a5f'))
 
        root.addWidget(left, stretch=5)
 
        # ── Right auth panel ─────────────────────────────────────────
        right = QFrame()
        right.setStyleSheet(f"background-color: {PANEL};")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)
 
        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(40, 36, 40, 36)
        card_lay.setSpacing(0)
 
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
 
        self.login_panel    = LoginPanel()
        self.register_panel = RegisterPanel()
        self.forgot_panel   = ForgotPanel()
 
        self.stack.addWidget(self.login_panel)      # 0
        self.stack.addWidget(self.register_panel)   # 1
        self.stack.addWidget(self.forgot_panel)     # 2
 
        self.login_panel.login_success.connect(self._on_login_success)
        self.login_panel.go_register.connect(self._show_register)
        self.login_panel.go_forgot.connect(self._show_forgot)
 
        self.register_panel.register_success.connect(self._on_register_success)
        self.register_panel.go_back.connect(self._show_login)
 
        self.forgot_panel.go_back.connect(self._show_login)
 
        card_lay.addWidget(self.stack)
        rl.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(right, stretch=4)
 
    def _show_login(self):
        self.login_panel.reset()
        self.stack.setCurrentIndex(0)
 
    def _show_register(self):
        self.register_panel.reset()
        self.stack.setCurrentIndex(1)
 
    def _show_forgot(self):
        self.forgot_panel.reset()
        self.stack.setCurrentIndex(2)
 
    def _on_login_success(self, user_doc):
        self.login_success.emit(user_doc)
 
    def _on_register_success(self, username: str):
        QMessageBox.information(
            self, "Account Created",
            f"✅  Account '{username}' created successfully!\nYou can now sign in."
        )
        self._show_login()
        self.login_panel.username_field.setText(username)
        self.login_panel.password_field.setFocus()