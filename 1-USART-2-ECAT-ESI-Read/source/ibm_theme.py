"""IBM Carbon Design System — PyQt5 QSS."""


def get_ibm_stylesheet() -> str:
    return """
    /* ═══════════════════════════════════════════════════
       IBM Carbon Design System
       Canvas: #ffffff, Ink: #161616, Accent: #0f62fe
       Square geometry: 0–4px radius
       ═══════════════════════════════════════════════════ */

    * {
        font-family: "IBM Plex Sans", "Segoe UI", "Arial", sans-serif;
    }

    QMainWindow {
        background-color: #ffffff;
    }
    QWidget#centralWidget {
        background-color: #ffffff;
    }

    /* ── Top header bar ─────────────────────────────── */
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
    QLabel#connBadge {
        color: #161616;
        background-color: #24a148;
        border-radius: 8px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
    }
    QLabel#connBadgeOff {
        color: #c6c6c6;
        background-color: #525252;
        border-radius: 8px;
        padding: 2px 10px;
        font-size: 11px;
    }

    /* ── Buttons ────────────────────────────────────── */
    QPushButton {
        background-color: #0f62fe;
        color: #ffffff;
        border: none;
        border-radius: 0px;
        padding: 5px 10px;
        font-size: 12px;
        min-height: 24px;
        min-width: 50px;
    }
    QPushButton:hover {
        background-color: #0050e6;
    }
    QPushButton:pressed {
        background-color: #002d9c;
    }
    QPushButton:disabled {
        background-color: #c6c6c6;
        color: #525252;
    }
    QPushButton#secondaryBtn {
        background-color: #f4f4f4;
        color: #161616;
        border: 1px solid #161616;
    }
    QPushButton#secondaryBtn:hover {
        background-color: #e0e0e0;
    }
    QPushButton#connectBtn {
        background-color: #24a148;
        color: #161616;
        border: 1px solid #1c7a38;
        border-radius: 0px;
        padding: 5px 14px;
        font-size: 13px;
        font-weight: 700;
        min-height: 28px;
        min-width: 70px;
    }
    QPushButton#connectBtn:hover {
        background-color: #1c7a38;
        border-color: #155d2b;
    }
    QPushButton#connectBtn:pressed {
        background-color: #155d2b;
    }
    QPushButton#connectBtn:disabled {
        background-color: #e0e0e0;
        color: #8c8c8c;
        border: 1px solid #c6c6c6;
    }
    QPushButton#disconnectBtn {
        background-color: #da1e28;
        color: #161616;
        border: 1px solid #b11821;
        border-radius: 0px;
        padding: 5px 14px;
        font-size: 13px;
        font-weight: 700;
        min-height: 28px;
        min-width: 70px;
    }
    QPushButton#disconnectBtn:hover {
        background-color: #b11821;
        border-color: #8e1319;
    }
    QPushButton#disconnectBtn:pressed {
        background-color: #8e1319;
    }
    QPushButton#disconnectBtn:disabled {
        background-color: #e0e0e0;
        color: #8c8c8c;
        border: 1px solid #c6c6c6;
    }

    /* ── Line Edits ─────────────────────────────────── */
    QLineEdit {
        background-color: #f4f4f4;
        color: #161616;
        border: none;
        border-bottom: 1px solid #8c8c8c;
        padding: 8px 0px;
        font-size: 14px;
    }
    QLineEdit:focus {
        border-bottom: 2px solid #0f62fe;
        background-color: #ffffff;
    }
    QLineEdit:disabled {
        background-color: #ffffff;
        color: #8c8c8c;
        border-bottom: 1px solid #e0e0e0;
    }

    /* ── Combo Boxes ────────────────────────────────── */
    QComboBox {
        background-color: #f4f4f4;
        color: #161616;
        border: none;
        border-bottom: 1px solid #8c8c8c;
        padding: 8px 4px;
        font-size: 14px;
        min-height: 20px;
    }
    QComboBox:focus {
        border-bottom: 2px solid #0f62fe;
    }
    QComboBox:disabled {
        background-color: #ffffff;
        color: #8c8c8c;
        border-bottom: 1px solid #e0e0e0;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        selection-background-color: #0f62fe;
        selection-color: #ffffff;
        outline: none;
    }

    /* ── Text Edit ──────────────────────────────────── */
    QTextEdit {
        background-color: #f4f4f4;
        color: #161616;
        border: 1px solid #e0e0e0;
        padding: 12px;
        font-size: 14px;
        font-family: "IBM Plex Mono", "Consolas", "Courier New", monospace;
    }
    QTextEdit:focus {
        border: 1px solid #0f62fe;
        background-color: #ffffff;
    }

    /* ── Tables ─────────────────────────────────────── */
    QTableWidget {
        background-color: #ffffff;
        color: #161616;
        border: 1px solid #e0e0e0;
        gridline-color: #e0e0e0;
        font-size: 14px;
        outline: none;
    }
    QTableWidget::item {
        padding: 6px 12px;
        border-bottom: 1px solid #e0e0e0;
    }
    QTableWidget::item:selected {
        background-color: #0f62fe;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #f4f4f4;
        color: #161616;
        border: none;
        border-bottom: 1px solid #161616;
        padding: 10px 12px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.32px;
    }
    QTableWidget::item:alternate {
        background-color: #f4f4f4;
    }

    /* ── Tabs ───────────────────────────────────────── */
    QTabWidget {
        border: none;
        margin: 0px;
        padding: 0px;
    }
    QTabWidget::pane {
        border: none;
        border-top: 1px solid #e0e0e0;
        background-color: #ffffff;
        top: -1px;
        padding: 0px;
        margin: 0px;
    }
    QTabBar {
        margin-top: 0px;
        margin-bottom: 0px;
    }
    QTabBar::tab {
        background: transparent;
        color: #525252;
        border: none;
        border-bottom: 3px solid transparent;
        padding: 8px 16px 6px 16px;
        font-size: 14px;
        font-weight: 400;
        margin: 0;
    }
    QTabBar::tab:selected {
        color: #161616;
        font-weight: 600;
        border-bottom: 3px solid #0f62fe;
    }
    QTabBar::tab:hover:!selected {
        color: #161616;
        border-bottom: 3px solid #e0e0e0;
    }

    /* ── Group Boxes ────────────────────────────────── */
    QGroupBox {
        border: 1px solid #e0e0e0;
        font-size: 14px;
        font-weight: 600;
        color: #161616;
        margin-top: 8px;
        padding: 16px 12px 12px 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0px 4px;
    }

    /* ── Labels ──────────────────────────────────────── */
    QLabel {
        color: #161616;
        font-size: 14px;
        border: none;
        background: transparent;
    }
    QLabel#statusLabel {
        color: #525252;
        font-size: 13px;
    }
    QLabel#guideLabel {
        color: #161616;
        font-size: 13px;
    }
    QLabel#sectionTitle {
        color: #161616;
        font-size: 20px;
        font-weight: 400;
    }
    QLabel#connectedLabel {
        color: #24a148;
        font-size: 14px;
        font-weight: 600;
    }
    QLabel#disconnectedLabel {
        color: #8c8c8c;
        font-size: 14px;
    }

    /* ── Check Boxes ────────────────────────────────── */
    QCheckBox {
        color: #161616;
        font-size: 14px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #161616;
        background-color: transparent;
    }
    QCheckBox::indicator:checked {
        background-color: #0f62fe;
        border: 1px solid #0f62fe;
    }

    /* ── Splitter ───────────────────────────────────── */
    QSplitter::handle {
        background-color: #e0e0e0;
        width: 1px;
    }
    QSplitter::handle:hover {
        background-color: #0f62fe;
    }

    /* ── Scroll Bars ────────────────────────────────── */
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
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
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
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    /* ── Status Bar ─────────────────────────────────── */
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

    /* ── Menu ───────────────────────────────────────── */
    QMenuBar {
        background-color: #ffffff;
        color: #161616;
        border-bottom: 1px solid #e0e0e0;
        font-size: 14px;
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
        font-size: 14px;
    }
    QMenu::item:selected {
        background-color: #0f62fe;
        color: #ffffff;
    }
    """
