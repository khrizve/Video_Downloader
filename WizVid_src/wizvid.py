import sys
import re
import yt_dlp
import os
import urllib.request
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog,
    QProgressBar, QComboBox, QGraphicsOpacityEffect, QHBoxLayout, QDialog
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QUrl, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QDesktopServices


# ==================== THREAD WORKERS ====================
class DownloadWorker(QObject):
    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, urls, options):
        super().__init__()
        self.urls = urls
        self.options = options

    def run(self):
        try:
            # Add our progress hook to the options
            self.options['progress_hooks'] = [self.progress_hook]
            with yt_dlp.YoutubeDL(self.options) as ydl:
                ydl.download(self.urls)
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))

    def progress_hook(self, d):
        self.progress_signal.emit(d)


class PreviewWorker(QObject):
    preview_ready = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'socket_timeout': 10}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                # Download thumbnail in thread
                thumbnail_url = info.get('thumbnail', '')
                if thumbnail_url:
                    with urllib.request.urlopen(thumbnail_url) as response:
                        info['thumbnail_data'] = response.read()
                self.preview_ready.emit(info)
        except Exception as e:
            self.error_signal.emit(str(e))


# ==================== PREVIEW DIALOG ====================
class VideoPreviewDialog(QDialog):
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self.setWindowTitle("✨ Video Preview ✨")
        self.setGeometry(300, 100, 650, 500)
        self.setStyleSheet(self.fantasy_style_preview())
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel(info.get('title', 'No title available'))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; color: #ffd700;")
        layout.addWidget(self.title_label)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label)
        
        duration = info.get('duration', 0)
        minutes, seconds = divmod(duration, 60)
        self.duration_label = QLabel(f"⏱️ Duration: {minutes}:{seconds:02d}")
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.duration_label)
        
        self.view_button = QPushButton("🌐 View on YouTube")
        self.view_button.clicked.connect(self.open_in_browser)
        layout.addWidget(self.view_button)
        
        self.close_button = QPushButton("🔮 Close Preview")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
        
        self.setLayout(layout)
        
        # Load thumbnail if available
        if 'thumbnail_data' in info:
            pixmap = QPixmap()
            pixmap.loadFromData(info['thumbnail_data'])
            self.thumbnail_label.setPixmap(pixmap.scaled(400, 225, Qt.AspectRatioMode.KeepAspectRatio))
    
    def fantasy_style_preview(self):
        return """
            QDialog {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #0a0f14, stop:1 #1a2233); /* Deep Midnight Ice */
                color: #a9cfe7; /* Moonlit Silver */
                font-family: 'Garamond';
            }
            QLabel {
                color: #b8d0ff;  /* Frosted Sorcery Blue */
                font-weight: bold; 
                font-size: 16px;
                margin: 10px;
            }
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #1e2d44, stop:1 #0c1829); /* Arcane Ocean Depths */
                border: 2px solid #5b93c6; /* Ancient Steel Blue */
                color: #f0f8ff; /* Ghost White */
                font-weight: bold;
                padding: 10px;
                border-radius: 15px;
                font-size: 16px;
                margin: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #2f4f6a, stop:1 #19334d); /* Frozen Depth Glint */
                color: #e0f7ff; /* Mystic Frost */
                border: 2px solid #6cb2e2; /* Crystal Sky */
            }
        """



    
    def open_in_browser(self):
        QDesktopServices.openUrl(QUrl(self.info['webpage_url']))


