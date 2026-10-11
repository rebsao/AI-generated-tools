"""PlayerPage — 左侧文件夹树 + 右侧音乐列表 + 底部播放控制条。"""
import os

from PyQt5.QtCore import Qt, QDir, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".ape"}

PLAY_MODES = [
    (QMediaPlaylist.Sequential, "顺序播放"),
    (QMediaPlaylist.Loop, "列表循环"),
    (QMediaPlaylist.CurrentItemInLoop, "单曲循环"),
    (QMediaPlaylist.Random, "随机播放"),
]


def _split_title(filename: str):
    """从文件名猜标题 / 艺术家：'Artist - Title.ext' → ('Title', 'Artist')。"""
    base = os.path.splitext(filename)[0]
    if " - " in base:
        artist, title = base.split(" - ", 1)
        return title.strip(), artist.strip()
    return base, "未知艺术家"


def _fmt_ms(ms: int) -> str:
    ms = max(0, int(ms))
    total = ms // 1000
    return f"{total // 60:02d}:{total % 60:02d}"


class PlayerPage(QWidget):
    def __init__(self, status_cb, folder_cb) -> None:
        super().__init__()
        self._status = status_cb
        self._folder_cb = folder_cb
        self._folder = None
        self._duration_ms = 0
        self._dragging = False
        self._mode_idx = 0

        self._build_media()
        self._build_ui()

    # ── 媒体引擎 ──────────────────────────────────────
    def _build_media(self) -> None:
        self._player = QMediaPlayer(self)
        self._playlist = QMediaPlaylist(self)
        self._player.setPlaylist(self._playlist)
        self._playlist.setPlaybackMode(PLAY_MODES[0][0])

        self._playlist.currentIndexChanged.connect(self._on_current_index_changed)
        self._playlist.playbackModeChanged.connect(self._on_playback_mode_changed)
        self._player.stateChanged.connect(self._on_state_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.error.connect(self._on_player_error)

    # ── 界面构建 ──────────────────────────────────────
    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_explorer())
        root.addWidget(self._build_right_panel(), stretch=1)

    def _build_explorer(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("explorerPanel")
        panel.setFixedWidth(300)
        v = QVBoxLayout(panel)
        v.setContentsMargins(12, 12, 12, 8)
        v.setSpacing(8)

        open_btn = QPushButton("打开文件夹…")
        open_btn.setObjectName("openFolderBtn")
        open_btn.clicked.connect(self._open_folder_dialog)
        v.addWidget(open_btn)

        self._path_label = QLabel("未打开文件夹")
        self._path_label.setObjectName("pathLabel")
        v.addWidget(self._path_label)

        self._fs_model = QFileSystemModel(self)
        self._fs_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self._fs_model.setNameFilters([f"*{e}" for e in sorted(AUDIO_EXTS)])
        self._fs_model.setNameFilterDisables(False)

        self._tree = QTreeView()
        self._tree.setObjectName("explorerTree")
        self._tree.setModel(self._fs_model)
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(14)
        for col in (1, 2, 3):
            self._tree.hideColumn(col)
        self._tree.clicked.connect(self._on_tree_clicked)
        self._tree.doubleClicked.connect(self._on_tree_double_clicked)
        v.addWidget(self._tree, stretch=1)
        return panel

    def _build_right_panel(self) -> QWidget:
        wrap = QWidget()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(16, 12, 16, 10)
        v.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("音乐列表")
        title.setObjectName("sectionTitle")
        self._count_label = QLabel("0 首")
        self._count_label.setObjectName("statusLabel")
        head.addWidget(title)
        head.addStretch(1)
        head.addWidget(self._count_label)
        v.addLayout(head)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["#", "曲名", "艺术家", "时长"])
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setColumnWidth(0, 44)
        self._table.setColumnWidth(2, 160)
        self._table.setColumnWidth(3, 72)
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        empty = QWidget()
        ely = QVBoxLayout(empty)
        el = QLabel("未打开文件夹\n点击左侧「打开文件夹」或将文件夹拖入窗口")
        el.setObjectName("emptyLabel")
        el.setAlignment(Qt.AlignCenter)
        ely.addWidget(el)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._table)
        self._stack.addWidget(empty)
        v.addWidget(self._stack, stretch=1)

        v.addWidget(self._build_player_bar())
        return wrap

    def _build_player_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("playerBar")
        v = QVBoxLayout(bar)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(6)

        # 控制行
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self._mode_btn = QPushButton(PLAY_MODES[0][1])
        self._mode_btn.setObjectName("modeBtn")
        self._mode_btn.setToolTip("点击切换：顺序播放 / 列表循环 / 单曲循环 / 随机播放")
        self._mode_btn.clicked.connect(self._cycle_mode)

        self._prev_btn = QPushButton("上一首")
        self._prev_btn.setObjectName("ctrlBtn")
        self._prev_btn.clicked.connect(self._prev)

        self._play_btn = QPushButton("播放")
        self._play_btn.setObjectName("playBtn")
        self._play_btn.setMinimumWidth(76)
        self._play_btn.clicked.connect(self.toggle_play)

        self._next_btn = QPushButton("下一首")
        self._next_btn.setObjectName("ctrlBtn")
        self._next_btn.clicked.connect(self._next)

        self._now_label = QLabel("未在播放")
        self._now_label.setObjectName("nowLabel")

        row1.addWidget(self._mode_btn)
        row1.addWidget(self._prev_btn)
        row1.addWidget(self._play_btn)
        row1.addWidget(self._next_btn)
        row1.addStretch(1)
        row1.addWidget(self._now_label)
        v.addLayout(row1)

        # 进度行
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self._seek = QSlider(Qt.Horizontal)
        self._seek.setRange(0, 0)
        self._seek.sliderPressed.connect(self._on_seek_pressed)
        self._seek.sliderReleased.connect(self._on_seek_released)
        self._seek.sliderMoved.connect(self._on_seek_moved)

        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setObjectName("timeLabel")

        vol_caption = QLabel("音量")
        vol_caption.setObjectName("statusLabel")
        self._vol = QSlider(Qt.Horizontal)
        self._vol.setRange(0, 100)
        self._vol.setValue(70)
        self._vol.setFixedWidth(110)
        self._vol.valueChanged.connect(self._player.setVolume)

        row2.addWidget(self._seek, stretch=1)
        row2.addWidget(self._time_label)
        row2.addSpacing(12)
        row2.addWidget(vol_caption)
        row2.addWidget(self._vol)
        v.addLayout(row2)

        self._player.setVolume(70)
        return bar

    # ── 文件夹 / 文件树 ───────────────────────────────
    def open_folder(self, path: str) -> None:
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            self._status(f"无法打开文件夹：{path}", 4000)
            return
        self._fs_model.setRootPath(path)
        self._tree.setRootIndex(self._fs_model.index(path))
        self.load_folder(path)

    def load_folder(self, path: str) -> None:
        path = os.path.abspath(path)
        try:
            names = os.listdir(path)
        except OSError as exc:
            self._status(f"读取文件夹失败：{exc}", 5000)
            return

        files = []
        for name in names:
            full = os.path.join(path, name)
            if os.path.isfile(full) and os.path.splitext(name)[1].lower() in AUDIO_EXTS:
                files.append(name)
        files.sort(key=str.lower)

        self._player.stop()
        self._playlist.clear()

        self._folder = path
        self._folder_cb(path)
        self._path_label.setText(path)
        self._path_label.setToolTip(path)

        self._table.setRowCount(len(files))
        for i, name in enumerate(files):
            title, artist = _split_title(name)
            num = QTableWidgetItem(str(i + 1))
            num.setTextAlignment(Qt.AlignCenter)
            t = QTableWidgetItem(title)
            t.setToolTip(os.path.join(path, name))
            a = QTableWidgetItem(artist)
            d = QTableWidgetItem("--:--")
            d.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 0, num)
            self._table.setItem(i, 1, t)
            self._table.setItem(i, 2, a)
            self._table.setItem(i, 3, d)
            self._table.setRowHeight(i, 30)
            self._playlist.addMedia(
                QMediaContent(QUrl.fromLocalFile(os.path.join(path, name)))
            )

        self._count_label.setText(f"{len(files)} 首")
        self._now_label.setText("未在播放")
        self._seek.setRange(0, 0)
        self._time_label.setText("00:00 / 00:00")
        self._duration_ms = 0
        self._stack.setCurrentIndex(0 if files else 1)
        if files:
            self._status(f"已加载 {len(files)} 首音乐：{path}", 4000)
        else:
            self._status(f"该文件夹没有音频文件：{path}", 4000)

    def _open_folder_dialog(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if path:
            self.open_folder(path)

    def _on_tree_clicked(self, index) -> None:
        path = self._fs_model.filePath(index)
        if os.path.isdir(path):
            self.load_folder(path)

    def _on_tree_double_clicked(self, index) -> None:
        path = self._fs_model.filePath(index)
        if os.path.isfile(path):
            parent = os.path.dirname(path)
            self.load_folder(parent)
            for i in range(self._table.rowCount()):
                item = self._table.item(i, 1)
                if item and item.toolTip() == path:
                    self.play_index(i)
                    return

    # ── 播放控制 ──────────────────────────────────────
    def play_index(self, row: int) -> None:
        if row < 0 or row >= self._playlist.mediaCount():
            return
        self._playlist.setCurrentIndex(row)
        self._player.play()

    def toggle_play(self) -> None:
        if self._playlist.mediaCount() == 0:
            self._status("请先打开一个包含音乐的文件夹", 3000)
            return
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            if self._playlist.currentIndex() < 0:
                self._playlist.setCurrentIndex(0)
            self._player.play()

    def _prev(self) -> None:
        if self._playlist.mediaCount() == 0:
            return
        if self._playlist.currentIndex() <= 0:
            self._playlist.setCurrentIndex(self._playlist.mediaCount() - 1)
        else:
            self._playlist.previous()
        self._player.play()

    def _next(self) -> None:
        if self._playlist.mediaCount() == 0:
            return
        if self._playlist.currentIndex() < 0:
            self._playlist.setCurrentIndex(0)
        else:
            self._playlist.next()
        self._player.play()

    def _cycle_mode(self) -> None:
        self._playlist.setPlaybackMode(PLAY_MODES[(self._mode_idx + 1) % len(PLAY_MODES)][0])

    def _on_cell_double_clicked(self, row: int, _col: int) -> None:
        self.play_index(row)

    # ── 信号处理 ──────────────────────────────────────
    def _on_current_index_changed(self, index: int) -> None:
        if index < 0 or index >= self._table.rowCount():
            self._now_label.setText("未在播放")
            return
        self._table.selectRow(index)
        self._table.scrollToItem(
            self._table.item(index, 1), QAbstractItemView.PositionAtCenter
        )
        name = self._table.item(index, 1).text()
        self._now_label.setText(f"{index + 1}. {name}")
        self._now_label.setToolTip(name)

    def _on_playback_mode_changed(self, mode) -> None:
        for idx, (m, label) in enumerate(PLAY_MODES):
            if m == mode:
                self._mode_idx = idx
                self._mode_btn.setText(label)
                self._status(f"播放模式：{label}", 2500)
                return

    def _on_state_changed(self, state) -> None:
        self._play_btn.setText("暂停" if state == QMediaPlayer.PlayingState else "播放")

    def _on_position_changed(self, pos: int) -> None:
        if not self._dragging:
            self._seek.setValue(pos)
        self._time_label.setText(f"{_fmt_ms(pos)} / {_fmt_ms(self._duration_ms)}")

    def _on_duration_changed(self, duration: int) -> None:
        self._duration_ms = duration
        self._seek.setRange(0, int(duration))
        row = self._playlist.currentIndex()
        if 0 <= row < self._table.rowCount():
            self._table.item(row, 3).setText(_fmt_ms(duration))

    def _on_player_error(self, error) -> None:
        if error != QMediaPlayer.NoError:
            self._status(f"播放出错：{self._player.errorString()}", 5000)

    def _on_seek_pressed(self) -> None:
        self._dragging = True

    def _on_seek_moved(self, pos: int) -> None:
        self._player.setPosition(pos)

    def _on_seek_released(self) -> None:
        self._dragging = False
        self._player.setPosition(self._seek.value())
