"""
VM Embed Widget
Starts a VirtualBox VM and embeds its window directly inside the application.
Uses ctypes (built-in) — no extra dependencies required.
"""

import ctypes
import ctypes.wintypes as wintypes
import platform
import time
import threading

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QSizePolicy, QFrame, QDialog,
                              QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QWindow, QKeySequence, QShortcut

from utils.styles import COLORS, START_BUTTON_STYLE, STOP_BUTTON_STYLE
from core.vm_manager import VMWorker

# Compact button style for the 28 px toolbar (LAUNCH_BUTTON_STYLE has 15 px padding, too tall)
_ICON_BTN_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 5px;
        padding: 0px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_tertiary']};
        color: {COLORS['text_primary']};
    }}
"""

_BAR_BTN_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['accent_blue']};
        color: white;
        border: none;
        padding: 2px 10px;
        border-radius: 5px;
    }}
    QPushButton:hover {{ background-color: {COLORS['accent_blue_hover']}; }}
"""

# ---------------------------------------------------------------------------
# Win32 constants & helpers (ctypes — no pywin32 needed)
# ---------------------------------------------------------------------------

GWL_STYLE      = -16
GWL_EXSTYLE    = -20
WS_CAPTION      = 0x00C00000
WS_THICKFRAME   = 0x00040000
WS_MINIMIZEBOX  = 0x00020000
WS_MAXIMIZEBOX  = 0x00010000
WS_SYSMENU      = 0x00080000
WS_EX_DLGMODALFRAME = 0x00000001
WS_EX_CLIENTEDGE    = 0x00000200
WS_EX_STATICEDGE    = 0x00020000
SWP_FRAMECHANGED    = 0x0020
SWP_NOMOVE          = 0x0002
SWP_NOSIZE          = 0x0001
SWP_NOZORDER        = 0x0004
SW_SHOW             = 5
HWND_TOP            = 0


def _find_vbox_window(search: str) -> int | None:
    """Return the HWND of a visible VirtualBox window whose title contains *search*."""
    if platform.system() != "Windows":
        return None

    user32 = ctypes.windll.user32
    results = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def _cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if search.lower() in title and "virtualbox" in title:
                    results.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return results[0] if results else None


def _strip_chrome(hwnd: int):
    """Remove the title bar and border from a window."""
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
    user32.SetWindowLongW(hwnd, GWL_STYLE, style)

    ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ex &= ~(WS_EX_DLGMODALFRAME | WS_EX_CLIENTEDGE | WS_EX_STATICEDGE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)

    user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)


def _restore_chrome(hwnd: int):
    """Restore the title bar and border so VirtualBox gets its window back."""
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    style |= WS_CAPTION | WS_THICKFRAME | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
    user32.SetWindowLongW(hwnd, GWL_STYLE, style)
    user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
    user32.ShowWindow(hwnd, SW_SHOW)


# ---------------------------------------------------------------------------
# WindowFinder — polls for the VirtualBox window after VM starts
# ---------------------------------------------------------------------------

class WindowFinder(QThread):
    found  = pyqtSignal(int)   # HWND
    failed = pyqtSignal()

    def __init__(self, search: str, timeout: float = 60.0, parent=None):
        super().__init__(parent)
        self._search  = search
        self._timeout = timeout

    def run(self):
        deadline = time.time() + self._timeout
        while time.time() < deadline:
            hwnd = _find_vbox_window(self._search)
            if hwnd:
                self.found.emit(hwnd)
                return
            time.sleep(0.5)
        self.failed.emit()


# ---------------------------------------------------------------------------
# VMEmbedWidget
# ---------------------------------------------------------------------------

