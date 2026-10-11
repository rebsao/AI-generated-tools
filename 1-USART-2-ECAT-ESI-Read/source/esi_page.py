from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence
import xml.etree.ElementTree as ET

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QAction,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


NA_TEXT = "N/A"


# ───────────────────────── 数据模型 ─────────────────────────

@dataclass
class EsiParseWarning:
    code: str
    message: str
    path: str = ""


@dataclass
class EsiBasicInfo:
    vendor_name: str = NA_TEXT
    vendor_id: str = NA_TEXT
    device_name: str = NA_TEXT
    type_name: str = NA_TEXT
    group_type: str = NA_TEXT
    group_name: str = NA_TEXT
    product_code: str = NA_TEXT
    revision_no: str = NA_TEXT
    serial_no: str = NA_TEXT
    profile_no: str = NA_TEXT
    physics: str = NA_TEXT


@dataclass
class EsiSmEntry:
    index: int
    start_address: str = NA_TEXT
    control_byte: str = NA_TEXT
    enable: str = NA_TEXT
    default_size: str = NA_TEXT
    name: str = NA_TEXT


@dataclass
class EsiFmmuEntry:
    index: int
    type: str = NA_TEXT
    logical_start: str = NA_TEXT
    length: str = NA_TEXT
    physical_start: str = NA_TEXT
    active: str = NA_TEXT


@dataclass
class EsiPdoEntry:
    direction: str
    pdo_index: str = NA_TEXT
    pdo_name: str = NA_TEXT
    entry_index: str = NA_TEXT
    subindex: str = NA_TEXT
    name: str = NA_TEXT
    data_type: str = NA_TEXT
    bit_len: str = NA_TEXT
    sm: str = NA_TEXT
    fixed: str = NA_TEXT
    syncm: str = NA_TEXT


@dataclass
class EsiSdoEntry:
    obj_index: str = NA_TEXT
    obj_name: str = NA_TEXT
    obj_type: str = NA_TEXT
    subindex: str = NA_TEXT
    sub_name: str = NA_TEXT
    data_type: str = NA_TEXT
    access: str = NA_TEXT
    bit_size: str = NA_TEXT
    default: str = NA_TEXT


@dataclass
class EsiMailboxDcInfo:
    coe: str = NA_TEXT
    foe: str = NA_TEXT
    eoe: str = NA_TEXT
    soe: str = NA_TEXT
    voe: str = NA_TEXT
    dc_supported: str = NA_TEXT
    dc_assign_activate: str = NA_TEXT
    dc_sync0_cycle: str = NA_TEXT
    dc_sync1_cycle: str = NA_TEXT


@dataclass
class EsiDevice:
    device_id: str
    basic_info: EsiBasicInfo = field(default_factory=EsiBasicInfo)
    sm_entries: List[EsiSmEntry] = field(default_factory=list)
    fmmu_entries: List[EsiFmmuEntry] = field(default_factory=list)
    pdo_entries: List[EsiPdoEntry] = field(default_factory=list)
    sdo_entries: List[EsiSdoEntry] = field(default_factory=list)
    mailbox_dc: EsiMailboxDcInfo = field(default_factory=EsiMailboxDcInfo)


@dataclass
class EsiParseResult:
    devices: List[EsiDevice] = field(default_factory=list)
    warnings: List[EsiParseWarning] = field(default_factory=list)
    source_file: str = ""


# ───────────────────────── XML 解析 ─────────────────────────

def parse_esi_file(file_path: str) -> EsiParseResult:
    source = str(Path(file_path).resolve())
    try:
        tree = ET.parse(source)
    except ET.ParseError as err:
        raise ValueError(f"XML 格式错误：{err}") from err
    except OSError as err:
        raise ValueError(f"无法读取 XML 文件：{err}") from err

    root = tree.getroot()
    result = EsiParseResult(source_file=source)

    vendor_name, vendor_id = _parse_vendor_info(root)
    group_map = _parse_group_map(root)
    device_nodes = _find_device_nodes(root)

    if not device_nodes:
        result.warnings.append(
            EsiParseWarning(code="NO_DEVICE", message="未发现 Device 节点。", path="Descriptions/Devices")
        )
        return result

    for idx, device_node in enumerate(device_nodes, start=1):
        device = _parse_device(device_node, idx, vendor_name, vendor_id, group_map, result.warnings)
        result.devices.append(device)

    return result


def to_export_dict(result: EsiParseResult) -> dict:
    return asdict(result)


def _parse_device(
    device_node: ET.Element,
    index: int,
    vendor_name: str,
    vendor_id: str,
    group_map: Dict[str, str],
    warnings: List[EsiParseWarning],
) -> EsiDevice:
    type_node = _find_child(device_node, "Type")

    type_name = _clean_text(_node_text(type_node)) or NA_TEXT
    product_code = _attr_or_path(type_node, "ProductCode", [device_node, type_node], ["ProductCode"])
    revision_no = _attr_or_path(type_node, "RevisionNo", [device_node, type_node], ["RevisionNo"])
    serial_no = _attr_or_path(type_node, "SerialNo", [device_node, type_node], ["SerialNo"])
    physics = _attr_or_path(type_node, "Physics", [device_node, type_node], ["Physics"])
    group_type = _first_text(device_node, ["GroupType"])
    group_name = group_map.get(group_type, NA_TEXT) if group_type != NA_TEXT else NA_TEXT

    device_name = _first_text(device_node, ["Name"])
    if device_name == NA_TEXT and type_name != NA_TEXT:
        device_name = type_name

    profile_no = _first_text(device_node, ["Profile/No", "ProfileNo"])

    basic_info = EsiBasicInfo(
        vendor_name=vendor_name,
        vendor_id=vendor_id,
        device_name=device_name,
        type_name=type_name,
        group_type=group_type,
        group_name=group_name,
        product_code=product_code,
        revision_no=revision_no,
        serial_no=serial_no,
        profile_no=profile_no,
        physics=physics,
    )

    sm_entries = _parse_sm_entries(device_node)
    if not sm_entries:
        warnings.append(
            EsiParseWarning(code="NO_SM", message=f"设备#{index} 未发现 SM 信息。", path=f"Device[{index}]/Sm")
        )

    fmmu_entries = _parse_fmmu_entries(device_node)
    if not fmmu_entries:
        warnings.append(
            EsiParseWarning(
                code="NO_FMMU",
                message=f"设备#{index} 未发现 FMMU 信息。",
                path=f"Device[{index}]/Fmmu",
            )
        )

    pdo_entries = _parse_pdo_entries(device_node)
    if not pdo_entries:
        warnings.append(
            EsiParseWarning(
                code="NO_PDO",
                message=f"设备#{index} 未发现 PDO 条目。",
                path=f"Device[{index}]/RxPdo|TxPdo",
            )
        )

    sdo_entries = _parse_sdo_entries(device_node)
    if not sdo_entries:
        warnings.append(
            EsiParseWarning(
                code="NO_SDO",
                message=f"设备#{index} 未发现 SDO 字典条目。",
                path=f"Device[{index}]/Profile/Dictionary/Objects",
            )
        )

    mailbox_dc = _parse_mailbox_dc(device_node)

    device_id = f"device_{index}"
    return EsiDevice(
        device_id=device_id,
        basic_info=basic_info,
        sm_entries=sm_entries,
        fmmu_entries=fmmu_entries,
        pdo_entries=pdo_entries,
        sdo_entries=sdo_entries,
        mailbox_dc=mailbox_dc,
    )


