# -*- coding: utf-8 -*-
"""
万能媒体浏览器 - 支持几乎所有图片和视频格式
图片: JPG, PNG, GIF, BMP, WEBP, TIFF, ICO, SVG 等
视频: MP4, AVI, MKV, MOV, FLV, WMV, RMVB, M4V, TS 等 (基于VLC)
"""

import sys
import os
import platform
import logging
import traceback

# ---------- 日志配置 ----------
def setup_logging():
    """配置日志输出到文件和控制台"""
    log_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, "debug.log")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("=" * 50)
    logging.info("程序启动")
    logging.info(f"Python: {sys.version}")
    logging.info(f"Platform: {platform.platform()}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    if hasattr(sys, '_MEIPASS'):
        logging.info(f"_MEIPASS: {sys._MEIPASS}")
    return log_file

LOG_FILE = setup_logging()

def log_except(msg=""):
    """记录异常堆栈"""
    logging.error(f"{msg}\n{traceback.format_exc()}")

# ---------- VLC 初始化 ----------
def find_vlc():
    """查找VLC运行时，返回vlc模块或None"""
    logging.info("开始查找VLC运行时...")
    # 确定候选目录列表
    candidate_dirs = []

    # PyInstaller打包后的_MEIPASS目录（onefile模式的临时目录或onedir的_internal）
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        candidate_dirs.append(meipass)
        logging.info(f"  候选: _MEIPASS = {meipass}")

    # 打包后exe所在目录
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidate_dirs.append(exe_dir)
        candidate_dirs.append(os.path.join(exe_dir, "_internal"))
        candidate_dirs.append(os.path.join(exe_dir, "vlc"))
        logging.info(f"  候选: exe_dir = {exe_dir}")
    else:
        # 开发模式：脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_dirs.append(script_dir)
        candidate_dirs.append(os.path.join(script_dir, "vlc"))

    # 系统安装路径
    candidate_dirs.extend([
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
    ])

    for p in candidate_dirs:
        if p and os.path.isfile(os.path.join(p, "libvlc.dll")):
            logging.info(f"  找到VLC: {p}")
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            # 设置VLC插件路径
            plugin_path = os.path.join(p, "plugins")
            if os.path.isdir(plugin_path):
                os.environ["VLC_PLUGIN_PATH"] = plugin_path
                logging.info(f"  插件路径: {plugin_path}")
            try:
                import vlc
                logging.info("VLC导入成功")
                return vlc
            except Exception as e:
                logging.error(f"VLC导入失败: {e}")
                continue
    # 最后尝试直接import（可能系统已装VLC且在PATH中）
    try:
        import vlc
        logging.info("VLC从系统PATH导入成功")
        return vlc
    except Exception as e:
        logging.error(f"VLC从系统PATH导入失败: {e}")
    logging.warning("未找到VLC运行时，视频播放将不可用")
    return None

vlc_mod = find_vlc()
VLC_AVAILABLE = vlc_mod is not None


# ---------- 全局VLC管理器（共享instance，延迟初始化） ----------
class VLCManager:
    """全局VLC管理器，所有播放器共享同一个instance"""
    _instance = None
    _vlc_instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_instance(self):
        """获取或创建VLC instance（单例）"""
        if not VLC_AVAILABLE:
            return None
        if self._vlc_instance is None:
            try:
                logging.info("创建VLC Instance...")
                self._vlc_instance = vlc_mod.Instance('--no-xlib', '--quiet', '--no-video-title-show')
                logging.info("VLC Instance创建成功")
            except Exception as e:
                log_except("VLC Instance创建失败")
                self._vlc_instance = None
        return self._vlc_instance

    def create_player(self, video_frame=None):
        """创建一个新的media_player，并绑定到video_frame"""
        inst = self.get_instance()
        if inst is None:
            return None
        try:
            player = inst.media_player_new()
            if video_frame is not None:
                # 延迟设置hwnd，确保widget已创建
                try:
                    wid = int(video_frame.winId())
                    if platform.system() == 'Windows':
                        player.set_hwnd(wid)
                    elif platform.system() == 'Linux':
                        player.set_xwindow(wid)
                    elif platform.system() == 'Darwin':
                        player.set_nsobject(wid)
                    logging.info(f"VLC player绑定到窗口 {wid}")
                except Exception as e:
                    logging.warning(f"设置VLC输出窗口失败: {e}")
            return player
        except Exception as e:
            log_except("创建VLC player失败")
            return None


vlc_mgr = VLCManager()

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeView, QListView, QStackedWidget, QToolBar,
    QStatusBar, QSlider, QPushButton, QLabel, QFileDialog, QMessageBox,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QDockWidget,
    QAbstractItemView, QSizePolicy, QFrame, QScrollArea, QComboBox,
    QToolButton, QMenu, QSplashScreen, QFileSystemModel
)
from PySide6.QtCore import (
    Qt, QSize, QTimer, QUrl, QMimeData, QPoint, QRect, Signal, QObject
)
from PySide6.QtGui import (
    QPixmap, QImage, QIcon, QAction, QKeySequence, QPainter, QColor,
    QFont, QCursor, QMovie, QTransform, QStandardItemModel, QStandardItem,
    QDragEnterEvent, QDropEvent
)

