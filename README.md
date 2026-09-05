# 万能媒体浏览器 (MediaBrowser)

一个支持几乎所有图片和视频格式的桌面媒体浏览器，基于 PySide6 + VLC + LibRaw 开发，开箱即用，无需额外安装解码器。

## ✨ 功能特性

- 🖼️ **万能图片浏览** — 支持 JPG/PNG/GIF/BMP/WEBP/TIFF/HEIC/AVIF/PSD/TGA 等
- 📷 **单反 RAW 支持** — 基于 LibRaw，支持佳能 CR2/CR3、尼康 NEF、索尼 ARW、通用 DNG 等几乎所有 RAW 格式
- 🎬 **万能视频播放** — 基于 VLC 引擎，支持 MP4/AVI/MKV/MOV/FLV/WMV/RMVB 等几乎所有视频格式
- 🎵 **音频播放** — 支持 MP3/WAV/FLAC/AAC/OGG 等
- 📁 **文件浏览器** — 左侧树形文件浏览器，支持"此电脑"所有驱动器
- 🖼️ **缩略图列表** — 底部显示当前文件夹媒体文件缩略图
- 🔍 **图片操作** — 滚轮缩放、拖拽平移、旋转、适应窗口/原始大小
- ⏯️ **视频控制** — 播放/暂停、进度条、音量、全屏
- 📂 **拖放支持** — 直接拖放文件或文件夹到窗口打开
- ⌨️ **快捷键** — 丰富的键盘快捷键支持
- 🌙 **深色界面** — 护眼深色主题，高 DPI 适配

## 📋 支持格式

### 图片格式

| 类别 | 格式 |
|------|------|
| 普通格式 | JPG, JPEG, PNG, GIF(动画), BMP, WEBP, TIFF, ICO, TGA, PSD, PCX, PPM, PGM, PBM, XBM, XPM |
| 苹果格式 | HEIC, HEIF (iPhone 照片) |
| 新一代 | AVIF |
| 单反 RAW | CR2, CR3 (佳能), NEF, NRW (尼康), ARW, SRF, SR2 (索尼), DNG (通用), ORF (奥林巴斯), RW2 (松下), PEF (宾得), RAF (富士), RWL (徕卡), SRW (三星), 3FR (哈苏), ERF, MEF, MOS, MRW, X3F, KDC, DCR, IIQ 等 |

### 视频格式

MP4, AVI, MKV, MOV, FLV, WMV, RMVB, M4V, TS, M2TS, MPG, MPEG, 3GP, VOB, WEBM, ASF, DIVX, F4V 等几乎所有格式

### 音频格式

MP3, WAV, FLAC, AAC, OGG, WMA, M4A, APE, OPUS 等

## 🚀 快速开始

### 环境要求

- Windows 10/11 (64-bit)
- Python 3.10+ (开发用)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 命令行参数

```bash
# 直接打开文件
python main.py "C:\path\to\image.jpg"

# 直接打开文件夹
python main.py "C:\path\to\folder"
```

## 🔨 构建 EXE

### 1. 准备 VLC 运行时

下载 VLC 便携版并解压，将 `libvlc.dll`、`libvlccore.dll` 和 `plugins/` 目录放到 `vlc-runtime/` 目录下。

下载地址：https://www.videolan.org/vlc/

### 2. 执行打包脚本

```bash
build.bat
```

或手动执行：

```bash
pyinstaller --name "MediaBrowser" --windowed --noconfirm --clean \
    --add-data "vlc-runtime\libvlc.dll;." \
    --add-data "vlc-runtime\libvlccore.dll;." \
    --add-data "vlc-runtime\plugins;plugins" \
    --collect-all rawpy \
    --collect-all pillow_heif \
    main.py
```

### 3. 输出

打包后的文件在 `dist/MediaBrowser/` 目录下，双击 `MediaBrowser.exe` 即可运行。

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `空格` | 播放/暂停 (视频/音频) |
| `←` `→` | 上一个/下一个媒体文件 |
| `↑` `↓` | 音量加/减 (视频播放时) |
| `F` | 全屏切换 |
| `R` | 图片旋转 90 度 |
| `滚轮` | 图片缩放 |
| `0` | 图片适应窗口 |
| `Esc` | 退出全屏 |

## 📁 项目结构

```
MediaBrowser/
├── main.py              # 主程序（包含所有功能）
├── requirements.txt     # Python 依赖
├── build.bat            # Windows 打包脚本
├── .gitignore           # Git 忽略文件
└── README.md            # 项目说明
```

## 🛠️ 技术栈

- **GUI 框架**: [PySide6](https://doc.qt.io/qtforpython/) (Qt 6)
- **视频播放**: [python-vlc](https://github.com/oaubert/python-vlc) + [VLC](https://www.videolan.org/vlc/)
- **图片处理**: [Pillow](https://python-pillow.org/)
- **RAW 解码**: [rawpy](https://github.com/letmaik/rawpy) (LibRaw)
- **HEIC 支持**: [pillow-heif](https://github.com/bigcat88/pillow_heif)
- **AVIF 支持**: [pillow-avif-plugin](https://github.com/bigcat88/pillow_avif)
- **打包工具**: [PyInstaller](https://www.pyinstaller.org/)

## 📝 注意事项

1. 打包后的 `_internal` 文件夹包含 VLC 运行时和程序依赖，请勿删除
2. 单反 RAW 文件较大（20-50MB），加载可能需要 1-3 秒
3. 首次启动可能较慢（VLC 插件加载），属正常现象
4. 分发时请将整个 `MediaBrowser` 文件夹一起复制

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