def _parse_vendor_info(root: ET.Element) -> tuple[str, str]:
    vendors_parent = _find_path(root, "Descriptions/Vendors")
    if vendors_parent is None:
        vendors_parent = _find_path(root, "Vendors")
    if vendors_parent is None:
        return NA_TEXT, NA_TEXT

    vendor_node = _find_child(vendors_parent, "Vendor")
    if vendor_node is None:
        return NA_TEXT, NA_TEXT

    vendor_name = _first_text(vendor_node, ["Name"])
    vendor_id = _first_text(vendor_node, ["Id", "VendorId"])
    return vendor_name, vendor_id


def _parse_group_map(root: ET.Element) -> Dict[str, str]:
    groups_parent = _find_path(root, "Descriptions/Groups")
    if groups_parent is None:
        groups_parent = _find_path(root, "Groups")
    if groups_parent is None:
        return {}

    mapping: Dict[str, str] = {}
    for group in _iter_children(groups_parent, "Group"):
        group_type = _first_text(group, ["Type"])
        group_name = _first_text(group, ["Name"])
        if group_type != NA_TEXT:
            mapping[group_type] = group_name
    return mapping


def _find_device_nodes(root: ET.Element) -> List[ET.Element]:
    devices_parent = _find_path(root, "Descriptions/Devices")
    if devices_parent is not None:
        nodes = list(_iter_children(devices_parent, "Device"))
        if nodes:
            return nodes

    devices_parent = _find_path(root, "Devices")
    if devices_parent is not None:
        nodes = list(_iter_children(devices_parent, "Device"))
        if nodes:
            return nodes

    return [node for node in root.iter() if _local_name(node.tag) == "Device"]


def _parse_sm_entries(device_node: ET.Element) -> List[EsiSmEntry]:
    sm_nodes = [node for node in device_node.iter() if _local_name(node.tag) == "Sm"]
    entries: List[EsiSmEntry] = []

    for idx, node in enumerate(sm_nodes, start=1):
        entries.append(
            EsiSmEntry(
                index=idx,
                start_address=_attr_value(node, "StartAddress"),
                control_byte=_attr_value(node, "ControlByte"),
                enable=_attr_value(node, "Enable"),
                default_size=_attr_value(node, "DefaultSize"),
                name=_clean_text(node.text) or _attr_or_text(node, "Name"),
            )
        )

    return entries


def _parse_fmmu_entries(device_node: ET.Element) -> List[EsiFmmuEntry]:
    fmmu_nodes = [node for node in device_node.iter() if _local_name(node.tag) == "Fmmu"]
    entries: List[EsiFmmuEntry] = []

    for idx, node in enumerate(fmmu_nodes, start=1):
        entries.append(
            EsiFmmuEntry(
                index=idx,
                type=_clean_text(node.text) or _attr_or_text(node, "Type"),
                logical_start=_attr_value(node, "LogicalStartAddress", "StartAddress"),
                length=_attr_value(node, "Length", "Size"),
                physical_start=_attr_value(node, "PhysicalStartAddress", "StartAddress"),
                active=_attr_value(node, "Enable", "Active"),
            )
        )

    return entries


def _parse_pdo_entries(device_node: ET.Element) -> List[EsiPdoEntry]:
    pdo_entries: List[EsiPdoEntry] = []
    pdo_nodes: List[ET.Element] = [
        node for node in device_node.iter() if _local_name(node.tag) in {"RxPdo", "TxPdo"}
    ]

    for pdo_node in pdo_nodes:
        direction = "Rx" if _local_name(pdo_node.tag) == "RxPdo" else "Tx"
        pdo_index = _first_text(pdo_node, ["Index"])
        pdo_name = _first_text(pdo_node, ["Name"])
        sm = _first_non_empty(
            [
                _attr_or_text(pdo_node, "Sm"),
                _first_text(pdo_node, ["Sm"], empty_as_na=False),
            ]
        )
        fixed = _first_non_empty(
            [
                _attr_or_text(pdo_node, "Fixed"),
                _first_text(pdo_node, ["Fixed"], empty_as_na=False),
            ]
        )
        syncm = _first_non_empty(
            [
                _attr_or_text(pdo_node, "SyncM"),
                _first_text(pdo_node, ["SyncM"], empty_as_na=False),
            ]
        )

        entry_nodes = [node for node in pdo_node.iter() if _local_name(node.tag) == "Entry"]
        if not entry_nodes:
            pdo_entries.append(
                EsiPdoEntry(
                    direction=direction,
                    pdo_index=pdo_index,
                    pdo_name=pdo_name,
                    sm=sm,
                    fixed=fixed,
                    syncm=syncm,
                )
            )
            continue

        for entry_node in entry_nodes:
            pdo_entries.append(
                EsiPdoEntry(
                    direction=direction,
                    pdo_index=pdo_index,
                    pdo_name=pdo_name,
                    entry_index=_first_text(entry_node, ["Index"]),
                    subindex=_first_text(entry_node, ["SubIndex", "SubIdx"]),
                    name=_first_text(entry_node, ["Name"]),
                    data_type=_first_text(entry_node, ["DataType", "Type"]),
                    bit_len=_first_text(entry_node, ["BitLen", "BitSize"]),
                    sm=sm,
                    fixed=fixed,
                    syncm=syncm,
                )
            )

    return pdo_entries


