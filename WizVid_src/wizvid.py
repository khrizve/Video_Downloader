import sys
import re
import yt_dlp
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog,
    QProgressBar, QComboBox, QGraphicsOpacityEffect
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt


class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.download_path = "."
        self.ffmpeg_path = self.get_ffmpeg_path()
        self.init_ui()

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

        self.title_label = QLabel("✨ WizVid - Fantasy Downloader ✨")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 30px; color: #ffd700; font-weight: bold;")
        layout.addWidget(self.title_label)
        self.setup_fade_effect(self.title_label)

        self.label = QLabel("Enter Video URLs (one per line):")
        layout.addWidget(self.label)

        self.url_input = QTextEdit(self)
        layout.addWidget(self.url_input)

        self.path_label = QLabel("Select Download Folder:")
        layout.addWidget(self.path_label)

        self.path_button = QPushButton("📂 Browse")
        self.path_button.clicked.connect(self.select_folder)
        layout.addWidget(self.path_button)

        self.format_label = QLabel("Select Format:")
        layout.addWidget(self.format_label)

        self.format_dropdown = QComboBox(self)
        self.format_dropdown.addItems([
            "Best Video", "Best Audio", "MP4 720p", "MP4 1080p", "MP4 1440p", "MP4 4K", "MP3"
        ])
        layout.addWidget(self.format_dropdown)

        self.speed_label = QLabel("⚡ Speed: N/A")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speed_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffd700;")
        layout.addWidget(self.speed_label)

        self.download_button = QPushButton("🌟 Download Videos")
        self.download_button.clicked.connect(self.download_videos)
        layout.addWidget(self.download_button)

        self.progress = QProgressBar(self)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.status = QTextEdit(self)
        self.status.setReadOnly(True)
        layout.addWidget(self.status)

        self.footer_label = QLabel('<p align="center" style="font-size:14px;">'
                                   'Created by <a href="https://rizve.netlify.app/" '
                                   'style="color:#ffd700; text-decoration:none;">Rizve Reza</a>'
                                   '</p>')
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setOpenExternalLinks(True)
        layout.addWidget(self.footer_label)

        self.setLayout(layout)

    def fantasy_style(self):
        return """
            QWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #4b0082, stop:1 #8a2be2);
                color: #ffd700;
                font-family: 'Garamond';
                font-size: 14px;
            }
            QLabel {
                color: #fff8dc;
                font-weight: bold;
                font-size: 16px;
            }
            QLineEdit, QTextEdit {
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid #d8bfd8;
                color: #fff8dc;
                padding: 5px;
                border-radius: 8px;
                font-weight: bold;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid #ffccff;
                color: #fff8dc;
                padding: 5px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #a46cd3, stop:1 #6a1b9a);
                border: 2px solid #ffd700;
                color: #ffffff;
                font-weight: bold;
                padding: 12px;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #c084fc, stop:1 #8e24aa);
                color: #fff3cd;
                border: 2px solid #ffccff;
            }
            QPushButton:pressed {
                background: #6a1b9a;
                color: #ffd700;
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

    def remove_ansi_codes(self, text):
        return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)

    def progress_hook(self, d):
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

    def download_videos(self):
        urls = self.url_input.toPlainText().strip().split("\n")
        if not urls:
            self.status.append("⚠️ Please enter at least one video URL!")
            return

        self.status.append("⏳ Starting batch download...")
        self.progress.setValue(0)
        QApplication.processEvents()

        format_map = {
            "Best Video": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "Best Audio": "bestaudio[ext=m4a]/bestaudio",
            "MP4 720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "MP4 1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "MP4 1440p": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440][ext=mp4]",
            "MP4 4K": "bestvideo[height>=2160][ext=mp4]+bestaudio[ext=m4a]/best[height>=2160][ext=mp4]",
            "MP3": "bestaudio[ext=mp3]/bestaudio"
        }

        selected_format = format_map[self.format_dropdown.currentText()]

        options = {
            'outtmpl': f"{self.download_path}/%(title)s.%(ext)s",
            'format': selected_format,
            'progress_hooks': [self.progress_hook],
            'nocolor': True,
            'ffmpeg_location': self.ffmpeg_path
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download(urls)
        except Exception as e:
            self.status.append(f"❌ Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoDownloader()
    window.show()
    sys.exit(app.exec())