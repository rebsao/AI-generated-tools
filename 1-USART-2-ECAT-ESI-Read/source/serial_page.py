"""Serial port terminal / monitor — NVIDIA-themed, QThread-based I/O."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


BAUD_RATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
DATA_BITS = ["5", "6", "7", "8"]
PARITY = ["None", "Even", "Odd", "Mark", "Space"]
STOP_BITS = ["1", "1.5", "2"]


class SerialWorker(QThread):
    """Background thread that continuously reads from a serial port."""

    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)

    def __init__(self, ser: serial.Serial) -> None:
        super().__init__()
        self._ser = ser
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            try:
                if self._ser.in_waiting:
                    data = self._ser.read(self._ser.in_waiting)
                    self.data_received.emit(data)
                else:
                    self.msleep(20)
            except serial.SerialException as e:
                if self._running:
                    self.error_occurred.emit(str(e))
                    self._running = False
                break
            except Exception:
                self.msleep(50)

    def stop(self) -> None:
        self._running = False
        self.wait(1000)


def _serial_port_names() -> list[str]:
    """Return formatted port list: 'COM3 — USB Serial Port (CP210x)'"""
    if not HAS_SERIAL:
        return []
    result = []
    for p in sorted(serial.tools.list_ports.comports()):
        parts = [p.device]
        desc = p.description or ""
        if desc and desc != p.device and desc != "USB Serial Port":
            parts.append(desc)
        elif p.manufacturer:
            parts.append(p.manufacturer)
        result.append(" — ".join(parts))
    return result


def _extract_port(text: str) -> str:
    """Extract raw COM port name from display text (e.g. 'COM3 — CP210x' → 'COM3')."""
    return text.split(" ")[0].strip() if text else ""


def _parse_parity(text: str) -> str:
    return {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}.get(text, "N")


def _parse_stopbits(text: str) -> float:
    return {"1": 1, "1.5": 1.5, "2": 2}.get(text, 1)


class PortCombo(QComboBox):
    """下拉选择框：每次展开时自动扫描可用串口。不可编辑输入，只能下拉选择。"""

    def __init__(self, page: "SerialPage") -> None:
        super().__init__()
        self._page = page
        self.setEditable(False)

    def showPopup(self) -> None:
        self._page._refresh_ports()
        super().showPopup()


class SerialPage(QWidget):
    """IBM Carbon-themed serial port terminal widget."""

    def __init__(self) -> None:
        super().__init__()
        self._ser: Optional[serial.Serial] = None
        self._worker: Optional[SerialWorker] = None
        self._connect_time: float = 0.0
        self._tx_bytes = 0
        self._rx_bytes = 0
        self._log_file: Optional[str] = None

        self._build_ui()
        self._refresh_ports()
        self._update_connect_state(False)
        self._update_uptime_label()

    # ── UI ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Connection panel
        conn_box = QGroupBox("串口配置")
        conn_layout = QVBoxLayout(conn_box)
        conn_layout.setSpacing(8)

        config_row = QHBoxLayout()
        config_row.setSpacing(8)

        self._port_combo = PortCombo(self)
        self._port_combo.setMinimumWidth(180)

        self._baud_combo = QComboBox()
        self._baud_combo.addItems(BAUD_RATES)
        self._baud_combo.setCurrentText("115200")

        self._data_combo = QComboBox()
        self._data_combo.addItems(DATA_BITS)
        self._data_combo.setCurrentText("8")

        self._parity_combo = QComboBox()
        self._parity_combo.addItems(PARITY)
        self._parity_combo.setCurrentText("None")

        self._stop_combo = QComboBox()
        self._stop_combo.addItems(STOP_BITS)
        self._stop_combo.setCurrentText("1")

        config_row.addWidget(QLabel("端口"))
        config_row.addWidget(self._port_combo)
        config_row.addWidget(QLabel("波特率"))
        config_row.addWidget(self._baud_combo)
        config_row.addWidget(QLabel("数据位"))
        config_row.addWidget(self._data_combo)
        config_row.addWidget(QLabel("校验位"))
        config_row.addWidget(self._parity_combo)
        config_row.addWidget(QLabel("停止位"))
        config_row.addWidget(self._stop_combo)
        config_row.addStretch(1)
        conn_layout.addLayout(config_row)

        # Connect / Disconnect — 一个按钮切换
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self._toggle_btn = QPushButton("●  打开串口")
        self._toggle_btn.setObjectName("connectBtn")
        self._toggle_btn.clicked.connect(self._toggle_connection)

        self._conn_status_label = QLabel()
        self._conn_status_label.setObjectName("disconnectedLabel")
        self._conn_status_label.setText("○ 未连接")

        action_row.addWidget(self._toggle_btn)
        action_row.addWidget(self._conn_status_label)
        action_row.addStretch(1)
        conn_layout.addLayout(action_row)

        root.addWidget(conn_box)

        # TX / RX splitter
        splitter = QSplitter(Qt.Horizontal)

        # ── TX Panel ──
        tx_box = QGroupBox("TX · 发送")
        tx_root = QVBoxLayout(tx_box)
        tx_root.setSpacing(6)

        self._tx_edit = QTextEdit()
        self._tx_edit.setPlaceholderText("输入要发送的数据...")
        self._tx_edit.setMaximumHeight(200)
        tx_root.addWidget(self._tx_edit)

        tx_ctrl = QHBoxLayout()
        tx_ctrl.setSpacing(8)

        self._send_btn = QPushButton("⬆ 发送")
        self._send_btn.clicked.connect(self._send_text)

        self._send_file_btn = QPushButton("📁 发送文件...")
        self._send_file_btn.clicked.connect(self._send_file)

        self._hex_tx_cb = QCheckBox("十六进制发送")
        self._hex_tx_cb.setToolTip("以十六进制字节发送 (例如: A0 01 FF)")

        self._append_nl_cb = QCheckBox("追加 \\r\\n")
        self._append_nl_cb.setChecked(True)

        tx_ctrl.addWidget(self._send_btn)
        tx_ctrl.addWidget(self._send_file_btn)
        tx_ctrl.addWidget(self._hex_tx_cb)
        tx_ctrl.addWidget(self._append_nl_cb)
        tx_ctrl.addStretch(1)
        tx_root.addLayout(tx_ctrl)

        splitter.addWidget(tx_box)

        # ── RX Panel ──
        rx_box = QGroupBox("RX · 接收")
        rx_root = QVBoxLayout(rx_box)
        rx_root.setSpacing(6)

        self._rx_edit = QTextEdit()
        self._rx_edit.setReadOnly(True)
        self._rx_edit.setPlaceholderText("接收数据将显示在此...")
        self._rx_edit.setStyleSheet(
            "QTextEdit { background-color: #f7f7f7; color: #1a1a1a; }"
        )
        rx_root.addWidget(self._rx_edit)

        rx_ctrl = QHBoxLayout()
        rx_ctrl.setSpacing(8)

        self._clear_rx_btn = QPushButton("清空")
        self._clear_rx_btn.setObjectName("secondaryBtn")
        self._clear_rx_btn.clicked.connect(self._rx_edit.clear)

        self._save_log_btn = QPushButton("💾 保存日志...")
        self._save_log_btn.setObjectName("secondaryBtn")
        self._save_log_btn.clicked.connect(self._save_log)

        self._hex_rx_cb = QCheckBox("十六进制显示")
        self._timestamp_cb = QCheckBox("时间戳")
        self._autoscroll_cb = QCheckBox("自动滚动")
        self._autoscroll_cb.setChecked(True)

        rx_ctrl.addWidget(self._clear_rx_btn)
        rx_ctrl.addWidget(self._save_log_btn)
        rx_ctrl.addWidget(self._hex_rx_cb)
        rx_ctrl.addWidget(self._timestamp_cb)
        rx_ctrl.addWidget(self._autoscroll_cb)
        rx_ctrl.addStretch(1)
        rx_root.addLayout(rx_ctrl)

        splitter.addWidget(rx_box)
        splitter.setSizes([300, 400])
        root.addWidget(splitter, stretch=1)

    # ── Port Management ──────────────────────────────────

    def _refresh_ports(self) -> None:
        current = self._port_combo.currentText()
        self._port_combo.clear()
        ports = _serial_port_names()
        self._port_combo.addItems(ports)

        # Restore previous selection or pick first
        matched = False
        if current:
            for port in ports:
                if port.startswith(current) or current.startswith(port):
                    self._port_combo.setCurrentText(port)
                    matched = True
                    break
        if not matched and ports:
            self._port_combo.setCurrentIndex(0)

        if ports:
            self._append_rx_log(f"[端口扫描] 可用串口: {', '.join(ports)}")
        elif HAS_SERIAL:
            self._append_rx_log("[端口扫描] 未检测到串口设备。")
        else:
            self._append_rx_log("[端口扫描] pyserial 未安装，请执行: pip install pyserial")

    def _current_config(self) -> dict:
        return {
            "port": _extract_port(self._port_combo.currentText()),
            "baudrate": int(self._baud_combo.currentText()),
            "bytesize": int(self._data_combo.currentText()),
            "parity": _parse_parity(self._parity_combo.currentText()),
            "stopbits": _parse_stopbits(self._stop_combo.currentText()),
            "timeout": 1,
        }

    def _toggle_connection(self) -> None:
        """单按钮切换：已连接→断开，未连接→打开。"""
        if self._ser and self._ser.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self) -> None:
        if not HAS_SERIAL:
            QMessageBox.critical(self, "错误", "pyserial 未安装。\npip install pyserial")
            return

        config = self._current_config()
        if not config["port"]:
            QMessageBox.warning(self, "警告", "请先选择一个串口。")
            return

        try:
            self._ser = serial.Serial(**config)
        except Exception as e:
            QMessageBox.critical(self, "连接错误", str(e))
            return

        self._worker = SerialWorker(self._ser)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.error_occurred.connect(self._on_worker_error)
        self._worker.start()

        self._connect_time = time.time()
        self._tx_bytes = 0
        self._rx_bytes = 0
        self._update_connect_state(True)

    def _disconnect(self) -> None:
        if self._worker:
            self._worker.stop()
            self._worker = None
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._update_connect_state(False)

    def _update_connect_state(self, connected: bool) -> None:
        self._port_combo.setEnabled(not connected)
        self._baud_combo.setEnabled(not connected)
        self._data_combo.setEnabled(not connected)
        self._parity_combo.setEnabled(not connected)
        self._stop_combo.setEnabled(not connected)
        self._send_btn.setEnabled(connected)
        self._send_file_btn.setEnabled(connected)

        if connected:
            self._toggle_btn.setText("○  关闭串口")
            self._toggle_btn.setObjectName("disconnectBtn")
            self._conn_status_label.setObjectName("connectedLabel")
            cfg = self._current_config()
            self._conn_status_label.setText(
                f"● 已连接  |  {cfg['port']}  {cfg['baudrate']}-{cfg['bytesize']}"
                f"{cfg['parity']}{cfg['stopbits']}"
            )
        else:
            self._toggle_btn.setText("●  打开串口")
            self._toggle_btn.setObjectName("connectBtn")
            self._conn_status_label.setObjectName("disconnectedLabel")
            self._conn_status_label.setText("○ 未连接")

        self._toggle_btn.style().unpolish(self._toggle_btn)
        self._toggle_btn.style().polish(self._toggle_btn)
        self._conn_status_label.style().unpolish(self._conn_status_label)
        self._conn_status_label.style().polish(self._conn_status_label)

    # ── Send ─────────────────────────────────────────────

    def _send_text(self) -> None:
        if not self._ser or not self._ser.is_open:
            return
        raw = self._tx_edit.toPlainText()
        if not raw:
            return

        try:
            if self._hex_tx_cb.isChecked():
                raw = raw.replace(",", " ").replace("0x", "").replace("0X", "")
                data = bytes.fromhex(raw)
            else:
                data = raw.encode("utf-8")
                if self._append_nl_cb.isChecked():
                    data += b"\r\n"
        except ValueError as e:
            QMessageBox.warning(self, "格式错误", f"无效的十六进制: {e}")
            return

        try:
            written = self._ser.write(data)
            self._tx_bytes += written
        except serial.SerialException as e:
            QMessageBox.critical(self, "发送错误", str(e))
            self._disconnect()

    def _send_file(self) -> None:
        if not self._ser or not self._ser.is_open:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要发送的文件", "", "所有文件 (*.*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            written = self._ser.write(data)
            self._tx_bytes += written
        except Exception as e:
            QMessageBox.critical(self, "文件发送错误", str(e))

    # ── Receive ──────────────────────────────────────────

    def _append_rx_log(self, text: str) -> None:
        """Append a log message to the RX area (non-data, informational)."""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cursor = self._rx_edit.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(f"[{ts}] {text}\n")
        if self._autoscroll_cb.isChecked():
            self._rx_edit.ensureCursorVisible()

    def _on_data_received(self, data: bytes) -> None:
        self._rx_bytes += len(data)

        if self._hex_rx_cb.isChecked():
            text = " ".join(f"{b:02X}" for b in data)
        else:
            text = data.decode("utf-8", errors="replace")

        if self._timestamp_cb.isChecked():
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            text = f"[{ts}] {text}"

        cursor = self._rx_edit.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        if not text.endswith("\n"):
            cursor.insertText("\n")

        self._rx_edit.setTextCursor(cursor)

        if self._autoscroll_cb.isChecked():
            self._rx_edit.ensureCursorVisible()

    def _on_worker_error(self, message: str) -> None:
        self._disconnect()
        QMessageBox.critical(self, "串口错误", message)

    # ── Log ──────────────────────────────────────────────

    def _save_log(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存接收日志", "serial_log.txt", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self._rx_edit.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "保存错误", str(e))

    # ── Status bar ───────────────────────────────────────

    def _update_uptime_label(self) -> None:
        # Called periodically; for now we just track bytes
        pass

    def status_info(self) -> str:
        if self._ser and self._ser.is_open:
            elapsed = int(time.time() - self._connect_time)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            cfg = self._current_config()
            return (
                f"端口: {cfg['port']}  |  {cfg['baudrate']}-{cfg['bytesize']}"
                f"{cfg['parity']}{cfg['stopbits']}  |  "
                f"TX: {self._tx_bytes:,} 字节  |  RX: {self._rx_bytes:,} 字节  |  "
                f"运行时间: {h:02d}:{m:02d}:{s:02d}"
            )
        return "未连接"