def _parse_sdo_entries(device_node: ET.Element) -> List[EsiSdoEntry]:
    object_parent = _find_path(device_node, "Profile/Dictionary/Objects")
    if object_parent is not None:
        object_nodes = list(_iter_children(object_parent, "Object"))
    else:
        object_nodes = [node for node in device_node.iter() if _local_name(node.tag) == "Object"]

    sdo_entries: List[EsiSdoEntry] = []
    for object_node in object_nodes:
        obj_index = _first_text(object_node, ["Index"])
        obj_name = _first_text(object_node, ["Name"])
        obj_type = _first_text(object_node, ["Type", "ObjectType"])
        obj_data_type = _first_text(object_node, ["DataType"])
        obj_access = _first_text(object_node, ["Access", "Flags/Access"])
        obj_bit_size = _first_text(object_node, ["BitSize", "BitLen"])
        obj_default = _first_text(object_node, ["DefaultValue", "DefaultData"])

        sub_nodes = [
            child
            for child in list(object_node)
            if _local_name(child.tag) in {"SubItem", "SubIdx", "SubIndex", "Entry"}
        ]

        if not sub_nodes:
            sdo_entries.append(
                EsiSdoEntry(
                    obj_index=obj_index,
                    obj_name=obj_name,
                    obj_type=obj_type,
                    subindex="0",
                    sub_name=obj_name,
                    data_type=obj_data_type,
                    access=obj_access,
                    bit_size=obj_bit_size,
                    default=obj_default,
                )
            )
            continue

        for sub_node in sub_nodes:
            subindex = _first_non_empty(
                [
                    _clean_text(sub_node.attrib.get("SubIdx", "")),
                    _clean_text(sub_node.attrib.get("SubIndex", "")),
                    _first_text(sub_node, ["SubIdx", "SubIndex", "Index"], empty_as_na=False),
                ]
            )
            sdo_entries.append(
                EsiSdoEntry(
                    obj_index=obj_index,
                    obj_name=obj_name,
                    obj_type=obj_type,
                    subindex=subindex,
                    sub_name=_first_text(sub_node, ["Name"]),
                    data_type=_first_non_empty(
                        [
                            _first_text(sub_node, ["DataType", "Type"], empty_as_na=False),
                            obj_data_type,
                        ]
                    ),
                    access=_first_non_empty(
                        [
                            _first_text(sub_node, ["Access", "Flags/Access"], empty_as_na=False),
                            obj_access,
                        ]
                    ),
                    bit_size=_first_non_empty(
                        [
                            _first_text(sub_node, ["BitSize", "BitLen"], empty_as_na=False),
                            obj_bit_size,
                        ]
                    ),
                    default=_first_non_empty(
                        [
                            _first_text(sub_node, ["DefaultValue", "DefaultData"], empty_as_na=False),
                            obj_default,
                        ]
                    ),
                )
            )

    return sdo_entries


def _parse_mailbox_dc(device_node: ET.Element) -> EsiMailboxDcInfo:
    mailbox_node = _find_child(device_node, "Mailbox")
    if mailbox_node is None:
        mailbox_node = next((node for node in device_node.iter() if _local_name(node.tag) == "Mailbox"), None)

    dc_node = _find_child(device_node, "Dc")
    if dc_node is None:
        dc_node = _find_child(device_node, "DC")
    if dc_node is None:
        dc_node = next((node for node in device_node.iter() if _local_name(node.tag).lower() == "dc"), None)

    coe = _mailbox_feature(mailbox_node, "CoE")
    foe = _mailbox_feature(mailbox_node, "FoE")
    eoe = _mailbox_feature(mailbox_node, "EoE")
    soe = _mailbox_feature(mailbox_node, "SoE")
    voe = _mailbox_feature(mailbox_node, "VoE")

    dc_supported = "是" if dc_node is not None else "否"
    dc_assign_activate = NA_TEXT
    dc_sync0_cycle = NA_TEXT
    dc_sync1_cycle = NA_TEXT
    if dc_node is not None:
        dc_assign_activate = _first_text(dc_node, ["OpMode/AssignActivate", "AssignActivate"])
        dc_sync0_cycle = _first_text(dc_node, ["OpMode/CycleTimeSync0", "CycleTimeSync0"])
        dc_sync1_cycle = _first_text(dc_node, ["OpMode/CycleTimeSync1", "CycleTimeSync1"])

    return EsiMailboxDcInfo(
        coe=coe,
        foe=foe,
        eoe=eoe,
        soe=soe,
        voe=voe,
        dc_supported=dc_supported,
        dc_assign_activate=dc_assign_activate,
        dc_sync0_cycle=dc_sync0_cycle,
        dc_sync1_cycle=dc_sync1_cycle,
    )


def _mailbox_feature(mailbox_node: Optional[ET.Element], feature_name: str) -> str:
    if mailbox_node is None:
        return NA_TEXT

    feature_node = _find_child(mailbox_node, feature_name)
    if feature_node is None:
        return "否"

    details = []
    for key, value in feature_node.attrib.items():
        clean_value = _clean_text(value)
        if clean_value:
            details.append(f"{key}={clean_value}")

    state = _feature_state(feature_node)
    if details:
        return f"{state} [{', '.join(details)}]"
    return state


def _feature_state(node: ET.Element) -> str:
    attrs = {k.lower(): _clean_text(v).lower() for k, v in node.attrib.items()}
    for key in ("enable", "enabled", "support", "supported", "active"):
        if key in attrs:
            return _bool_text(attrs[key])

    text = _clean_text(node.text)
    if text:
        return _bool_text(text.lower())

    return "是"


def _bool_text(value: str) -> str:
    if value in {"1", "true", "yes", "on", "enabled", "supported"}:
        return "是"
    if value in {"0", "false", "no", "off", "disabled", "unsupported"}:
        return "否"
    return value


def _first_text(node: Optional[ET.Element], paths: Sequence[str], empty_as_na: bool = True) -> str:
    if node is None:
        return NA_TEXT if empty_as_na else ""

    for path in paths:
        found = _find_path(node, path)
        if found is None:
            continue
        value = _clean_text(found.text)
        if value:
            return value

    return NA_TEXT if empty_as_na else ""


def _attr_or_path(
    preferred_node: Optional[ET.Element],
    attr_name: str,
    fallback_nodes: Sequence[Optional[ET.Element]],
    fallback_paths: Sequence[str],
) -> str:
    if preferred_node is not None:
        attr_value = _clean_text(preferred_node.attrib.get(attr_name, ""))
        if attr_value:
            return attr_value

    for node in fallback_nodes:
        if node is None:
            continue
        for path in fallback_paths:
            value = _first_text(node, [path], empty_as_na=False)
            if value:
                return value

    return NA_TEXT


def _attr_or_text(node: Optional[ET.Element], *attr_names: str) -> str:
    if node is None:
        return NA_TEXT

    for name in attr_names:
        value = _clean_text(node.attrib.get(name, ""))
        if value:
            return value

    text = _clean_text(node.text)
    if text:
        return text
    return NA_TEXT