class _KeyboardHelpDialog(QDialog):
    """Keyboard shortcuts and VM interaction tips."""

    _SECTIONS = [
        ("Mouse & Keyboard Capture", [
            ("Click inside the VM",        "Capture mouse and keyboard — input goes to the VM"),
            ("Right Ctrl",                 "Release mouse/keyboard back to your host PC"),
            ("Right Ctrl + Del",           "Send Ctrl+Alt+Delete to the VM"),
        ]),
        ("Fullscreen", [
            ("F11  or  [ ] button",        "Toggle VM-only fullscreen (VM fills the whole screen)"),
            ("F11  or  Esc (in fullscreen)","Exit VM fullscreen and return to the app"),
            ("Right Ctrl + F",             "Toggle VirtualBox native fullscreen for this VM"),
        ]),
        ("Copy & Paste", [
            ("Ctrl+C  /  Ctrl+V",          "Copy/paste within the VM (normal shortcuts)"),
            ("Right Ctrl + S",             "Take a VirtualBox screenshot"),
        ]),
        ("Linux VM Shortcuts", [
            ("Super key (Win key)",        "Open the applications menu / activity overview"),
            ("Ctrl+Alt+T",                 "Open a terminal"),
            ("Ctrl+Alt+F2  …  F6",         "Switch to a different TTY (text console)"),
            ("Ctrl+Alt+F7  or  F1",        "Return to the graphical desktop"),
            ("Alt+F2",                     "Run a command (GNOME / KDE)"),
            ("Ctrl+L",                     "Clear the terminal"),
            ("Tab",                        "Autocomplete commands and file paths"),
            ("Up / Down arrow",            "Scroll through previous commands"),
        ]),
        ("VirtualBox Host Keys", [
            ("Right Ctrl + H",             "Hibernate (save state) the VM"),
            ("Right Ctrl + P",             "Pause / resume the VM"),
            ("Right Ctrl + R",             "Reset (hard reboot) the VM"),
            ("Right Ctrl + Q",             "Close the VM window"),
        ]),
        ("If Something Goes Wrong", [
            ("Mouse stuck inside VM",      "Press Right Ctrl to release it"),
            ("Keyboard not responding",    "Click somewhere outside the VM, then back in"),
            ("VM window disappeared",      "Press the Embed button in the toolbar"),
            ("VM froze",                   "Click Stop in the toolbar, then Start to restore snapshot"),
        ]),
    ]

    def __init__(self, vm_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"VM Controls — {vm_name}")
        self.setMinimumWidth(620)
        self.setMinimumHeight(500)
        self.setModal(True)
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']}; color: {COLORS['text_primary']};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel(f"Using the VM: {vm_name}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 20px 24px 8px 24px;")
        outer.addWidget(title)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 8, 24, 24)
        layout.setSpacing(20)

        for section_title, rows in self._SECTIONS:
            # Section header
            hdr = QLabel(section_title)
            hdr.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            hdr.setStyleSheet(f"color: {COLORS['accent_blue']}; margin-top: 4px;")
            layout.addWidget(hdr)

            # Table frame
            frame = QFrame()
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                }}
            """)
            grid = QVBoxLayout(frame)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(0)

            for i, (key, desc) in enumerate(rows):
                row_widget = QWidget()
                bg = COLORS['bg_secondary'] if i % 2 == 0 else COLORS['bg_primary']
                row_widget.setStyleSheet(f"background-color: {bg}; border: none;")
                row = QHBoxLayout(row_widget)
                row.setContentsMargins(14, 8, 14, 8)
                row.setSpacing(16)

                key_lbl = QLabel(key)
                key_lbl.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
                key_lbl.setStyleSheet(f"""
                    color: {COLORS['text_primary']};
                    background-color: {COLORS['bg_tertiary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 2px 8px;
                """)
                key_lbl.setFixedWidth(220)
                key_lbl.setWordWrap(True)
                row.addWidget(key_lbl)

                desc_lbl = QLabel(desc)
                desc_lbl.setFont(QFont("Arial", 10))
                desc_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; border: none;")
                desc_lbl.setWordWrap(True)
                row.addWidget(desc_lbl, stretch=1)

                grid.addWidget(row_widget)

            layout.addWidget(frame)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Arial", 10))
        close_btn.setMinimumHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin: 12px 24px;
                padding: 0 20px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border_hover']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        outer.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


class _VMFullscreenOverlay(QWidget):
    """
    Top-level frameless window that hosts the embedded VM widget in fullscreen.
    The VM container is re-parented into this overlay on enter, and back out on exit.
    """

    exit_requested = pyqtSignal()

    def __init__(self, vm_name: str, parent=None):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(f"{vm_name} — Fullscreen")
        self.setStyleSheet("background-color: black;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Thin top bar ──────────────────────────────────────────────
        bar = QWidget()
        bar.setFixedHeight(36)
        bar.setStyleSheet(f"""
            background-color: {COLORS['bg_secondary']};
            border-bottom: 1px solid {COLORS['border']};
        """)
        bar_row = QHBoxLayout(bar)
        bar_row.setContentsMargins(14, 0, 14, 0)
        bar_row.setSpacing(12)

        name_lbl = QLabel(vm_name)
        name_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {COLORS['text_primary']};")
        bar_row.addWidget(name_lbl)

        bar_row.addStretch()

        hint = QLabel("F11 or Esc to exit")
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet(f"color: {COLORS['text_secondary']};")
        bar_row.addWidget(hint)

        exit_btn = QPushButton("Exit Fullscreen")
        exit_btn.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setFixedHeight(26)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 0 12px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border_hover']}; }}
        """)
        exit_btn.clicked.connect(self.exit_requested)
        bar_row.addWidget(exit_btn)

        root.addWidget(bar)

        # ── VM container area ─────────────────────────────────────────
        self._area = QWidget()
        self._area.setStyleSheet("background-color: black;")
        self._area_layout = QVBoxLayout(self._area)
        self._area_layout.setContentsMargins(0, 0, 0, 0)
        self._area_layout.setSpacing(0)
        root.addWidget(self._area, stretch=1)

        # Keyboard shortcuts
        QShortcut(QKeySequence("F11"),    self).activated.connect(self.exit_requested)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.exit_requested)


