"""IBM Carbon Design System — PyQt5 QSS（适配 MP3 Player）。"""


def get_theme_stylesheet() -> str:
    return """
    /* ═══════════════════════════════════════════════════
       IBM Carbon Design System
       Canvas: #ffffff, Ink: #161616, Accent: #0f62fe
       Square geometry: 0–4px radius
       ═══════════════════════════════════════════════════ */

    * {
        font-family: "Segoe UI", "Microsoft YaHei", "IBM Plex Sans", "Arial", sans-serif;
    }

    QMainWindow {
        background-color: #ffffff;
    }
    QWidget#centralWidget {
        background-color: #ffffff;
    }

    /* ── 顶部标题栏 ─────────────────────────────────── */
    QWidget#headerBar {
        background-color: #161616;
    }
    QWidget#headerBar QLabel {
        color: #ffffff;
        background: transparent;
        border: none;
    }
    QLabel#appTitle {
        color: #ffffff;
        font-size: 18px;
        font-weight: 600;
    }
    QLabel#appSubtitle {
        color: #c6c6c6;
        font-size: 13px;
    }

    /* ── 左侧文件树面板 ─────────────────────────────── */
    QWidget#explorerPanel {
        background-color: #f4f4f4;
        border-right: 1px solid #e0e0e0;
    }
    QLabel#pathLabel {
        color: #525252;
        font-size: 12px;
    }
    QPushButton#openFolderBtn {
        background-color: #0f62fe;
        color: #ffffff;
        border: none;
        border-radius: 0px;
        padding: 6px 12px;
        font-size: 13px;
        font-weight: 600;
        min-height: 20px;
    }
    QPushButton#openFolderBtn:hover {
        background-color: #0050e6;
    }
    QPushButton#openFolderBtn:pressed {
        background-color: #002d9c;
    }
    QTreeView#explorerTree {
        background-color: #ffffff;
        border: none;
        font-size: 13px;
        outline: none;
    }
    QTreeView#explorerTree::item {
        height: 26px;
        padding: 0px 4px;
    }
    QTreeView#explorerTree::item:hover {
        background-color: #e0e0e0;
    }
    QTreeView#explorerTree::item:selected {
        background-color: #0f62fe;
        color: #ffffff;
    }
    QTreeView#explorerTree::branch {
        background: transparent;
    }

    /* ── 标签 ───────────────────────────────────────── */
    QLabel#sectionTitle {
        color: #161616;
        font-size: 18px;
        font-weight: 400;
    }
    QLabel#statusLabel {
        color: #525252;
        font-size: 13px;
    }
    QLabel#emptyLabel {
        color: #8c8c8c;
        font-size: 14px;
    }
    QLabel#nowLabel {
        color: #161616;
        font-size: 13px;
        font-weight: 600;
    }
    QLabel#timeLabel {
        color: #525252;
        font-size: 12px;
        font-family: "Consolas", "Courier New", monospace;
    }

    /* ── 音乐列表表格 ───────────────────────────────── */
    QTableWidget {
        background-color: #ffffff;
        color: #161616;
        border: 1px solid #e0e0e0;
        gridline-color: #e0e0e0;
        font-size: 13px;
        outline: none;
    }
    QTableWidget::item {
        padding: 0px 10px;
        border-bottom: 1px solid #f4f4f4;
    }
    QTableWidget::item:selected {
        background-color: #0f62fe;
        color: #ffffff;
    }
    QTableWidget::item:alternate {
        background-color: #f4f4f4;
    }
    QHeaderView::section {
        background-color: #f4f4f4;
        color: #161616;
        border: none;
        border-bottom: 1px solid #161616;
        padding: 8px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    QTableCornerButton::section {
        background-color: #f4f4f4;
        border: none;
    }

    /* ── 底部播放控制条 ─────────────────────────────── */
    QWidget#playerBar {
        background-color: #ffffff;
        border-top: 1px solid #e0e0e0;
    }
    QPushButton#modeBtn {
        background-color: #f4f4f4;
        color: #161616;
        border: 1px solid #e0e0e0;
        border-radius: 0px;
        padding: 4px 10px;
        font-size: 12px;
        min-width: 64px;
    }
    QPushButton#modeBtn:hover {
        background-color: #e0e0e0;
    }
    QPushButton#modeBtn:pressed {
        background-color: #c6c6c6;
    }
    QPushButton#ctrlBtn {
        background-color: transparent;
        color: #161616;
        border: 1px solid transparent;
        border-radius: 0px;
        padding: 4px 10px;
        font-size: 12px;
    }
    QPushButton#ctrlBtn:hover {
        background-color: #e0e0e0;
    }
    QPushButton#ctrlBtn:pressed {
        background-color: #c6c6c6;
    }
    QPushButton#playBtn {
        background-color: #0f62fe;
        color: #ffffff;
        border: none;
        border-radius: 0px;
        padding: 4px 12px;
        font-size: 13px;
        font-weight: 600;
        min-width: 76px;
    }
    QPushButton#playBtn:hover {
        background-color: #0050e6;
    }
    QPushButton#playBtn:pressed {
        background-color: #002d9c;
    }
    QPushButton#playBtn:disabled {
        background-color: #c6c6c6;
        color: #525252;
    }

    /* ── 滑条 ───────────────────────────────────────── */
    QSlider::groove:horizontal {
        height: 4px;
        background: #e0e0e0;
    }
    QSlider::sub-page:horizontal {
        background: #0f62fe;
    }
    QSlider::add-page:horizontal {
        background: #e0e0e0;
    }
    QSlider::handle:horizontal {
        background: #161616;
        width: 14px;
        height: 14px;
        margin: -5px 0px;
    }
    QSlider::handle:horizontal:hover {
        background: #0f62fe;
    }

    /* ── 滚动条 ─────────────────────────────────────── */
    QScrollBar:vertical {
        background: #ffffff;
        width: 10px;
        border: none;
    }
    QScrollBar::handle:vertical {
        background: #e0e0e0;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #8c8c8c;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar:horizontal {
        background: #ffffff;
        height: 10px;
        border: none;
    }
    QScrollBar::handle:horizontal {
        background: #e0e0e0;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #8c8c8c;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

    /* ── 状态栏 ─────────────────────────────────────── */
    QStatusBar {
        background-color: #161616;
        color: #c6c6c6;
        font-size: 12px;
        border: none;
        padding: 4px 16px;
    }
    QStatusBar::item { border: none; }
    QStatusBar QLabel {
        color: #c6c6c6;
        font-size: 12px;
        background: transparent;
    }

    /* ── 菜单 ───────────────────────────────────────── */
    QMenuBar {
        background-color: #ffffff;
        color: #161616;
        border-bottom: 1px solid #e0e0e0;
        font-size: 13px;
        padding: 4px 8px;
    }
    QMenuBar::item:selected { background-color: #f4f4f4; }
    QMenu {
        background-color: #ffffff;
        color: #161616;
        border: 1px solid #e0e0e0;
        padding: 4px;
    }
    QMenu::item {
        padding: 8px 32px 8px 16px;
        font-size: 13px;
    }
    QMenu::item:selected {
        background-color: #0f62fe;
        color: #ffffff;
    }

    QStackedWidget {
        background-color: #ffffff;
    }
    """