try:
    from PIL import Image, ImageSequence, ImageQt
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# RAW 格式支持 (单反 CR2/NEF/ARW/DNG 等)
try:
    import rawpy
    RAWPY_AVAILABLE = True
except ImportError:
    RAWPY_AVAILABLE = False

# HEIC/HEIF 支持
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

# AVIF 支持
try:
    import pillow_avif
    AVIF_AVAILABLE = True
except ImportError:
    AVIF_AVAILABLE = False

# numpy (rawpy 依赖)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# ---------- 支持的格式 ----------
IMAGE_EXTS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
    '.ico', '.svg', '.heic', '.heif', '.avif', '.jxr', '.wdp', '.ppm',
    '.pgm', '.pbm', '.pnm', '.tga', '.dds', '.pcx', '.xpm', '.xbm',
    '.cur', '.ani', '.flic', '.flc', '.fpx', '.pict', '.pct', '.pic',
    '.psd', '.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2',
    '.pef', '.sr2', '.raf', '.kdc', '.dcr', '.mrw', '.x3f', '.3fr',
    '.erf', '.mef', '.mos', '.nrw', '.qtk', '.rwl', '.srw'
}

VIDEO_EXTS = {
    '.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.rmvb', '.rm',
    '.m4v', '.ts', '.m2ts', '.mts', '.mpg', '.mpeg', '.3gp', '.3g2',
    '.vob', '.ogv', '.webm', '.asf', '.divx', '.xvid', '.dat', '.m1v',
    '.m2v', '.mp2', '.mpv', '.nut', '.swf', '.f4v', '.f4p', '.f4a',
    '.f4b', '.ifo', '.bup', '.amv', '.roq', '.nsv', '.drc', '.yuv',
    '.rmj', '.rms', '.rmx', '.rv', '.ra', '.mka', '.m3u', '.m3u8',
    '.pls', '.cue', '.iso'
}

AUDIO_EXTS = {
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.ape',
    '.alac', '.opus', '.aiff', '.aif', '.au', '.ra', '.mid', '.midi',
    '.amr', '.ac3', '.dts', '.tta', '.wv', '.shn', '.mka'
}

MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS


def is_image(path):
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS

def is_video(path):
    return os.path.splitext(path)[1].lower() in VIDEO_EXTS

def is_audio(path):
    return os.path.splitext(path)[1].lower() in AUDIO_EXTS

def is_media(path):
    return os.path.splitext(path)[1].lower() in MEDIA_EXTS


# ---------- 单反 RAW 格式扩展名 ----------
RAW_EXTS = {
    '.cr2', '.cr3', '.nef', '.nrw', '.arw', '.srf', '.sr2', '.dng',
    '.orf', '.rw2', '.pef', '.raf', '.kdc', '.dcr', '.mrw', '.x3f',
    '.3fr', '.erf', '.mef', '.mos', '.qtk', '.rwl', '.srw', '.raw',
    '.iiq', '.3fr', '.cine', '.ia', '.kc2', '.mdc', '.mmv', '.stc'
}