class VMEmbedWidget(QFrame):
    """
    Shows a VM screen embedded inside the app.

    States:
      not_created — VM has never been provisioned  → shows Provision button
      stopped     — VM exists but is off           → shows Start button
      starting    — waiting / embedding            → shows spinner text
      embedded    — VM window is inside the app    → shows Pop Out + Stop
      released    — VM running in separate window  → shows Embed + Stop
    """

    def __init__(self, display_name: str, vbox_name: str, vm_manager,
                 vagrant_manager=None, scenario_id: str = None,
                 scenario: dict = None, parent=None):
        super().__init__(parent)
        self.display_name    = display_name
        self.vbox_name       = vbox_name
        self.vm_manager      = vm_manager
        self.vagrant_manager = vagrant_manager
        self.scenario_id     = scenario_id
        self.scenario        = scenario

        self._state          = "stopped"
        self._embedded_hwnd  = None     # HWND of the currently embedded window
        self._container      = None     # QWidget wrapping the foreign QWindow
        self._fs_overlay     = None     # _VMFullscreenOverlay when in VM fullscreen
        self._finder         = None
        self._worker         = None
        self._pollers        = []

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._refresh_status)
        self._poll_timer.start(5000)

        self._setup_ui()
        self._refresh_status()

    # ------------------------------------------------------------------
    # UI setup
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
        self.setMinimumHeight(200)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._root_layout = root

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
        bar_row = QHBoxLayout(bar)
        bar_row.setContentsMargins(12, 0, 12, 0)
        bar_row.setSpacing(8)

        self._title_lbl = QLabel(self.display_name)
        self._title_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self._title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        bar_row.addWidget(self._title_lbl)

        self._dot = QLabel("●")
        self._dot.setFont(QFont("Arial", 10))
        self._dot.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none;")
        bar_row.addWidget(self._dot)

        bar_row.addStretch()

        def _btn(label, style, slot):
            b = QPushButton(label)
            b.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            b.setStyleSheet(style)
            b.setFixedHeight(28)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(slot)
            b.hide()
            bar_row.addWidget(b)
            return b

        self._provision_btn = _btn("Provision",  _BAR_BTN_STYLE,     self._on_provision)
        self._start_btn     = _btn("Start",      START_BUTTON_STYLE, self._on_start)
        self._embed_btn     = _btn("Embed",      _BAR_BTN_STYLE,     self._on_embed)
        self._popout_btn    = _btn("Pop Out",    _BAR_BTN_STYLE,     self._on_popout)
        self._stop_btn      = _btn("Stop",       STOP_BUTTON_STYLE,  self._on_stop)
        self._delete_btn    = _btn("Delete VM",  STOP_BUTTON_STYLE,  self._on_delete)

        # Always-visible utility buttons (not toggled by _set_state)
        _sep = QLabel("|")
        _sep.setStyleSheet(f"color: {COLORS['border']}; border: none;")
        bar_row.addWidget(_sep)

        self._fs_btn = QPushButton("[ ]")
        self._fs_btn.setToolTip("VM Fullscreen  (F11)")
        self._fs_btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self._fs_btn.setStyleSheet(_ICON_BTN_STYLE)
        self._fs_btn.setFixedSize(32, 28)
        self._fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fs_btn.clicked.connect(self._on_fullscreen)
        bar_row.addWidget(self._fs_btn)

        self._help_btn = QPushButton("?")
        self._help_btn.setToolTip("Keyboard shortcuts & tips")
        self._help_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self._help_btn.setStyleSheet(_ICON_BTN_STYLE)
        self._help_btn.setFixedSize(28, 28)
        self._help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_btn.clicked.connect(self._on_help)
        bar_row.addWidget(self._help_btn)

        root.addWidget(bar)

        # F11 shortcut for fullscreen
        fs_shortcut = QShortcut(QKeySequence("F11"), self)
        fs_shortcut.activated.connect(self._on_fullscreen)

        # ── Body ─────────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._body, stretch=1)

        self._placeholder = QLabel()
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setFont(QFont("Arial", 12))
        self._placeholder.setStyleSheet(f"color: {COLORS['text_tertiary']}; border: none;")
        self._placeholder.setWordWrap(True)
        self._body_layout.addWidget(self._placeholder)

    # ------------------------------------------------------------------
    # Status polling
    # ------------------------------------------------------------------

    def _refresh_status(self):
        if self._state in ("starting", "stopping"):
            return
        poller = self.vm_manager.poll_state_async(self.vbox_name)
        self._pollers.append(poller)
        poller.state_ready.connect(self._on_state)
        poller.state_ready.connect(lambda _: self._pollers.remove(poller)
                                   if poller in self._pollers else None)
        poller.start()

    def _on_state(self, state: str):
        dot_colors = {
            "running":  COLORS["success"],
            "poweroff": COLORS["text_tertiary"],
            "aborted":  COLORS["danger"],
            "paused":   COLORS["warning"],
            "saved":    COLORS["warning"],
            "unknown":  COLORS["text_tertiary"],
        }
        self._dot.setStyleSheet(
            f"color: {dot_colors.get(state, COLORS['text_tertiary'])}; border: none;")
        self._dot.setToolTip(state.capitalize())

        if self._state in ("embedded", "starting", "stopping"):
            return  # don't override active states

        if state in ("poweroff", "aborted", "saved", "unknown"):
            # Check if it was never provisioned
            if not self.vm_manager.vm_exists(self.vbox_name):
                self._set_state("not_created")
            else:
                self._set_state("stopped")
        elif state == "running" and self._state == "stopped":
            self._set_state("released")

    # ------------------------------------------------------------------
    # Button actions
    # ------------------------------------------------------------------

    def _on_provision(self):
        """First-time Vagrant provisioning."""
        if not self.vagrant_manager or not self.scenario_id:
            return
        if self._state == "starting":
            return   # already in progress — ignore double-click

        from UI.vm_storage_dialog import VMStorageDialog
        scenario_name = self.scenario.get("name") if self.scenario else None
        if not VMStorageDialog.ensure_configured(self, scenario_name=scenario_name):
            return

        self._set_state("starting")
        self._placeholder.setText(f"Provisioning {self.display_name}\n(first-time setup — this may take a while)")

        from UI.widgets import VagrantOutputDialog
        dlg = VagrantOutputDialog(f"Provisioning {self.display_name}", self)
        self._vagrant_dlg = dlg
        dlg.finished.connect(lambda: setattr(self, '_vagrant_dlg', None))
        dlg.show()

        def _safe_call(fn, *args):
            """Call fn only if the dialog still exists as a live Qt object."""
            try:
                if self._vagrant_dlg is not None:
                    fn(*args)
            except RuntimeError:
                # Dialog's C++ object was already deleted
                pass

        def _done(ok):
            if ok:
                _safe_call(dlg.mark_done, True)
                self._do_start_and_embed()
            else:
                _safe_call(dlg.mark_done, False)
                self._set_state("not_created")

        self.vagrant_manager.up_async(
            self.scenario_id, self.display_name,
            output_cb=lambda line: _safe_call(dlg.append_line, line),
            done_cb=_done,
        )

    def _on_start(self):
        self._set_state("starting")
        self._placeholder.setText(f"Starting {self.display_name}…")
        self._do_start_and_embed()

    def _do_start_and_embed(self):
        """Restore snapshot (if configured and exists), start VM, then embed its window."""
        snapshot = self.scenario.get("snapshots", {}).get(self.display_name) if self.scenario else None

        # Only restore snapshot if it actually exists — otherwise just boot normally
        if snapshot and not self.vm_manager.snapshot_exists(self.vbox_name, snapshot):
            snapshot = None

        def _launch():
            ok, msg = self.vm_manager.launch_scenario_vm(self.vbox_name, snapshot)
            return ok

        worker = VMWorker(_launch)
        self._worker = worker
        worker.finished.connect(self._on_launch_done)
        worker.start()

    def _on_launch_done(self, success: bool, msg: str):
        if not success:
            self._placeholder.setText(f"Failed to start {self.display_name}.\n{msg}")
            self._set_state("stopped")
            return
        self._placeholder.setText(f"Waiting for {self.display_name} window…")
        self._begin_embed()

    def _on_embed(self):
        self._set_state("starting")
        self._placeholder.setText(f"Looking for {self.display_name} window…")
        self._begin_embed()

    def _on_popout(self):
        self._detach_container()
        self._set_state("released")

    def _on_stop(self):
        self._detach_container()
        self._set_state("stopping")
        worker = self.vm_manager.stop_vm_async(self.vbox_name, force=True)
        self._worker = worker
        worker.finished.connect(lambda ok, _: self._set_state("stopped"))
        worker.start()

    def _on_delete(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.warning(
            self,
            "Delete VM",
            f"Permanently delete '{self.display_name}'?\n\n"
            "This will remove the VM and all its files from disk.\n"
            "You will need to run Provision again to use this VM.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_state("stopping")
        self._placeholder.setText(f"Deleting {self.display_name}…")

        worker = self.vm_manager.delete_vm_async(self.vbox_name)
        self._worker = worker

        def _done(ok: bool, msg: str):
            if ok:
                self._set_state("not_created")
            else:
                self._placeholder.setText(f"Failed to delete VM:\n{msg}")
                self._set_state("stopped")

        worker.finished.connect(_done)
        worker.start()

    # ------------------------------------------------------------------
    # Fullscreen & help
    # ------------------------------------------------------------------

    def _on_fullscreen(self):
        """Toggle VM-only fullscreen. If no VM is embedded, does nothing."""
        if not self._container:
            return
        if self._fs_overlay:
            self._exit_vm_fullscreen()
        else:
            self._enter_vm_fullscreen()

    def _enter_vm_fullscreen(self):
        overlay = _VMFullscreenOverlay(vm_name=self.display_name)
        overlay.exit_requested.connect(self._exit_vm_fullscreen)
        self._fs_overlay = overlay

        # Move the container from the body layout into the overlay
        self._body_layout.removeWidget(self._container)
        self._container.setParent(overlay._area)
        overlay._area_layout.addWidget(self._container)
        self._container.show()

        # Show placeholder while VM is in fullscreen overlay
        self._placeholder.setText(
            f"{self.display_name} is in fullscreen.\n"
            "Press F11 or Esc, or click Exit Fullscreen in the overlay bar."
        )
        self._placeholder.show()

        # Show on the same screen as the main window
        overlay.setScreen(self.screen())
        overlay.showFullScreen()
        overlay.raise_()
        overlay.activateWindow()

        self._fs_btn.setText("[x]")
        self._fs_btn.setToolTip("Exit VM fullscreen  (F11)")

    def _exit_vm_fullscreen(self):
        overlay = self._fs_overlay
        if not overlay:
            return
        self._fs_overlay = None

        # Return the container to the body layout
        overlay._area_layout.removeWidget(self._container)
        self._container.setParent(self._body)
        self._placeholder.hide()
        self._body_layout.addWidget(self._container)
        self._container.show()

        overlay.close()
        overlay.deleteLater()

        self._fs_btn.setText("[ ]")
        self._fs_btn.setToolTip("VM Fullscreen  (F11)")

    def _on_help(self):
        dlg = _KeyboardHelpDialog(self.display_name, self)
        dlg.exec()

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

        self._finder = WindowFinder(self.vbox_name, timeout=60)
        self._finder.found.connect(self._on_window_found)
        self._finder.failed.connect(self._on_window_not_found)
        self._finder.start()

    def _on_window_found(self, hwnd: int):
        try:
            _strip_chrome(hwnd)

            foreign_window = QWindow.fromWinId(hwnd)
            foreign_window.setFlags(Qt.WindowType.FramelessWindowHint)

            self._container = QWidget.createWindowContainer(foreign_window, self._body)
            self._container.setMinimumSize(640, 480)
            self._container.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            self._embedded_hwnd = hwnd
            self._placeholder.hide()
            self._body_layout.addWidget(self._container)
            self._set_state("embedded")
        except Exception as e:
            self._placeholder.setText(
                f"Could not embed window:\n{e}\n\nVM is running in VirtualBox.")
            self._set_state("released")

    def _on_window_not_found(self):
        self._placeholder.setText(
            f"Could not find the {self.display_name} window.\n"
            "The VM may still be booting — press Embed to try again."
        )
        self._set_state("released")

    def _detach_container(self):
        # If the container is in the fullscreen overlay, pull it back first
        if self._fs_overlay:
            self._exit_vm_fullscreen()

        if self._embedded_hwnd:
            try:
                _restore_chrome(self._embedded_hwnd)
            except Exception:
                pass
            self._embedded_hwnd = None

        if self._container:
            self._body_layout.removeWidget(self._container)
            self._container.deleteLater()
            self._container = None

        self._placeholder.show()

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _set_state(self, state: str):
        self._state = state

        for btn in (self._provision_btn, self._start_btn, self._embed_btn,
                    self._popout_btn, self._stop_btn, self._delete_btn):
            btn.hide()

        if state == "not_created":
            self._placeholder.setText(
                f"{self.display_name}\n\nNot yet downloaded.\nPress Provision to set up this VM."
            )
            self._provision_btn.show()

        elif state == "stopped":
            self._placeholder.setText(
                f"{self.display_name}\n\nVM is stopped.\nPress Start to launch."
            )
            self._start_btn.show()
            self._delete_btn.show()

        elif state in ("starting", "stopping"):
            pass  # caller sets placeholder text

        elif state == "embedded":
            self._popout_btn.show()
            self._stop_btn.show()

        elif state == "released":
            self._embed_btn.show()
            self._stop_btn.show()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def deleteLater(self):
        self._poll_timer.stop()
        self._detach_container()
        super().deleteLater()