def _attr_value(node: Optional[ET.Element], *attr_names: str) -> str:
    if node is None:
        return NA_TEXT
    for name in attr_names:
        value = _clean_text(node.attrib.get(name, ""))
        if value:
            return value
    return NA_TEXT


def _first_non_empty(values: Sequence[str]) -> str:
    for value in values:
        clean = _clean_text(value)
        if clean and clean != NA_TEXT:
            return clean
    return NA_TEXT


def _find_path(node: ET.Element, path: str) -> Optional[ET.Element]:
    parts = [part for part in path.split("/") if part]
    if not parts:
        return node

    current_nodes = [node]
    for part in parts:
        next_nodes: List[ET.Element] = []
        for current in current_nodes:
            next_nodes.extend(_iter_children(current, part))
        if not next_nodes:
            return None
        current_nodes = next_nodes
    return current_nodes[0]


def _iter_children(node: ET.Element, child_name: str):
    for child in list(node):
        if _local_name(child.tag) == child_name:
            yield child


def _find_child(node: ET.Element, child_name: str) -> Optional[ET.Element]:
    return next(_iter_children(node, child_name), None)


def _node_text(node: Optional[ET.Element]) -> str:
    if node is None:
        return ""
    return node.text or ""


def _clean_text(text: Optional[str]) -> str:
    if text is None:
        return ""
    return text.strip()


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


# ───────────────────────── 详情窗口 ─────────────────────────

class _DetailWindow(QWidget):
    """独立浮动详情窗口基类。"""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        device: EsiDevice,
        source_file: str,
    ) -> None:
        super().__init__(parent, Qt.Window)
        device_name = EsiPage._na_text(device.basic_info.device_name)
        self.setWindowTitle(f"{title} — {device_name} ({os.path.basename(source_file)})")
        self.resize(960, 620)
        self._device = device
        self.setAttribute(Qt.WA_DeleteOnClose)

    # ── 表格工具 ──────────────────────────────────────

    @staticmethod
    def _na_text(value) -> str:
        if value is None:
            return NA_TEXT
        text = str(value).strip()
        return text if text else NA_TEXT

    def _setup_table(self, table: QTableWidget, headers: List[str]) -> None:
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.setAlternatingRowColors(True)
        table.setRowCount(0)

    def _fill_table(self, table: QTableWidget, rows: List[List[str]]) -> None:
        table.setRowCount(len(rows))
        for row_idx, row_values in enumerate(rows):
            for col_idx, value in enumerate(row_values):
                table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        # 最后一列自动拉伸填充剩余空间，同时允许手动调整
        last_col = table.columnCount() - 1
        if last_col >= 0:
            table.horizontalHeader().setSectionResizeMode(last_col, QHeaderView.Stretch)

    def _setup_table_ctx_menu(self, table: QTableWidget) -> None:
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos, t=table: self._on_table_context_menu(t, pos)
        )

    def _on_table_context_menu(self, table: QTableWidget, pos: QPoint) -> None:
        menu = QMenu(self)
        act_copy_row = QAction("复制当前行", menu)
        act_copy_row.triggered.connect(lambda: self._copy_table_row(table))
        menu.addAction(act_copy_row)
        act_copy_cell = QAction("复制当前单元格", menu)
        act_copy_cell.triggered.connect(lambda: self._copy_table_cell(table, pos))
        menu.addAction(act_copy_cell)
        menu.addSeparator()
        act_copy_all = QAction("复制全部可见行", menu)
        act_copy_all.triggered.connect(lambda: self._copy_table_all(table))
        menu.addAction(act_copy_all)
        menu.exec_(table.viewport().mapToGlobal(pos))

    def _copy_table_row(self, table: QTableWidget) -> None:
        row = table.currentRow()
        if row < 0:
            return
        values = [
            table.item(row, col).text() if table.item(row, col) else ""
            for col in range(table.columnCount())
        ]
        QApplication.clipboard().setText("\t".join(values))

    def _copy_table_cell(self, table: QTableWidget, pos: QPoint) -> None:
        item = table.itemAt(pos)
        if item:
            QApplication.clipboard().setText(item.text())

    def _copy_table_all(self, table: QTableWidget) -> None:
        if table.rowCount() == 0:
            return
        lines = []
        for row in range(table.rowCount()):
            values = [
                table.item(row, col).text() if table.item(row, col) else ""
                for col in range(table.columnCount())
            ]
            lines.append("\t".join(values))
        QApplication.clipboard().setText("\n".join(lines))