def load_image_to_pixmap(path):
    """
    万能图片加载函数，支持几乎所有图片格式。
    返回 (QPixmap, error_msg)，成功时 error_msg 为 None。
    """
    ext = os.path.splitext(path)[1].lower()
    last_error = None

    # 1. RAW 格式 (单反) - 使用 rawpy (LibRaw)
    if ext in RAW_EXTS:
        if RAWPY_AVAILABLE and NUMPY_AVAILABLE:
            try:
                with rawpy.imread(path) as raw:
                    # 使用默认参数解码，自动白平衡
                    rgb = raw.postprocess(
                        use_camera_wb=True,
                        no_auto_bright=False,
                        output_bps=8,
                        gamma=(2.222, 4.5),
                    )
                    h, w, ch = rgb.shape
                    if ch == 3:
                        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy()
                    else:
                        qimg = QImage(rgb.data, w, h, w * ch, QImage.Format_RGBA8888).copy()
                    pix = QPixmap.fromImage(qimg)
                    if not pix.isNull():
                        return pix, None
                    last_error = "RAW解码后图像为空"
            except Exception as e:
                last_error = f"RAW解码失败: {e}"
        else:
            last_error = "未安装rawpy，无法解码RAW格式"

    # 2. HEIC/HEIF - pillow-heif 已注册 opener
    if ext in ('.heic', '.heif'):
        if not HEIF_AVAILABLE:
            last_error = "未安装pillow-heif，无法解码HEIC格式"
        # 继续走 Pillow 路径

    # 3. AVIF - pillow-avif 已注册
    if ext == '.avif' and not AVIF_AVAILABLE:
        last_error = "未安装pillow-avif，无法解码AVIF格式"
        # 继续走 Pillow 路径

    # 4. 通用 Pillow 路径 (JPG/PNG/BMP/WEBP/TIFF/HEIC/AVIF/PSD/TGA 等)
    if PILLOW_AVAILABLE:
        try:
            img = Image.open(path)
            img.load()  # 强制加载，确保能检测错误
            # 处理多帧图像（TIFF、GIF、ICO等），取第一帧
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                img.seek(0)
            # 统一转为 RGBA
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            # 使用 ImageQt 转换，更稳定
            try:
                qimg = ImageQt.ImageQt(img)
                pix = QPixmap.fromImage(qimg)
            except Exception:
                # 备用方案：手动转换
                if img.mode == 'RGBA':
                    data = img.tobytes('raw', 'RGBA')
                    qimg = QImage(data, img.width, img.height, img.width * 4, QImage.Format_RGBA8888).copy()
                else:
                    data = img.tobytes('raw', 'RGB')
                    qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format_RGB888).copy()
                pix = QPixmap.fromImage(qimg)
            if not pix.isNull():
                return pix, None
            last_error = "Pillow转换后图像为空"
        except Exception as e:
            last_error = f"Pillow加载失败: {e}"

    # 5. Qt 原生加载 (最后手段)
    try:
        pix = QPixmap(path)
        if not pix.isNull():
            return pix, None
        last_error = last_error or "Qt无法加载此图片格式"
    except Exception as e:
        last_error = f"Qt加载失败: {e}"

    return None, last_error or "未知错误"


