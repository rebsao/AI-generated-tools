CCAT — USART & EtherCAT ESI 工具 — 运行说明

1) 安装方式（推荐）
- 双击 installer\Setup-CCAT-1.0.0.exe，按向导完成安装。
- 安装无需管理员权限（按用户安装，默认装到 %LOCALAPPDATA%\Programs\CCAT）。
- 向导中可选择「创建桌面快捷方式」（默认勾选），安装完成后可立即启动。
- 卸载：Windows 设置 → 应用 → 找到 CCAT 卸载；或运行安装目录下 unins000.exe。

2) 绿色版（可选）
- app\ 目录是免安装版本，直接双击 CCAT.exe 即可运行（不创建快捷方式）。

3) 兼容范围
- Windows 10/11 x64。

4) 目录说明
- installer\ : 安装包（Setup-CCAT-1.0.0.exe）。
- app\       : 绿色版程序（构建产物）。
- source\    : 源码（main.py / esi_page.py / serial_page.py / ibm_theme.py / icon.ico 等）。
- CCAT.iss   : Inno Setup 安装脚本。

5) 功能说明
- 选择并解析 ESI XML 文件。
- 查看设备基础信息、SM/FMMU、PDO 映射、SDO 字典、Mailbox/DC 等。
- 支持 PDO / SDO 条目筛选。
- 右键表格可复制单行、单元格或全部行。
- 支持导出解析结果为 JSON（自动保存到 output\last_esi_result.json）。
- 串口页：USART 收发与状态查看（USART: YES/NO 徽标实时显示）。

6) 从源码构建（可选）
- 需要 Python 3.10+：pip install -r source\requirements.txt
- 打包 exe：pyinstaller --noconfirm --onedir --windowed --name CCAT --icon source\icon.ico main.py（在 source 目录）
- 生成安装包：ISCC CCAT.iss（需安装 Inno Setup 6）
