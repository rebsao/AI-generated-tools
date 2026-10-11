"""MP3 Player — 本地音乐播放器（PyQt5 / IBM Carbon 风格）。"""
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from player_page import PlayerPage
from theme import get_theme_stylesheet


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MP3 Player")
        self.resize(1160, 720)
        self.setAcceptDrops(True)
        self._build_ui()
        self._center_on_screen()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 顶部标题栏 ──
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(52)
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(20, 0, 20, 0)

        app_title = QLabel("MP3 Player")
        app_title.setObjectName("appTitle")
        self._subtitle = QLabel("未打开文件夹")
        self._subtitle.setObjectName("appSubtitle")
        hlay.addWidget(app_title)
        hlay.addWidget(self._subtitle)
        hlay.addStretch(1)
        root.addWidget(header)

        # ── 主页面 ──
        self._page = PlayerPage(self._show_status, self._on_folder_changed)
        root.addWidget(self._page, stretch=1)

        # ── 菜单 ──
        open_act = QAction("打开文件夹…", self)
        open_act.setShortcut(QKeySequence("Ctrl+O"))
        open_act.triggered.connect(self._open_folder_dialog)
        file_menu = self.menuBar().addMenu("文件")
        file_menu.addAction(open_act)

        # ── 状态栏 ──
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("就绪 — 打开文件夹开始。", 4000)

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        if self.statusBar():
            self.statusBar().showMessage(message, timeout)

    def _on_folder_changed(self, path: str) -> None:
        self._subtitle.setText(path)
        self._subtitle.setToolTip(path)

    def _open_folder_dialog(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if path:
            self._page.open_folder(path)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Space:
            self._page.toggle_play()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and os.path.isdir(local):
                self._page.open_folder(local)
                return

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            self.move(
                avail.x() + (avail.width() - self.width()) // 2,
                avail.y() + (avail.height() - self.height()) // 2,
            )


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(get_theme_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