# ==================== MAIN APPLICATION ====================
class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.download_path = "."
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.init_ui()
        self.download_thread = None
        self.preview_thread = None

    def get_ffmpeg_path(self):
        if sys.platform == "win32":
            return os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffmpeg.exe")
        elif sys.platform == "darwin":
            return os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffmpeg")
        else:
            return os.path.join(os.path.dirname(__file__), "ffmpeg", "bin", "ffmpeg")

    def init_ui(self):
        self.setWindowTitle("✨ WizVid - Fantasy Downloader ✨")
        self.setGeometry(300, 100, 650, 500)
        self.setStyleSheet(self.fantasy_style())

        layout = QVBoxLayout()

        # Header with animation
        self.title_label = QLabel("✨ WizVid - Fantasy Downloader ✨")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 30px; color: #ffd700; font-weight: bold;")
        layout.addWidget(self.title_label)
        self.setup_fade_effect(self.title_label)

        # URL Input
        self.label = QLabel("Enter Video URLs (one per line):")
        layout.addWidget(self.label)

        self.url_input = QTextEdit(self)
        layout.addWidget(self.url_input)

        # Download Path Selection
        self.path_label = QLabel("Select Download Folder:")
        layout.addWidget(self.path_label)

        self.path_button = QPushButton("📂 Browse")
        self.path_button.clicked.connect(self.select_folder)
        layout.addWidget(self.path_button)

        # Format Selection
        self.format_label = QLabel("Select Format:")
        layout.addWidget(self.format_label)

        self.format_dropdown = QComboBox(self)
        self.format_dropdown.addItems([
            "Best Video", "Best Audio", "MP4 720p", "MP4 1080p", "MP4 1440p", "MP4 4K", 
            "MP3"
        ])
        layout.addWidget(self.format_dropdown)

        # Action Buttons
        button_container = QHBoxLayout()
        
        self.download_button = QPushButton("🌟 Download Videos")
        self.download_button.clicked.connect(self.start_download)
        button_container.addWidget(self.download_button)
        
        self.preview_button = QPushButton("🔮 Preview Video")
        self.preview_button.clicked.connect(self.preview_video)
        button_container.addWidget(self.preview_button)
        
        layout.addLayout(button_container)

        # Progress Display
        self.speed_label = QLabel("⚡ Speed: N/A")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speed_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffd700;")
        layout.addWidget(self.speed_label)

        self.progress = QProgressBar(self)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Status Log
        self.status = QTextEdit(self)
        self.status.setReadOnly(True)
        layout.addWidget(self.status)

        # Footer
        self.footer_label = QLabel('<p align="center" style="font-size:14px;">'
                                 'Created by <a href="https://rizve.netlify.app/" '
                                 'style="color:#ffd700; text-decoration:none;">Code Sorcerer</a>'
                                 '</p>')
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setOpenExternalLinks(True)
        layout.addWidget(self.footer_label)

        self.setLayout(layout)

    def fantasy_style(self):
        return """
            QWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #0a0f1f, stop:1 #121a2e); /* Deep Twilight Blue */
                color: #a9cfe7; /* Moonlit Silver */
                font-family: 'Garamond';
                font-size: 14px;
            }
            QLabel {
                color: #cfdff9;  /* Frosted Ice Blue */
                font-weight: bold;
                font-size: 16px;
            }
            QLineEdit, QTextEdit {
                background-color: rgba(255, 255, 255, 0.05); /* Misty Veil */
                border: 2px solid #3b6e91; /* Arcane Azure */
                color: #dceeff;
                padding: 5px;
                border-radius: 8px;
                font-weight: bold;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.05); /* Misty Veil */
                border: 2px solid #3f7da9; /* Storm Sapphire */
                color: #dceeff;
                padding: 5px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #1b2a49, stop:1 #243b55); /* Shadow Blue Gradient */
                border: 2px solid #5b93c6; /* Ancient Steel Blue */
                color: #ffffff;
                font-weight: bold;
                padding: 12px;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #2c3e5d, stop:1 #3c5e80); /* Frozen Depths */
                color: #e0f7ff; /* Mystic Frost */
                border: 2px solid #6cb2e2; /* Crystal Sky */
            }
            QPushButton:pressed {
                background: #182538; /* Abyssal Ice */
                color: #8ecae6; /* Glacial Highlight */
            }
        """



    def setup_fade_effect(self, widget):
        self.opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(3000)
        self.fade_animation.setStartValue(0.3)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.setDirection(QPropertyAnimation.Direction.Forward)
        self.fade_animation.finished.connect(self.reverse_fade)
        self.fade_animation.start()

    def reverse_fade(self):
        if self.fade_animation.direction() == QPropertyAnimation.Direction.Forward:
            self.fade_animation.setDirection(QPropertyAnimation.Direction.Backward)
        else:
            self.fade_animation.setDirection(QPropertyAnimation.Direction.Forward)
        self.fade_animation.start()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.download_path = folder
            self.path_label.setText(f"Selected Folder: {folder}")
        else:
            self.download_path = "."

    def preview_video(self):
        url = self.url_input.toPlainText().strip().split("\n")[0]
        if not url:
            self.status.append("⚠️ Please enter a video URL first!")
            return
        
        self.preview_button.setEnabled(False)
        self.status.append("🔮 Gathering video info...")
        
        # Create thread and worker
        self.preview_thread = QThread()
        self.preview_worker = PreviewWorker(url)
        self.preview_worker.moveToThread(self.preview_thread)
        
        # Connect signals
        self.preview_thread.started.connect(self.preview_worker.run)
        self.preview_worker.preview_ready.connect(self.show_preview)
        self.preview_worker.error_signal.connect(self.preview_error)
        self.preview_worker.preview_ready.connect(self.preview_thread.quit)
        self.preview_worker.error_signal.connect(self.preview_thread.quit)
        self.preview_thread.finished.connect(self.preview_thread.deleteLater)
        
        self.preview_thread.start()

    def show_preview(self, info):
        self.preview_button.setEnabled(True)
        self.preview_dialog = VideoPreviewDialog(info, self)
        self.preview_dialog.exec()

    def preview_error(self, error):
        self.preview_button.setEnabled(True)
        self.status.append(f"❌ Preview error: {error}")

    def remove_ansi_codes(self, text):
        return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

    def update_progress(self, d):
        if d['status'] == 'downloading':
            percent_str = self.remove_ansi_codes(d.get('_percent_str', '0.0%'))
            percent = float(percent_str.replace('%', '').strip())
            speed_str = self.remove_ansi_codes(d.get('_speed_str', 'N/A'))
            self.progress.setValue(int(percent))
            self.speed_label.setText(f"⚡ Speed: {speed_str}/s")
            self.status.append(f"💾 Downloading... {percent:.2f}%")
            QApplication.processEvents()
        elif d['status'] == 'finished':
            self.status.append("✅ Download completed!")
            self.progress.setValue(100)
            self.speed_label.setText("✅ Speed: Download Finished")

    def start_download(self):
        urls = [url for url in self.url_input.toPlainText().strip().split("\n") if url]
        if not urls:
            self.status.append("⚠️ Please enter at least one video URL!")
            return

        self.status.append("⏳ Preparing download (this may take a moment)...")
        self.download_button.setEnabled(False)
        self.progress.setValue(0)
        
        format_map = {
            "Best Video": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "Best Audio": "bestaudio[ext=m4a]/bestaudio",
            "MP4 720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "MP4 1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "MP4 1440p": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440][ext=mp4]",
            "MP4 4K": "bestvideo[height>=2160][ext=mp4]+bestaudio[ext=m4a]/best[height>=2160][ext=mp4]",
            "MP3": "bestaudio[ext=mp3]/bestaudio"
        }

        options = {
            'outtmpl': f"{self.download_path}/%(title)s.%(ext)s",
            'format': format_map[self.format_dropdown.currentText()],
            'nocolor': True,
            'ffmpeg_location': self.ffmpeg_path,
            'socket_timeout': 30
        }
        
        # Create thread and worker
        self.download_thread = QThread()
        self.download_worker = DownloadWorker(urls, options)
        self.download_worker.moveToThread(self.download_thread)
        
        # Connect signals
        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.progress_signal.connect(self.update_progress)
        self.download_worker.finished_signal.connect(self.download_finished)
        self.download_worker.error_signal.connect(self.download_error)
        self.download_worker.finished_signal.connect(self.download_thread.quit)
        self.download_worker.error_signal.connect(self.download_thread.quit)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        
        self.download_thread.start()

    def download_finished(self):
        self.download_button.setEnabled(True)
        self.status.append("✅ All downloads completed!")
        self.progress.setValue(100)

    def download_error(self, error):
        self.download_button.setEnabled(True)
        self.status.append(f"❌ Download error: {error}")
        self.progress.setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoDownloader()
    window.show()
    sys.exit(app.exec())
    