# ---------- 图片查看器 ----------
class ImageViewer(QGraphicsView):
    """支持缩放、平移、旋转的图片查看器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFrameShape(QFrame.NoFrame)
        self.setBackgroundBrush(QColor(30, 30, 30))
        self._zoom = 0
        self._rotation = 0
        self._movie = None
        self._current_path = None

    def load_image(self, path):
        """加载图片，支持GIF动画和几乎所有图片格式。返回 (成功, 错误信息)"""
        logging.info(f"ImageViewer.load_image: {path}")
        self._current_path = path
        self._zoom = 0
        self._rotation = 0
        self.resetTransform()

        # 停止之前的GIF
        if self._movie:
            self._movie.stop()
            self._movie = None

        ext = os.path.splitext(path)[1].lower()
        logging.info(f"文件扩展名: {ext}")

        # GIF动画用QMovie
        if ext == '.gif':
            logging.info("使用QMovie加载GIF")
            self._movie = QMovie(path)
            if self._movie.isValid():
                self._movie.frameChanged.connect(self._on_gif_frame)
                self._movie.start()
                self._pixmap_item.setPixmap(self._movie.currentPixmap())
                self._scene.setSceneRect(self._pixmap_item.boundingRect())
                self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
                logging.info("GIF加载成功")
                return True, None
            logging.warning("QMovie无效，回退到通用加载")

        # 使用万能图片加载函数
        logging.info("调用load_image_to_pixmap")
        pixmap, error = load_image_to_pixmap(path)

        if pixmap is None or pixmap.isNull():
            logging.error(f"图片加载失败: {error}")
            return False, error or "无法加载图片"

        logging.info(f"图片加载成功，尺寸: {pixmap.width()}x{pixmap.height()}")
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(self._pixmap_item.boundingRect())
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
        return True, None

    def _on_gif_frame(self):
        if self._movie:
            self._pixmap_item.setPixmap(self._movie.currentPixmap())

    def wheelEvent(self, event):
        """滚轮缩放"""
        if event.angleDelta().y() > 0:
            factor = 1.15
            self._zoom += 1
        else:
            factor = 0.87
            self._zoom -= 1
        if self._zoom > 0:
            self.scale(factor, factor)
        elif self._zoom == 0:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
        else:
            self._zoom = 0
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def rotate(self, angle=90):
        """旋转图片"""
        self._rotation = (self._rotation + angle) % 360
        transform = QTransform()
        transform.rotate(self._rotation)
        self.setTransform(transform, False)
        if self._zoom == 0:
            self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def reset_zoom(self):
        """重置缩放和旋转"""
        self._zoom = 0
        self._rotation = 0
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def original_size(self):
        """原始大小显示"""
        self.resetTransform()
        self._zoom = 1
        self.scale(1, 1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.scale(1.15, 1.15)
            self._zoom += 1
        elif event.key() == Qt.Key_Minus:
            self.scale(0.87, 0.87)
            self._zoom -= 1
        elif event.key() == Qt.Key_0:
            self.reset_zoom()
        elif event.key() == Qt.Key_R:
            self.rotate(90)
        else:
            super().keyPressEvent(event)


# ---------- 视频播放器 ----------
class VideoPlayer(QWidget):
    """基于VLC的视频播放器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vlc_instance = None
        self._player = None
        self._current_path = None
        self._is_playing = False
        self._volume = 80
        self._muted = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(200)
        self._setup_ui()
        # 不立即初始化VLC，延迟到第一次播放时
        logging.info("VideoPlayer创建完成（VLC延迟初始化）")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 视频显示区域
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumSize(320, 240)
        layout.addWidget(self.video_frame, 1)

        # 控制栏
        self.controls = QWidget()
        self.controls.setStyleSheet("background-color: #2b2b2b; color: white;")
        ctrl_layout = QHBoxLayout(self.controls)
        ctrl_layout.setContentsMargins(10, 8, 10, 8)
        ctrl_layout.setSpacing(10)

        # 播放/暂停按钮
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.setStyleSheet("""
            QPushButton { background-color: #4a90d9; border: none; border-radius: 18px;
                          color: white; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #5aa0e9; }
        """)
        self.play_btn.clicked.connect(self.toggle_play)
        ctrl_layout.addWidget(self.play_btn)

        # 停止按钮
        self.stop_btn = QPushButton("■")
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: #555; border: none; border-radius: 16px;
                          color: white; font-size: 12px; }
            QPushButton:hover { background-color: #666; }
        """)
        self.stop_btn.clicked.connect(self.stop)
        ctrl_layout.addWidget(self.stop_btn)

        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #ccc; font-size: 12px;")
        self.time_label.setMinimumWidth(110)
        ctrl_layout.addWidget(self.time_label)

        # 进度条
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #444; border-radius: 2px; }
            QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0;
                                          background: #4a90d9; border-radius: 7px; }
            QSlider::sub-page:horizontal { background: #4a90d9; border-radius: 2px; }
        """)
        self.progress.sliderMoved.connect(self._seek)
        ctrl_layout.addWidget(self.progress, 1)

        # 音量按钮
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedSize(32, 32)
        self.mute_btn.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 16px; }")
        self.mute_btn.clicked.connect(self.toggle_mute)
        ctrl_layout.addWidget(self.mute_btn)

        # 音量滑块
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self._volume)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 3px; background: #444; border-radius: 1px; }
            QSlider::handle:horizontal { width: 10px; height: 10px; margin: -3px 0;
                                          background: #aaa; border-radius: 5px; }
        """)
        self.volume_slider.valueChanged.connect(self._set_volume)
        ctrl_layout.addWidget(self.volume_slider)

        # 全屏按钮
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedSize(32, 32)
        self.fullscreen_btn.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 16px; }")
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        ctrl_layout.addWidget(self.fullscreen_btn)

        layout.addWidget(self.controls)

    def _ensure_player(self):
        """确保VLC player已创建（延迟初始化）"""
        if self._player is not None:
            return True
        if not VLC_AVAILABLE:
            logging.warning("VLC不可用，无法创建player")
            return False
        logging.info("延迟初始化VLC player...")
        self._player = vlc_mgr.create_player(self.video_frame)
        if self._player is not None:
            self._player.audio_set_volume(self._volume)
            logging.info("VLC player创建成功")
            return True
        logging.error("VLC player创建失败")
        return False

    def load_video(self, path):
        """加载视频文件"""
        logging.info(f"加载视频: {path}")
        self._current_path = path
        if not self._ensure_player():
            return False
        try:
            inst = vlc_mgr.get_instance()
            media = inst.media_new(path)
            self._player.set_media(media)
            media.parse()
            self.play()
            logging.info("视频加载成功，开始播放")
            return True
        except Exception as e:
            log_except("加载视频失败")
            return False

    def play(self):
        if self._player:
            self._player.play()
            self._is_playing = True
            self.play_btn.setText("⏸")

    def pause(self):
        if self._player:
            self._player.pause()
            self._is_playing = False
            self.play_btn.setText("▶")

    def toggle_play(self):
        if self._is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        if self._player:
            self._player.stop()
            self._is_playing = False
            self.play_btn.setText("▶")
            self.progress.setValue(0)
            self.time_label.setText("00:00 / 00:00")

    def _seek(self, position):
        if self._player and self._player.get_length() > 0:
            self._player.set_time(int(position * self._player.get_length() / 1000))

    def _set_volume(self, value):
        self._volume = value
        if self._player:
            self._player.audio_set_volume(value)
        if value == 0:
            self._muted = True
            self.mute_btn.setText("🔇")
        else:
            self._muted = False
            self.mute_btn.setText("🔊")

    def toggle_mute(self):
        self._muted = not self._muted
        if self._player:
            self._player.audio_toggle_mute()
        if self._muted:
            self.mute_btn.setText("🔇")
        else:
            self.mute_btn.setText("🔊")

    def _toggle_fullscreen(self):
        parent = self.window()
        if parent.isFullScreen():
            parent.showNormal()
        else:
            parent.showFullScreen()

    def _update_progress(self):
        if not self._player or not self._is_playing:
            return
        try:
            length = self._player.get_length()
            current = self._player.get_time()
            if length > 0:
                self.progress.setValue(int(current * 1000 / length))
                self.time_label.setText(f"{self._format_time(current)} / {self._format_time(length)}")
        except Exception:
            pass

    @staticmethod
    def _format_time(ms):
        if ms < 0:
            ms = 0
        s = ms // 1000
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{sec:02d}"
        return f"{m:02d}:{sec:02d}"

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_play()
        elif event.key() == Qt.Key_Left:
            if self._player:
                self._player.set_time(max(0, self._player.get_time() - 5000))
        elif event.key() == Qt.Key_Right:
            if self._player:
                self._player.set_time(self._player.get_time() + 5000)
        elif event.key() == Qt.Key_Up:
            self._set_volume(min(100, self._volume + 5))
            self.volume_slider.setValue(self._volume)
        elif event.key() == Qt.Key_Down:
            self._set_volume(max(0, self._volume - 5))
            self.volume_slider.setValue(self._volume)
        elif event.key() == Qt.Key_F:
            self._toggle_fullscreen()
        elif event.key() == Qt.Key_M:
            self.toggle_mute()
        else:
            super().keyPressEvent(event)


# ---------- 音频可视化占位 ----------
class AudioPlayer(VideoPlayer):
    """音频播放器复用VideoPlayer，显示音频可视化占位"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_frame.setStyleSheet("background-color: #1a1a2e;")
        # 添加音频图标
        self.audio_label = QLabel("🎵\n音频播放中", self.video_frame)
        self.audio_label.setAlignment(Qt.AlignCenter)
        self.audio_label.setStyleSheet("color: #4a90d9; font-size: 48px;")
        layout = QVBoxLayout(self.video_frame)
        layout.addWidget(self.audio_label)


# ---------- 主窗口 ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("MainWindow初始化开始")
        self.setWindowTitle("万能媒体浏览器")
        self.setMinimumSize(900, 600)
        self.resize(1200, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QDockWidget { color: #ddd; titlebar-close-icon: none; }
            QDockWidget::title { background-color: #2d2d2d; padding: 6px; color: #ddd; }
            QTreeView { background-color: #252525; color: #ddd; border: none;
                        outline: none; }
            QTreeView::item:selected { background-color: #4a90d9; color: white; }
            QToolBar { background-color: #2d2d2d; border: none; spacing: 4px; padding: 4px; }
            QToolButton { background-color: transparent; border: none; padding: 6px;
                          color: #ddd; border-radius: 4px; }
            QToolButton:hover { background-color: #3d3d3d; }
            QStatusBar { background-color: #2d2d2d; color: #aaa; }
            QLabel { color: #ddd; }
        """)

        self._current_folder = None
        self._current_file = None
        self._file_list = []
        self._current_index = -1

        try:
            self._setup_ui()
            logging.info("UI设置完成")
        except Exception as e:
            log_except("UI设置失败")
            raise

        try:
            self._setup_toolbar()
            logging.info("工具栏设置完成")
        except Exception as e:
            log_except("工具栏设置失败")

        try:
            self._setup_statusbar()
            logging.info("状态栏设置完成")
        except Exception as e:
            log_except("状态栏设置失败")

        # 接受拖放
        self.setAcceptDrops(True)
        logging.info("MainWindow初始化完成")

    def _setup_ui(self):
        # 中央堆叠区域
        self.stack = QStackedWidget()

        # 图片查看器
        self.image_viewer = ImageViewer()
        self.stack.addWidget(self.image_viewer)

        # 视频播放器
        self.video_player = VideoPlayer()
        self.stack.addWidget(self.video_player)

        # 音频播放器
        self.audio_player = AudioPlayer()
        self.stack.addWidget(self.audio_player)

        # 欢迎页
        welcome = QWidget()
        welcome.setStyleSheet("background-color: #1e1e1e;")
        wl = QVBoxLayout(welcome)
        wl.setAlignment(Qt.AlignCenter)
        wl.setSpacing(15)
        icon_label = QLabel("🖼️  🎬")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px;")
        title_label = QLabel("万能媒体浏览器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 28px; color: #ddd; font-weight: bold;")
        desc_label = QLabel(
            "从左侧「文件浏览器」选择文件夹和文件\n"
            "或点击上方工具栏「打开文件夹」/「打开文件」\n"
            "也可以直接把文件或文件夹拖放到此窗口\n\n"
            "快捷键: 空格=播放/暂停  ←→=上/下一个  F=全屏  R=旋转"
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 14px; color: #888; line-height: 1.8;")
        wl.addWidget(icon_label)
        wl.addWidget(title_label)
        wl.addWidget(desc_label)
        self.stack.addWidget(welcome)
        self.stack.setCurrentWidget(welcome)

        self.setCentralWidget(self.stack)

        # 左侧文件浏览器
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")

        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        # 不设置rootIndex，默认显示"此电脑"（所有驱动器）
        self.file_tree.setHeaderHidden(True)
        for i in range(1, 4):
            self.file_tree.hideColumn(i)
        self.file_tree.setIndentation(15)
        self.file_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_tree.setAnimated(True)
        self.file_tree.setExpandsOnDoubleClick(True)
        # 单击：文件夹展开，文件预览
        self.file_tree.clicked.connect(self._on_file_clicked)
        # 双击：文件打开
        self.file_tree.doubleClicked.connect(self._on_file_selected)

        dock = QDockWidget("文件浏览器", self)
        dock.setWidget(self.file_tree)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self._file_dock = dock

        # 底部缩略图列表
        self.thumb_list = QListView()
        self.thumb_list.setViewMode(QListView.IconMode)
        self.thumb_list.setIconSize(QSize(96, 72))
        self.thumb_list.setResizeMode(QListView.Adjust)
        self.thumb_list.setMovement(QListView.Static)
        self.thumb_list.setSpacing(6)
        self.thumb_list.setWrapping(True)
        self.thumb_list.setFlow(QListView.LeftToRight)
        self.thumb_list.setFixedHeight(110)
        self.thumb_list.setStyleSheet("background-color: #252525; border: none;")
        self.thumb_model = QStandardItemModel()
        self.thumb_list.setModel(self.thumb_model)
        self.thumb_list.doubleClicked.connect(self._on_thumb_selected)

        thumb_dock = QDockWidget("媒体列表", self)
        thumb_dock.setWidget(self.thumb_list)
        thumb_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        thumb_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, thumb_dock)
        self._thumb_dock = thumb_dock

    def _setup_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # 向上
        act_up = QAction("⬆ 上级", self)
        act_up.triggered.connect(self._go_up)
        toolbar.addAction(act_up)

        toolbar.addSeparator()

        # 打开文件夹
        act_open_folder = QAction("📁 打开文件夹", self)
        act_open_folder.triggered.connect(self._open_folder)
        toolbar.addAction(act_open_folder)

        # 打开文件
        act_open_file = QAction("📄 打开文件", self)
        act_open_file.triggered.connect(self._open_file)
        toolbar.addAction(act_open_file)

        toolbar.addSeparator()

        # 常用位置
        for name, path in [("🖥 桌面", os.path.join(os.path.expanduser("~"), "Desktop")),
                           ("📷 图片", os.path.join(os.path.expanduser("~"), "Pictures")),
                           ("🎬 视频", os.path.join(os.path.expanduser("~"), "Videos")),
                           ("📥 下载", os.path.join(os.path.expanduser("~"), "Downloads"))]:
            if os.path.isdir(path):
                act = QAction(name, self)
                act.triggered.connect(lambda checked, p=path: self._load_folder(p))
                toolbar.addAction(act)

        toolbar.addSeparator()

        # 上一个
        act_prev = QAction("◀ 上一个", self)
        act_prev.setShortcut(QKeySequence(Qt.Key_Left))
        act_prev.triggered.connect(self._prev_file)
        toolbar.addAction(act_prev)

        # 下一个
        act_next = QAction("下一个 ▶", self)
        act_next.setShortcut(QKeySequence(Qt.Key_Right))
        act_next.triggered.connect(self._next_file)
        toolbar.addAction(act_next)

        toolbar.addSeparator()

        # 旋转
        act_rotate = QAction("🔄 旋转", self)
        act_rotate.setShortcut(QKeySequence(Qt.Key_R))
        act_rotate.triggered.connect(lambda: self.image_viewer.rotate(90))
        toolbar.addAction(act_rotate)

        # 适应窗口
        act_fit = QAction("🔍 适应窗口", self)
        act_fit.setShortcut(QKeySequence(Qt.Key_0))
        act_fit.triggered.connect(self.image_viewer.reset_zoom)
        toolbar.addAction(act_fit)

        # 原始大小
        act_original = QAction("1:1 原始大小", self)
        act_original.triggered.connect(self.image_viewer.original_size)
        toolbar.addAction(act_original)

        toolbar.addSeparator()

        # 全屏
        act_fullscreen = QAction("⛶ 全屏", self)
        act_fullscreen.setShortcut(QKeySequence(Qt.Key_F))
        act_fullscreen.triggered.connect(self._toggle_fullscreen)
        toolbar.addAction(act_fullscreen)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.file_info_label = QLabel("未打开文件")
        self.status.addWidget(self.file_info_label, 1)
        self.format_label = QLabel("")
        self.status.addPermanentWidget(self.format_label)

        if not VLC_AVAILABLE:
            self.status.showMessage("⚠️ 未检测到VLC运行时，视频播放可能不可用。请安装VLC播放器或将vlc目录放在程序同目录下。", 10000)

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")
        if folder:
            self._load_folder(folder)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开媒体文件", "",
            "所有媒体文件 (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff *.mp4 *.avi *.mkv *.mov *.flv *.wmv *.rmvb *.mp3 *.wav *.flac);;所有文件 (*.*)"
        )
        if path:
            self._open_media(path)

    def _load_folder(self, folder):
        self._current_folder = folder
        # 在文件树中定位并展开该文件夹
        idx = self.file_model.index(folder)
        if idx.isValid():
            self.file_tree.setRootIndex(idx)
            self.file_tree.expand(idx)
        # 收集文件夹中的媒体文件（仅当前目录，不递归）
        self._file_list = []
        try:
            for f in sorted(os.listdir(folder)):
                full = os.path.join(folder, f)
                if os.path.isfile(full) and is_media(f):
                    self._file_list.append(full)
        except Exception:
            pass
        self._update_thumbnails()
        self.status.showMessage(f"已加载: {folder}  ({len(self._file_list)} 个媒体文件)", 5000)

    def _go_up(self):
        """返回上一级目录"""
        if self._current_folder:
            parent = os.path.dirname(self._current_folder)
            if parent and parent != self._current_folder:
                self._load_folder(parent)
            else:
                # 已经是根目录，回到"此电脑"视图
                self.file_tree.setRootIndex(self.file_model.index(""))
                self._current_folder = None
                self._file_list = []
                self._update_thumbnails()

    def _update_thumbnails(self):
        self.thumb_model.clear()
        for path in self._file_list:
            name = os.path.basename(path)
            item = QStandardItem(name)
            item.setData(path, Qt.UserRole)
            # 尝试生成缩略图
            if is_image(path):
                try:
                    pix, _ = load_image_to_pixmap(path)
                    if pix and not pix.isNull():
                        pix = pix.scaled(96, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(pix))
                except Exception:
                    pass
            self.thumb_model.appendRow(item)

    def _on_file_selected(self, index):
        path = self.file_model.filePath(index)
        if os.path.isfile(path):
            if is_media(path):
                self._open_media(path)
            else:
                self.status.showMessage(f"不支持的文件格式: {os.path.splitext(path)[1]}", 3000)
        elif os.path.isdir(path):
            self._load_folder(path)

    def _on_file_clicked(self, index):
        path = self.file_model.filePath(index)
        if os.path.isdir(path):
            # 单击文件夹：展开/进入
            if self.file_tree.isExpanded(index):
                self.file_tree.collapse(index)
            else:
                self.file_tree.expand(index)
        elif os.path.isfile(path) and is_media(path):
            # 单击媒体文件：直接预览
            self._open_media(path)

    def _on_thumb_selected(self, index):
        path = index.data(Qt.UserRole)
        if path:
            self._open_media(path)

    def _open_media(self, path):
        logging.info(f"_open_media: {path}")
        logging.info(f"  is_image={is_image(path)}, is_video={is_video(path)}, is_audio={is_audio(path)}")
        # 停止之前的视频
        self.video_player.stop()
        self.audio_player.stop()

        self._current_file = path
        if path in self._file_list:
            self._current_index = self._file_list.index(path)

        if is_image(path):
            self.stack.setCurrentWidget(self.image_viewer)
            ok, error = self.image_viewer.load_image(path)
            if not ok:
                ext = os.path.splitext(path)[1].upper()
                QMessageBox.warning(
                    self, "无法加载图片",
                    f"文件: {os.path.basename(path)}\n"
                    f"格式: {ext}\n"
                    f"错误: {error or '未知错误'}\n\n"
                    f"提示: 单反RAW格式(CR2/NEF/ARW/DNG等)需要rawpy解码库支持。"
                )
        elif is_video(path):
            if not VLC_AVAILABLE:
                QMessageBox.warning(self, "VLC未安装", "视频播放需要VLC运行时。\n请安装VLC播放器，或将vlc目录复制到程序同目录下。")
                return
            self.stack.setCurrentWidget(self.video_player)
            ok = self.video_player.load_video(path)
            if not ok:
                QMessageBox.warning(self, "错误", f"无法加载视频:\n{path}")
        elif is_audio(path):
            if not VLC_AVAILABLE:
                QMessageBox.warning(self, "VLC未安装", "音频播放需要VLC运行时。")
                return
            self.stack.setCurrentWidget(self.audio_player)
            ok = self.audio_player.load_video(path)
            if not ok:
                QMessageBox.warning(self, "错误", f"无法加载音频:\n{path}")

        # 更新状态栏
        size = os.path.getsize(path)
        size_str = self._format_size(size)
        ext = os.path.splitext(path)[1].upper()
        self.file_info_label.setText(f"{os.path.basename(path)}  |  {size_str}  |  {ext}")
        self.format_label.setText(f"文件 {self._current_index + 1}/{len(self._file_list)}" if self._file_list else "")

        # 在文件树中选中
        idx = self.file_model.index(path)
        if idx.isValid():
            self.file_tree.setCurrentIndex(idx)

    def _prev_file(self):
        if not self._file_list or self._current_index <= 0:
            return
        self._current_index -= 1
        self._open_media(self._file_list[self._current_index])

    def _next_file(self):
        if not self._file_list or self._current_index >= len(self._file_list) - 1:
            return
        self._current_index += 1
        self._open_media(self._file_list[self._current_index])

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self._file_dock.show()
            self._thumb_dock.show()
        else:
            self.showFullScreen()
            self._file_dock.hide()
            self._thumb_dock.hide()

    @staticmethod
    def _format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    # 拖放支持
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isdir(path):
                self._load_folder(path)
            elif os.path.isfile(path) and is_media(path):
                self._open_media(path)
            break

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self._toggle_fullscreen()
        elif event.key() == Qt.Key_Space:
            # 空格在视频/音频时播放暂停
            if self.stack.currentWidget() in (self.video_player, self.audio_player):
                if self.stack.currentWidget() == self.video_player:
                    self.video_player.toggle_play()
                else:
                    self.audio_player.toggle_play()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.video_player.stop()
        self.audio_player.stop()
        event.accept()


def main():
    logging.info("进入main()函数")
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("万能媒体浏览器")
    app.setOrganizationName("MediaBrowser")
    logging.info("QApplication创建完成")

    try:
        window = MainWindow()
        window.show()
        logging.info("主窗口显示完成")
    except Exception as e:
        log_except("主窗口创建失败")
        # 显示错误对话框
        try:
            QMessageBox.critical(None, "启动失败",
                f"程序启动时发生错误:\n{e}\n\n详细日志已保存到:\n{LOG_FILE}")
        except Exception:
            pass
        sys.exit(1)

    # 如果有命令行参数，直接打开
    if len(sys.argv) > 1:
        try:
            path = sys.argv[1]
            logging.info(f"命令行参数: {path}")
            if os.path.isdir(path):
                window._load_folder(path)
            elif os.path.isfile(path):
                window._open_media(path)
        except Exception as e:
            log_except("打开命令行文件失败")

    logging.info("进入事件循环")
    ret = app.exec()
    logging.info(f"事件循环退出，返回码: {ret}")
    sys.exit(ret)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_except("程序未捕获异常")
        sys.exit(1)
