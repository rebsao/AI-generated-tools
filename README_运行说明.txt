MP3 Player — 运行说明

1) 安装方式（推荐）
- 双击 installer\Setup-MP3Player-1.0.0.exe，按向导完成安装。
- 安装无需管理员权限（按用户安装，默认装到 %LOCALAPPDATA%\Programs\MP3 Player）。
- 向导中可选择「创建桌面快捷方式」（默认勾选），安装完成后可立即启动。
- 卸载：Windows 设置 → 应用 → 找到 MP3 Player 卸载；或运行安装目录下 unins000.exe。

2) 绿色版（可选）
- app\ 目录是免安装版本，直接双击 MP3Player.exe 即可运行（不创建快捷方式）。

3) 兼容范围
- Windows 10/11 x64。
- 支持的音频格式：mp3 / wav / ogg / flac / m4a / aac / wma / ape。

4) 目录说明
- installer\ : 安装包（Setup-MP3Player-1.0.0.exe）。
- app\       : 绿色版程序（构建产物）。
- source\    : 源码（main.py / player_page.py / theme.py / icon.ico 等）。
- MP3Player.iss : Inno Setup 安装脚本。

5) 功能说明
- 打开文件夹：点击左侧「打开文件夹…」、菜单「文件 → 打开文件夹…」（Ctrl+O），
  或将文件夹直接拖入窗口。
- 左侧文件树：像 VSCode 一样浏览目录，单击文件夹即在右侧显示其中的音乐列表；
  双击树中的音频文件可直接播放。
- 音乐列表：显示序号 / 曲名 / 艺术家 / 时长；双击任意行开始播放；
  文件名形如 "歌手 - 歌名.ext" 时自动拆分艺术家与曲名。
- 播放模式：点击模式按钮循环切换 —— 顺序播放 → 列表循环 → 单曲循环 → 随机播放。
- 基本控制：上一首 / 播放-暂停 / 下一首；进度条可拖动跳转；
  音量滑条可调；空格键也可播放/暂停。

6) 从源码构建（可选）
- 需要 Python 3.10+：pip install -r source\requirements.txt
- 打包 exe：pyinstaller --noconfirm --onedir --windowed --name MP3Player --icon source\icon.ico main.py（在 source 目录）
- 生成安装包：ISCC MP3Player.iss（需安装 Inno Setup 6）