class _BasicInfoWindow(_DetailWindow):
    """基础信息窗口。"""

    def __init__(self, parent, device, source_file):
        super().__init__(parent, "基础信息", device, source_file)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        table = QTableWidget()
        self._setup_table(table, ["字段", "值"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._setup_table_ctx_menu(table)

        basic = self._device.basic_info
        rows = [
            ["设备 ID", self._na_text(self._device.device_id)],
            ["设备名称", self._na_text(basic.device_name)],
            ["厂商名称", self._na_text(basic.vendor_name)],
            ["厂商 ID", self._na_text(basic.vendor_id)],
            ["类型名称", self._na_text(basic.type_name)],
            ["GroupType", self._na_text(basic.group_type)],
            ["Group 名称", self._na_text(basic.group_name)],
            ["ProductCode", self._na_text(basic.product_code)],
            ["RevisionNo", self._na_text(basic.revision_no)],
            ["SerialNo", self._na_text(basic.serial_no)],
            ["ProfileNo", self._na_text(basic.profile_no)],
            ["Physics", self._na_text(basic.physics)],
            ["PDO 条目数", str(len(self._device.pdo_entries))],
            ["SDO 条目数", str(len(self._device.sdo_entries))],
            ["SM 条目数", str(len(self._device.sm_entries))],
            ["FMMU 条目数", str(len(self._device.fmmu_entries))],
        ]
        self._fill_table(table, rows)
        layout.addWidget(table)


class _SmFmmuWindow(_DetailWindow):
    """SM / FMMU 窗口。"""

    def __init__(self, parent, device, source_file):
        super().__init__(parent, "SM / FMMU", device, source_file)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(QLabel("SM 列表"))
        sm_table = QTableWidget()
        self._setup_table(
            sm_table,
            ["序号", "StartAddress", "ControlByte", "Enable", "DefaultSize", "名称"],
        )
        self._setup_table_ctx_menu(sm_table)
        sm_rows = [
            [
                str(item.index),
                self._na_text(item.start_address),
                self._na_text(item.control_byte),
                self._na_text(item.enable),
                self._na_text(item.default_size),
                self._na_text(item.name),
            ]
            for item in self._device.sm_entries
        ]
        self._fill_table(sm_table, sm_rows)
        layout.addWidget(sm_table)

        layout.addWidget(QLabel("FMMU 列表"))
        fmmu_table = QTableWidget()
        self._setup_table(
            fmmu_table,
            ["序号", "类型", "逻辑起始", "长度", "物理起始", "激活"],
        )
        self._setup_table_ctx_menu(fmmu_table)
        fmmu_rows = [
            [
                str(item.index),
                self._na_text(item.type),
                self._na_text(item.logical_start),
                self._na_text(item.length),
                self._na_text(item.physical_start),
                self._na_text(item.active),
            ]
            for item in self._device.fmmu_entries
        ]
        self._fill_table(fmmu_table, fmmu_rows)
        layout.addWidget(fmmu_table)


class _PdoWindow(_DetailWindow):
    """PDO 映射窗口（含筛选功能）。"""

    def __init__(self, parent, device, source_file):
        super().__init__(parent, "PDO 映射", device, source_file)
        self._all_rows = device.pdo_entries
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 筛选栏
        filter_row = QHBoxLayout()
        self._dir_combo = QComboBox()
        self._dir_combo.addItems(["全部", "Rx", "Tx"])
        self._index_edit = QLineEdit()
        self._index_edit.setPlaceholderText("Index 关键字")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("名称关键字")
        apply_btn = QPushButton("筛选")
        reset_btn = QPushButton("重置")

        filter_row.addWidget(QLabel("方向"))
        filter_row.addWidget(self._dir_combo)
        filter_row.addWidget(QLabel("Index"))
        filter_row.addWidget(self._index_edit)
        filter_row.addWidget(QLabel("名称"))
        filter_row.addWidget(self._name_edit)
        filter_row.addWidget(apply_btn)
        filter_row.addWidget(reset_btn)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self._table = QTableWidget()
        self._setup_table(
            self._table,
            [
                "方向", "PDO Index", "PDO 名称", "Entry Index", "SubIndex",
                "名称", "数据类型", "位长度", "SM", "Fixed", "SyncM",
            ],
        )
        self._setup_table_ctx_menu(self._table)
        layout.addWidget(self._table)

        self._summary_label = QLabel()
        self._summary_label.setObjectName("statusLabel")
        layout.addWidget(self._summary_label)

        # 事件
        apply_btn.clicked.connect(self._apply_filter)
        reset_btn.clicked.connect(self._reset_filter)
        self._dir_combo.currentIndexChanged.connect(self._apply_filter)
        self._index_edit.returnPressed.connect(self._apply_filter)
        self._name_edit.returnPressed.connect(self._apply_filter)

        self._apply_filter()

    def _apply_filter(self) -> None:
        direction = self._dir_combo.currentText().strip()
        index_key = self._index_edit.text().strip().lower()
        name_key = self._name_edit.text().strip().lower()

        filtered = []
        for item in self._all_rows:
            if direction != "全部" and item.direction != direction:
                continue
            if index_key:
                pdo_index = self._na_text(item.pdo_index).lower()
                entry_index = self._na_text(item.entry_index).lower()
                if index_key not in pdo_index and index_key not in entry_index:
                    continue
            if name_key:
                pdo_name = self._na_text(item.pdo_name).lower()
                entry_name = self._na_text(item.name).lower()
                if name_key not in pdo_name and name_key not in entry_name:
                    continue
            filtered.append(item)

        table_rows = [
            [
                item.direction,
                self._na_text(item.pdo_index),
                self._na_text(item.pdo_name),
                self._na_text(item.entry_index),
                self._na_text(item.subindex),
                self._na_text(item.name),
                self._na_text(item.data_type),
                self._na_text(item.bit_len),
                self._na_text(item.sm),
                self._na_text(item.fixed),
                self._na_text(item.syncm),
            ]
            for item in filtered
        ]
        self._fill_table(self._table, table_rows)
        self._summary_label.setText(f"PDO 条目：{len(filtered)} / {len(self._all_rows)}")

    def _reset_filter(self) -> None:
        self._dir_combo.setCurrentIndex(0)
        self._index_edit.clear()
        self._name_edit.clear()
        self._apply_filter()


class _SdoWindow(_DetailWindow):
    """SDO 字典窗口（含筛选功能）。"""

    def __init__(self, parent, device, source_file):
        super().__init__(parent, "SDO 字典", device, source_file)
        self._all_rows = device.sdo_entries
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        filter_row = QHBoxLayout()
        self._obj_index_edit = QLineEdit()
        self._obj_index_edit.setPlaceholderText("Obj Index 关键字")
        self._subindex_edit = QLineEdit()
        self._subindex_edit.setPlaceholderText("SubIndex 关键字")
        self._access_combo = QComboBox()
        self._access_combo.addItems(["全部", "ro", "rw", "wo", "const"])
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("对象/子项名称关键字")
        apply_btn = QPushButton("筛选")
        reset_btn = QPushButton("重置")

        filter_row.addWidget(QLabel("Obj Index"))
        filter_row.addWidget(self._obj_index_edit)
        filter_row.addWidget(QLabel("SubIndex"))
        filter_row.addWidget(self._subindex_edit)
        filter_row.addWidget(QLabel("Access"))
        filter_row.addWidget(self._access_combo)
        filter_row.addWidget(QLabel("名称"))
        filter_row.addWidget(self._name_edit)
        filter_row.addWidget(apply_btn)
        filter_row.addWidget(reset_btn)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self._table = QTableWidget()
        self._setup_table(
            self._table,
            [
                "Obj Index", "Object", "Obj Type", "SubIndex",
                "子项名称", "类型", "Access", "Bits", "Default",
            ],
        )
        self._setup_table_ctx_menu(self._table)
        layout.addWidget(self._table)

        self._summary_label = QLabel()
        self._summary_label.setObjectName("statusLabel")
        layout.addWidget(self._summary_label)

        apply_btn.clicked.connect(self._apply_filter)
        reset_btn.clicked.connect(self._reset_filter)
        self._access_combo.currentIndexChanged.connect(self._apply_filter)
        self._obj_index_edit.returnPressed.connect(self._apply_filter)
        self._subindex_edit.returnPressed.connect(self._apply_filter)
        self._name_edit.returnPressed.connect(self._apply_filter)

        self._apply_filter()

    def _apply_filter(self) -> None:
        obj_index_key = self._obj_index_edit.text().strip().lower()
        subindex_key = self._subindex_edit.text().strip().lower()
        access_key = self._access_combo.currentText().strip().lower()
        name_key = self._name_edit.text().strip().lower()

        filtered = []
        for item in self._all_rows:
            if obj_index_key and obj_index_key not in self._na_text(item.obj_index).lower():
                continue
            if subindex_key and subindex_key not in self._na_text(item.subindex).lower():
                continue
            if access_key != "全部":
                access_value = self._na_text(item.access).lower()
                if access_key not in access_value:
                    continue
            if name_key:
                obj_name = self._na_text(item.obj_name).lower()
                sub_name = self._na_text(item.sub_name).lower()
                if name_key not in obj_name and name_key not in sub_name:
                    continue
            filtered.append(item)

        table_rows = [
            [
                self._na_text(item.obj_index),
                self._na_text(item.obj_name),
                self._na_text(item.obj_type),
                self._na_text(item.subindex),
                self._na_text(item.sub_name),
                self._na_text(item.data_type),
                self._na_text(item.access),
                self._na_text(item.bit_size),
                self._na_text(item.default),
            ]
            for item in filtered
        ]
        self._fill_table(self._table, table_rows)
        self._summary_label.setText(f"SDO 条目：{len(filtered)} / {len(self._all_rows)}")

    def _reset_filter(self) -> None:
        self._obj_index_edit.clear()
        self._subindex_edit.clear()
        self._access_combo.setCurrentIndex(0)
        self._name_edit.clear()
        self._apply_filter()


class _MailboxDcWindow(_DetailWindow):
    """Mailbox / DC 窗口。"""

    def __init__(self, parent, device, source_file):
        super().__init__(parent, "Mailbox / DC", device, source_file)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        table = QTableWidget()
        self._setup_table(table, ["字段", "值"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._setup_table_ctx_menu(table)

        info = self._device.mailbox_dc
        rows = [
            ["CoE", self._na_text(info.coe)],
            ["FoE", self._na_text(info.foe)],
            ["EoE", self._na_text(info.eoe)],
            ["SoE", self._na_text(info.soe)],
            ["VoE", self._na_text(info.voe)],
            ["DC 支持", self._na_text(info.dc_supported)],
            ["AssignActivate", self._na_text(info.dc_assign_activate)],
            ["Sync0 Cycle", self._na_text(info.dc_sync0_cycle)],
            ["Sync1 Cycle", self._na_text(info.dc_sync1_cycle)],
        ]
        self._fill_table(table, rows)
        layout.addWidget(table)


# ───────────────────────── UI 页面 ─────────────────────────

class EsiPage(QWidget):
    def __init__(self, status_cb: Callable[[str, int], None]) -> None:
        super().__init__()
        self._status_cb = status_cb
        self._esi_results: Dict[str, EsiParseResult] = {}
        self._active_file: str = ""
        self._active_device: Optional[EsiDevice] = None

        self._build_ui()
        self._bind_events()
        self._set_controls_enabled(False)

    # ── UI 构建 ──────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # 操作指引
        self.esi_guide_label = QLabel(
            "步骤：① 选择 ESI XML 文件 → ② 点击「解析」→ ③ 左侧按钮打开详情窗口 → ④ 右侧目录切换文件进行对比"
        )
        self.esi_guide_label.setWordWrap(True)
        self.esi_guide_label.setObjectName("guideLabel")
        root.addWidget(self.esi_guide_label)

        # ── 文件操作区 ──
        top_box = QGroupBox("文件操作")
        top_grid = QGridLayout(top_box)
        top_grid.setVerticalSpacing(6)

        self.esi_file_edit = QLineEdit()
        self.esi_file_edit.setReadOnly(True)
        self.esi_file_edit.setPlaceholderText("请选择 ESI XML 文件...")
        self.esi_select_btn = QPushButton("选择 XML")
        self.esi_select_btn.setObjectName("secondaryBtn")
        self.esi_parse_btn = QPushButton("解析")
        self.esi_parse_btn.setEnabled(False)
        self.esi_export_btn = QPushButton("导出 JSON")
        self.esi_export_btn.setEnabled(False)
        self.esi_status_label = QLabel("未加载 XML。")
        self.esi_status_label.setObjectName("statusLabel")

        top_grid.addWidget(QLabel("XML 文件"), 0, 0)
        top_grid.addWidget(self.esi_file_edit, 0, 1, 1, 3)
        top_grid.addWidget(self.esi_select_btn, 0, 4)
        top_grid.addWidget(self.esi_parse_btn, 0, 5)
        top_grid.addWidget(self.esi_export_btn, 0, 6)
        top_grid.addWidget(self.esi_status_label, 1, 0, 1, 7)
        root.addWidget(top_box)

        # ── 主内容区：左右面板 ──
        splitter = QSplitter(Qt.Horizontal)

        # 左侧 — 设备 & 信息按钮
        left_panel = QGroupBox("设备信息查看")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        device_row = QHBoxLayout()
        device_row.addWidget(QLabel("设备:"))
        self.esi_device_combo = QComboBox()
        self.esi_device_combo.setEnabled(False)
        self.esi_device_combo.setMinimumWidth(180)
        device_row.addWidget(self.esi_device_combo, stretch=1)
        left_layout.addLayout(device_row)

        self.btn_basic = QPushButton("基础信息")
        self.btn_sm_fmmu = QPushButton("SM / FMMU")
        self.btn_pdo = QPushButton("PDO 映射")
        self.btn_sdo = QPushButton("SDO 字典")
        self.btn_mailbox = QPushButton("Mailbox / DC")

        for btn in [self.btn_basic, self.btn_sm_fmmu, self.btn_pdo, self.btn_sdo, self.btn_mailbox]:
            btn.setEnabled(False)
            left_layout.addWidget(btn)

        left_layout.addStretch(1)

        self.btn_copy_summary = QPushButton("复制设备摘要")
        self.btn_copy_summary.setObjectName("secondaryBtn")
        self.btn_copy_summary.setEnabled(False)
        left_layout.addWidget(self.btn_copy_summary)

        splitter.addWidget(left_panel)

        # 右侧 — 已加载文件目录
        right_panel = QGroupBox("已加载文件")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(6)

        self.esi_file_list = QListWidget()
        self.esi_file_list.setAlternatingRowColors(True)
        right_layout.addWidget(self.esi_file_list)

        file_btn_row = QHBoxLayout()
        self.btn_remove_file = QPushButton("移除选中")
        self.btn_remove_file.setObjectName("secondaryBtn")
        self.btn_remove_file.setEnabled(False)
        self.btn_clear_files = QPushButton("清空全部")
        self.btn_clear_files.setObjectName("secondaryBtn")
        self.btn_clear_files.setEnabled(False)
        file_btn_row.addWidget(self.btn_remove_file)
        file_btn_row.addWidget(self.btn_clear_files)
        right_layout.addLayout(file_btn_row)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, stretch=1)

        # 概览标签
        self.esi_overview_label = QLabel("解析概览：尚未解析文件。")
        self.esi_overview_label.setObjectName("statusLabel")
        root.addWidget(self.esi_overview_label)

        # 告警区
        warning_box = QGroupBox("解析告警")
        warning_root = QVBoxLayout(warning_box)
        self.esi_warning_text = QTextEdit()
        self.esi_warning_text.setReadOnly(True)
        self.esi_warning_text.setPlaceholderText("解析后将在此显示告警信息...")
        self.esi_warning_text.setMaximumHeight(110)
        warning_root.addWidget(self.esi_warning_text)
        root.addWidget(warning_box)

    # ── 事件绑定 ──────────────────────────────────────────

    def _bind_events(self) -> None:
        self.esi_select_btn.clicked.connect(self.browse_esi_file)
        self.esi_parse_btn.clicked.connect(self.load_esi_xml)
        self.esi_device_combo.currentIndexChanged.connect(self._on_device_changed)
        self.esi_export_btn.clicked.connect(self.export_esi_json)

        self.btn_basic.clicked.connect(self.open_basic_info)
        self.btn_sm_fmmu.clicked.connect(self.open_sm_fmmu)
        self.btn_pdo.clicked.connect(self.open_pdo)
        self.btn_sdo.clicked.connect(self.open_sdo)
        self.btn_mailbox.clicked.connect(self.open_mailbox_dc)
        self.btn_copy_summary.clicked.connect(self.copy_current_device_summary)

        self.esi_file_list.currentRowChanged.connect(self._on_file_selected)
        self.btn_remove_file.clicked.connect(self._remove_file)
        self.btn_clear_files.clicked.connect(self._clear_all_files)

    # ── 状态管理 ──────────────────────────────────────────

    def _status(self, message: str, timeout: int = 3000) -> None:
        self._status_cb(message, timeout)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.esi_device_combo.setEnabled(enabled)
        self.esi_export_btn.setEnabled(enabled)
        for btn in [self.btn_basic, self.btn_sm_fmmu, self.btn_pdo, self.btn_sdo, self.btn_mailbox]:
            btn.setEnabled(enabled)
        self.btn_copy_summary.setEnabled(enabled)

    def _get_active_result(self) -> Optional[EsiParseResult]:
        if not self._active_file:
            return None
        return self._esi_results.get(self._active_file)

    # ── 文件操作 ──────────────────────────────────────────

    def browse_esi_file(self) -> None:
        current = self.esi_file_edit.text().strip()
        base_dir = os.path.dirname(current) if current else os.path.dirname(__file__)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 ESI XML 文件",
            base_dir,
            "XML 文件 (*.xml);;所有文件 (*.*)",
        )
        if file_path:
            self.esi_file_edit.setText(file_path)
            self.esi_parse_btn.setEnabled(True)
            self.esi_status_label.setText("已选择 XML，请点击「解析」。")

    def load_esi_xml(self) -> None:
        file_path = self.esi_file_edit.text().strip()
        if not file_path:
            self._status("请先选择 XML 文件。", 4000)
            self.esi_status_label.setText("未选择 XML。")
            return
        if not os.path.isfile(file_path):
            self._status("XML 文件不存在。", 4000)
            self.esi_status_label.setText("文件不存在。")
            return

        # 如果已加载过该文件，直接激活
        abs_path = os.path.abspath(file_path)
        if abs_path in self._esi_results:
            self._status("该文件已加载，已切换为当前活动文件。", 3000)
            self._select_file_in_list(abs_path)
            return

        try:
            result = parse_esi_file(file_path)
        except Exception as err:
            self.esi_status_label.setText(f"解析失败：{err}")
            self._status(f"XML 解析失败：{err}", 5000)
            return

        self._esi_results[abs_path] = result

        # 自动保存解析结果到 output/
        try:
            base_runtime = (
                os.path.dirname(sys.executable)
                if getattr(sys, "frozen", False)
                else os.path.dirname(os.path.abspath(__file__))
            )
            output_dir = os.path.join(base_runtime, "output")
            os.makedirs(output_dir, exist_ok=True)
            snapshot_path = os.path.join(output_dir, "last_esi_result.json")
            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(to_export_dict(result), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # 添加到文件列表 (存储完整路径在 UserRole 中)
        display_name = os.path.basename(abs_path)
        item = QListWidgetItem(display_name)
        item.setData(Qt.UserRole, abs_path)
        self.esi_file_list.blockSignals(True)
        self.esi_file_list.addItem(item)
        self.esi_file_list.blockSignals(False)
        self.btn_remove_file.setEnabled(True)
        self.btn_clear_files.setEnabled(True)

        # 选中新添加的文件（会触发 _on_file_selected）
        last_idx = self.esi_file_list.count() - 1
        self.esi_file_list.setCurrentRow(last_idx)

        msg = f"解析成功：设备 {len(result.devices)} 个，告警 {len(result.warnings)} 条。"
        self.esi_status_label.setText(msg)
        self._status(msg, 5000)

    def _select_file_in_list(self, abs_path: str) -> None:
        for i in range(self.esi_file_list.count()):
            if self.esi_file_list.item(i).data(Qt.UserRole) == abs_path:
                self.esi_file_list.setCurrentRow(i)
                return

    def _on_file_selected(self, row: int) -> None:
        if row < 0:
            self._active_file = ""
            self._active_device = None
            self._set_controls_enabled(False)
            self.esi_device_combo.clear()
            self._update_overview()
            self._update_warnings()
            return

        self._active_file = self.esi_file_list.item(row).data(Qt.UserRole)
        display_name = os.path.basename(self._active_file)

        result = self._get_active_result()
        if result is None:
            return

        self._active_device = None
        self.esi_device_combo.blockSignals(True)
        self.esi_device_combo.clear()

        for idx, device in enumerate(result.devices, start=1):
            device_name = self._na_text(device.basic_info.device_name)
            product_code = self._na_text(device.basic_info.product_code)
            self.esi_device_combo.addItem(f"{idx}. {device_name} ({product_code})", idx - 1)

        self.esi_device_combo.blockSignals(False)

        has_device = bool(result.devices)
        self._set_controls_enabled(has_device)
        self._update_warnings()
        self._update_overview()

        if has_device:
            # Force signal emission: combo may already be at index 0 from addItem
            self.esi_device_combo.setCurrentIndex(-1)
            self.esi_device_combo.setCurrentIndex(0)
        else:
            self._active_device = None
            self._update_overview()

        self.esi_status_label.setText(f"已切换至：{display_name}")

    def _on_device_changed(self, index: int) -> None:
        result = self._get_active_result()
        if not result or index < 0:
            self._active_device = None
            self._update_overview()
            return

        device_index = self.esi_device_combo.itemData(index)
        if device_index is None or not isinstance(device_index, int):
            return
        if device_index < 0 or device_index >= len(result.devices):
            return

        self._active_device = result.devices[device_index]
        self._update_overview()

    def _remove_file(self) -> None:
        current_row = self.esi_file_list.currentRow()
        if current_row < 0:
            self._status("请先选中要移除的文件。", 3000)
            return

        item = self.esi_file_list.item(current_row)
        display_name = item.text()
        to_remove = item.data(Qt.UserRole)

        self.esi_file_list.blockSignals(True)
        self.esi_file_list.takeItem(current_row)
        self.esi_file_list.blockSignals(False)

        if to_remove and to_remove in self._esi_results:
            del self._esi_results[to_remove]

        remaining = self.esi_file_list.count()
        self.btn_remove_file.setEnabled(remaining > 0)
        self.btn_clear_files.setEnabled(remaining > 0)

        if remaining == 0:
            self._active_file = ""
            self._active_device = None
            self._set_controls_enabled(False)
            self.esi_device_combo.clear()
            self._update_overview()
            self._update_warnings()
        elif current_row < remaining:
            self.esi_file_list.setCurrentRow(current_row)
        else:
            self.esi_file_list.setCurrentRow(remaining - 1)

        self._status(f"已移除：{display_name}", 3000)

    def _clear_all_files(self) -> None:
        self._esi_results.clear()
        self._active_file = ""
        self._active_device = None

        self.esi_file_list.blockSignals(True)
        self.esi_file_list.clear()
        self.esi_file_list.blockSignals(False)

        self.btn_remove_file.setEnabled(False)
        self.btn_clear_files.setEnabled(False)
        self._set_controls_enabled(False)
        self.esi_device_combo.clear()
        self._update_overview()
        self._update_warnings()
        self.esi_status_label.setText("已清空全部文件。")
        self._status("已清空全部已加载文件。", 3000)

    # ── 打开详情窗口 ──────────────────────────────────────

    def _check_active_device(self) -> bool:
        if not self._active_device:
            self._status("请先选择设备和文件。", 3000)
            return False
        return True

    def open_basic_info(self) -> None:
        if not self._check_active_device():
            return
        w = _BasicInfoWindow(self, self._active_device, self._active_file)
        w.show()

    def open_sm_fmmu(self) -> None:
        if not self._check_active_device():
            return
        w = _SmFmmuWindow(self, self._active_device, self._active_file)
        w.show()

    def open_pdo(self) -> None:
        if not self._check_active_device():
            return
        w = _PdoWindow(self, self._active_device, self._active_file)
        w.show()

    def open_sdo(self) -> None:
        if not self._check_active_device():
            return
        w = _SdoWindow(self, self._active_device, self._active_file)
        w.show()

    def open_mailbox_dc(self) -> None:
        if not self._check_active_device():
            return
        w = _MailboxDcWindow(self, self._active_device, self._active_file)
        w.show()

    # ── 导出 / 复制 ───────────────────────────────────────

    def export_esi_json(self) -> None:
        result = self._get_active_result()
        if not result:
            self._status("没有可导出的解析结果。", 4000)
            return

        source = result.source_file
        if source:
            default_path = f"{os.path.splitext(source)[0]}.parsed.json"
        else:
            default_path = os.path.join(os.path.dirname(__file__), "esi.parsed.json")

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出解析结果为 JSON",
            default_path,
            "JSON 文件 (*.json);;所有文件 (*.*)",
        )
        if not save_path:
            return

        try:
            data = to_export_dict(result)
            with open(save_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError as err:
            self._status(f"导出失败：{err}", 5000)
            self.esi_status_label.setText("导出 JSON 失败。")
            return

        self._status(f"导出成功：{save_path}", 5000)
        self.esi_status_label.setText("JSON 导出成功。")

    def copy_current_device_summary(self) -> None:
        if not self._active_device:
            self._status("当前没有可复制的设备摘要。", 4000)
            return

        basic = self._active_device.basic_info
        text = (
            f"设备名称：{self._na_text(basic.device_name)}\n"
            f"厂商：{self._na_text(basic.vendor_name)} (ID: {self._na_text(basic.vendor_id)})\n"
            f"类型：{self._na_text(basic.type_name)}\n"
            f"ProductCode：{self._na_text(basic.product_code)}\n"
            f"RevisionNo：{self._na_text(basic.revision_no)}\n"
            f"PDO 条目数：{len(self._active_device.pdo_entries)}\n"
            f"SDO 条目数：{len(self._active_device.sdo_entries)}\n"
            f"SM 条目数：{len(self._active_device.sm_entries)}\n"
            f"FMMU 条目数：{len(self._active_device.fmmu_entries)}"
        )
        QApplication.clipboard().setText(text)
        self._status("当前设备摘要已复制到剪贴板。", 4000)

    # ── 渲染 ──────────────────────────────────────────────

    def _update_warnings(self) -> None:
        result = self._get_active_result()
        if result is None:
            self.esi_warning_text.setPlainText("无告警，结构完整度良好。")
            return

        warnings = result.warnings
        if not warnings:
            self.esi_warning_text.setPlainText("无告警，结构完整度良好。")
            return

        lines = []
        for idx, item in enumerate(warnings, start=1):
            path = f" @ {item.path}" if item.path else ""
            lines.append(f"{idx}. [{item.code}] {item.message}{path}")
        self.esi_warning_text.setPlainText("\n".join(lines))

    def _update_overview(self) -> None:
        if not self._esi_results:
            self.esi_overview_label.setText("解析概览：尚未解析文件。")
            return

        file_count = len(self._esi_results)
        result = self._get_active_result()
        if result is None:
            self.esi_overview_label.setText(f"解析概览：已加载 {file_count} 个文件，未选择活动文件。")
            return

        device_count = len(result.devices)
        warning_count = len(result.warnings)
        selected_device = "未选择"
        if self._active_device is not None:
            basic = self._active_device.basic_info
            selected_device = f"{self._na_text(basic.device_name)} ({self._na_text(basic.product_code)})"

        self.esi_overview_label.setText(
            f"解析概览：已加载 {file_count} 个文件，当前文件设备 {device_count} 个，"
            f"告警 {warning_count} 条，当前设备：{selected_device}"
        )

    # ── 工具方法 ──────────────────────────────────────────

    @staticmethod
    def _na_text(value: Optional[str]) -> str:
        if value is None:
            return NA_TEXT
        text = str(value).strip()
        if not text:
            return NA_TEXT
        return text
