"""
VM Embed Widget
Starts a VirtualBox VM and embeds its window directly into the app.

Requires pywin32 on Windows:  pip install pywin32
"""

import subprocess
import platform
import time

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QWindow

from utils.styles import COLORS, START_BUTTON_STYLE, STOP_BUTTON_STYLE, LAUNCH_BUTTON_STYLE


# ---------------------------------------------------------------------------
# Window-finder thread  (Windows only)
# ---------------------------------------------------------------------------

class WindowFinder(QThread):
    """
    Polls for a VirtualBox VM window by searching for a top-level window
    whose title contains the VM name.  Emits the HWND once found.
    """
    found = pyqtSignal(int)   # HWND as int
    failed = pyqtSignal()

    def __init__(self, vm_name: str, timeout: float = 30.0, parent=None):
        super().__init__(parent)
        self.vm_name = vm_name
        self.timeout = timeout

    def run(self):
        try:
            import win32gui
        except ImportError:
            self.failed.emit()
            return

        deadline = time.time() + self.timeout
        search = self.vm_name.lower()

        while time.time() < deadline:
            hwnds = []

            def _cb(hwnd, _):
                try:
                    title = win32gui.GetWindowText(hwnd).lower()
                    # VirtualBox window titles look like "VM Name [Running] - Oracle VM VirtualBox"
                    if search in title and "virtualbox" in title:
                        hwnds.append(hwnd)
                except Exception:
                    pass

            win32gui.EnumWindows(_cb, None)

            if hwnds:
                self.found.emit(hwnds[0])
                return

            time.sleep(0.5)

        self.failed.emit()


# ---------------------------------------------------------------------------
# VMEmbedWidget
# ---------------------------------------------------------------------------

