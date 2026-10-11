"""CCAT — EtherCAT ESI & 串口工具 Suite. Single-window, tabbed. IBM Carbon theme."""
import os
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplashScreen,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from esi_page import EsiPage
from ibm_theme import get_ibm_stylesheet
from serial_page import SerialPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CCAT")
        self.resize(1280, 800)
        self._build_ui()
        self._center_on_screen()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ──
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(52)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(20, 0, 20, 0)

        app_title = QLabel("CCAT")
        app_title.setObjectName("appTitle")
        app_subtitle = QLabel("")
        app_subtitle.setObjectName("appSubtitle")

        self._conn_badge = QLabel("USART: NO")
        self._conn_badge.setObjectName("connBadgeOff")

        hlay.addWidget(app_title)
        hlay.addWidget(app_subtitle)
        hlay.addStretch(1)
        hlay.addWidget(self._conn_badge)
        root.addWidget(header)

        # ── Tab widget ──
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        root.addWidget(self._tabs, stretch=1)

        # Serial tab
        self._serial_page = SerialPage()
        self._tabs.addTab(self._serial_page, "USART")

        # ESI tab
        def _status_cb(message: str, timeout: int = 3000) -> None:
            s = self.statusBar()
            if s:
                s.showMessage(message, timeout)

        self._esi_page = EsiPage(_status_cb)
        self._tabs.addTab(self._esi_page, "ESI Read")

        # Connect serial status tracking
        self._serial_timer = QTimer(self)
        self._serial_timer.timeout.connect(self._update_serial_badge)
        self._serial_timer.start(1000)

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("就绪 — 选择标签页开始。", 4000)

    def _update_serial_badge(self) -> None:
        info = self._serial_page.status_info()
        if info.startswith("端口:"):
            self._conn_badge.setText("USART: YES")
            self._conn_badge.setObjectName("connBadge")
            self._conn_badge.style().unpolish(self._conn_badge)
            self._conn_badge.style().polish(self._conn_badge)
        else:
            self._conn_badge.setText("USART: NO")
            self._conn_badge.setObjectName("connBadgeOff")

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            self.move(
                avail.x() + (avail.width() - self.width()) // 2,
                avail.y() + (avail.height() - self.height()) // 2,
            )


def _load_splash(app: QApplication) -> QSplashScreen | None:
    """Load and show a fullscreen splash from 祖国人.webp if available."""
    # PyInstaller bundled path; fallback to dev path
    if getattr(sys, "frozen", False):
        img_path = os.path.join(sys._MEIPASS, "祖国人.webp")
    else:
        src_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(src_dir, "..", "祖国人.webp")

    if not os.path.exists(img_path):
        return None

    pix = QPixmap(img_path)
    if pix.isNull():
        return None

    screen = app.primaryScreen()
    if screen:
        pix = pix.scaled(screen.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    splash = QSplashScreen(pix)
    splash.show()
    app.processEvents()
    return splash


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(get_ibm_stylesheet())

    splash = _load_splash(app)

    window = MainWindow()

    def _show_main() -> None:
        if splash:
            splash.close()
        window.show()

    if splash:
        QTimer.singleShot(1000, _show_main)
    else:
        window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