class VMEmbedWidget(QFrame):
    """
    Embeds a running VirtualBox VM window inside the application.

    States:
      stopped   → shows Start button
      starting  → shows spinner label, looking for VBox window
      embedded  → VM window is embedded, shows Release / Stop buttons
      released  → VM running externally, shows Re-embed / Stop buttons
    """

    def __init__(self, vm_name: str, vm_manager, parent=None):
        super().__init__(parent)
        self.vm_name = vm_name
        self.vm_manager = vm_manager

        self._state = "stopped"
        self._container = None      # QWidget wrapping the embedded QWindow
        self._finder = None         # WindowFinder thread
        self._worker = None         # VMWorker thread
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._refresh_status)
        self._poll_timer.start(5000)

        self._setup_ui()
        self._refresh_status()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────
        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                border-radius: 0px;
            }}
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 0, 12, 0)
        bar_layout.setSpacing(8)

        self._title_label = QLabel(self.vm_name)
        self._title_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self._title_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        bar_layout.addWidget(self._title_label)

        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont('Arial', 10))
        self._status_dot.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none;")
        bar_layout.addWidget(self._status_dot)

        bar_layout.addStretch()

        self._start_btn = QPushButton("▶ Start")
        self._start_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self._start_btn.setStyleSheet(START_BUTTON_STYLE)
        self._start_btn.setFixedHeight(28)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._on_start)
        bar_layout.addWidget(self._start_btn)

        self._embed_btn = QPushButton("⬛ Embed")
        self._embed_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self._embed_btn.setStyleSheet(LAUNCH_BUTTON_STYLE)
        self._embed_btn.setFixedHeight(28)
        self._embed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._embed_btn.clicked.connect(self._on_embed)
        self._embed_btn.hide()
        bar_layout.addWidget(self._embed_btn)

        self._release_btn = QPushButton("↗ Pop Out")
        self._release_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self._release_btn.setStyleSheet(LAUNCH_BUTTON_STYLE)
        self._release_btn.setFixedHeight(28)
        self._release_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._release_btn.clicked.connect(self._on_release)
        self._release_btn.hide()
        bar_layout.addWidget(self._release_btn)

        self._stop_btn = QPushButton("■ Stop")
        self._stop_btn.setFont(QFont('Arial', 9, QFont.Weight.Bold))
        self._stop_btn.setStyleSheet(STOP_BUTTON_STYLE)
        self._stop_btn.setFixedHeight(28)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.hide()
        bar_layout.addWidget(self._stop_btn)

        self._root_layout.addWidget(bar)

        # ── Body ─────────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.addWidget(self._body, stretch=1)

        self._placeholder = QLabel("VM not running\nPress ▶ Start to launch")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setFont(QFont('Arial', 12))
        self._placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none;")
        self._body_layout.addWidget(self._placeholder)

    # ------------------------------------------------------------------
    # Status polling
    # ------------------------------------------------------------------

    def _refresh_status(self):
        poller = self.vm_manager.poll_state_async(self.vm_name)
        self._pollers = getattr(self, '_pollers', [])
        self._pollers.append(poller)
        poller.state_ready.connect(self._apply_status)
        poller.state_ready.connect(lambda _: self._pollers.remove(poller) if poller in self._pollers else None)
        poller.start()

    def _apply_status(self, state: str):
        colors = {
            "running":  COLORS['success'],
            "poweroff": COLORS['text_tertiary'],
            "aborted":  COLORS['danger'],
            "paused":   COLORS['warning'],
            "saved":    COLORS['warning'],
        }
        self._status_dot.setStyleSheet(
            f"color: {colors.get(state, COLORS['text_tertiary'])}; border: none;")
        self._status_dot.setToolTip(state.capitalize())

        if state == "running" and self._state == "stopped":
            # VM started externally — offer embed
            self._set_state("released")
        elif state in ("poweroff", "aborted") and self._state not in ("stopped", "stopping"):
            self._detach_container()
            self._set_state("stopped")

    # ------------------------------------------------------------------
    # Button actions
    # ------------------------------------------------------------------

    def _on_start(self):
        self._set_state("starting")
        self._placeholder.setText(f"Starting {self.vm_name}…")

        worker = self.vm_manager.start_vm_async(self.vm_name, headless=False)
        self._worker = worker
        worker.finished.connect(self._on_start_done)
        worker.start()

    def _on_start_done(self, success: bool, message: str):
        if not success:
            self._placeholder.setText(f"Failed to start:\n{message}")
            self._set_state("stopped")
            return
        self._placeholder.setText(f"Waiting for {self.vm_name} window…")
        self._begin_embed()

    def _on_embed(self):
        """Re-embed a VM that was popped out."""
        self._placeholder.setText(f"Looking for {self.vm_name} window…")
        self._set_state("starting")
        self._begin_embed()

    def _on_release(self):
        """Pop the VM out into its own window."""
        self._detach_container()
        self._set_state("released")

    def _on_stop(self):
        self._detach_container()
        self._set_state("stopping")
        worker = self.vm_manager.stop_vm_async(self.vm_name, force=True)
        self._worker = worker
        worker.finished.connect(self._on_stop_done)
        worker.start()

    def _on_stop_done(self, success: bool, message: str):
        if success:
            self._set_state("stopped")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Stop Failed",
                                 f"Could not stop '{self.vm_name}':\n\n{message}")
            self._set_state("released")

    # ------------------------------------------------------------------
    # Embed / detach
    # ------------------------------------------------------------------

    def _begin_embed(self):
        if platform.system() != "Windows":
            self._placeholder.setText(
                "Window embedding is only supported on Windows.\n"
                "The VM is running — check VirtualBox."
            )
            self._set_state("released")
            return

        try:
            import win32gui  # noqa – just checking availability
        except ImportError:
            self._placeholder.setText(
                "pywin32 not installed.\n"
                "Run:  pip install pywin32\n\n"
                "The VM is running in a separate window."
            )
            self._set_state("released")
            return

        resolved = self.vm_manager.resolve_vm_name(self.vm_name) or self.vm_name
        self._finder = WindowFinder(resolved, timeout=30)
        self._finder.found.connect(self._on_window_found)
        self._finder.failed.connect(self._on_window_not_found)
        self._finder.start()

    def _on_window_found(self, hwnd: int):
        try:
            import win32gui
            import win32con

            # Remove the window border / title bar so it looks native
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME |
                       win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX |
                       win32con.WS_SYSMENU)
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style &= ~(win32con.WS_EX_DLGMODALFRAME | win32con.WS_EX_CLIENTEDGE |
                          win32con.WS_EX_STATICEDGE)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

            # Wrap in Qt
            foreign_window = QWindow.fromWinId(hwnd)
            foreign_window.setFlags(Qt.WindowType.FramelessWindowHint)

            self._container = QWidget.createWindowContainer(foreign_window, self._body)
            self._container.setMinimumSize(400, 300)
            self._container.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            # Swap placeholder for container
            self._placeholder.hide()
            self._body_layout.addWidget(self._container)

            self._set_state("embedded")
        except Exception as e:
            self._placeholder.setText(
                f"Could not embed window:\n{e}\n\nVM is running in VirtualBox.")
            self._set_state("released")

    def _on_window_not_found(self):
        self._placeholder.setText(
            f"Could not find the {self.vm_name} window.\n"
            "The VM may still be booting — try pressing Embed again."
        )
        self._set_state("released")

    def _detach_container(self):
        """Release the embedded window back to VirtualBox."""
        if self._container:
            try:
                import win32gui
                import win32con
                # Restore the window so it becomes a normal VBox window again
                hwnd = int(self._container.winId())
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style |= win32con.WS_CAPTION | win32con.WS_THICKFRAME
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            except Exception:
                pass
            self._body_layout.removeWidget(self._container)
            self._container.deleteLater()
            self._container = None
        self._placeholder.show()

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _set_state(self, state: str):
        self._state = state

        self._start_btn.hide()
        self._embed_btn.hide()
        self._release_btn.hide()
        self._stop_btn.hide()

        if state == "stopped":
            self._placeholder.setText("VM not running\nPress ▶ Start to launch")
            self._start_btn.show()

        elif state in ("starting", "stopping"):
            pass   # placeholder text set by caller

        elif state == "embedded":
            self._release_btn.show()
            self._stop_btn.show()

        elif state == "released":
            self._placeholder.setText(
                f"{self.vm_name} is running in a separate window.\n"
                "Press ⬛ Embed to bring it in-app."
            )
            self._embed_btn.show()
            self._stop_btn.show()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def deleteLater(self):
        self._poll_timer.stop()
        self._detach_container()
        super().deleteLater()