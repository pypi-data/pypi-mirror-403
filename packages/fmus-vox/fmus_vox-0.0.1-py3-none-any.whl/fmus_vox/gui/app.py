"""
fmus_vox.gui.app - GUI application for the FMUS-VOX library.

This module provides a PyQt6-based GUI application for interacting with
the FMUS-VOX library components.
"""

import os
import sys
import time
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

# Add parent directory to Python path so fmus_vox package can be imported
parent_dir = str(Path(__file__).resolve().parents[2])
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QComboBox, QSlider, QProgressBar,
        QGroupBox, QFrame, QFileDialog, QMessageBox, QTabWidget
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
    from PyQt6.QtGui import QIcon, QPainter, QColor, QPen
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from fmus_vox.core.audio import Audio
from fmus_vox.stream.microphone import Microphone
from fmus_vox.stream.audioplayer import AudioPlayer


class MissingDependencyError(Exception):
    """Error raised when a required dependency is missing."""
    pass


class AudioLevelWidget(QWidget):
    """Widget for displaying audio level meters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 30)
        self.rms_level = 0.0
        self.peak_level = 0.0
        self.setToolTip("Audio level meter - RMS (green) and peak (red)")

    def update_levels(self, levels: Dict[str, float]):
        """Update audio levels."""
        self.rms_level = levels.get("rms", 0.0)
        self.peak_level = levels.get("peak", 0.0)
        self.update()

    def paintEvent(self, event):
        """Draw the level meter."""
        painter = QPainter(self)
        width = self.width()
        height = self.height()

        # Draw background
        painter.fillRect(0, 0, width, height, QColor(40, 40, 40))

        # Draw RMS level
        rms_width = int(self.rms_level * width)
        rms_color = QColor(0, 200, 0)  # Green
        painter.fillRect(0, 0, rms_width, height, rms_color)

        # Draw peak level
        peak_width = int(self.peak_level * width)
        peak_color = QColor(200, 0, 0)  # Red
        peak_height = height // 4
        painter.fillRect(0, (height - peak_height) // 2, peak_width, peak_height, peak_color)

        # Draw level markers
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        for i in range(1, 10):
            x = int(width * i / 10)
            painter.drawLine(x, 0, x, height)


class RecorderTab(QWidget):
    """Tab for recording audio from microphone."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Audio components
        self.microphone: Optional[Microphone] = None
        self.recording: Optional[Audio] = None
        self.is_recording = False

        # Set up UI
        self.init_ui()

        # Initialize microphone
        self.initialize_microphone()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Device selection
        device_group = QGroupBox("Microphone Device")
        device_layout = QVBoxLayout(device_group)

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("Select microphone device")
        device_layout.addWidget(self.device_combo)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.populate_devices)
        device_layout.addWidget(refresh_btn)

        layout.addWidget(device_group)

        # Audio level meter
        level_group = QGroupBox("Audio Level")
        level_layout = QVBoxLayout(level_group)

        self.level_meter = AudioLevelWidget()
        level_layout.addWidget(self.level_meter)

        # Audio level timer
        self.level_timer = QTimer()
        self.level_timer.setInterval(50)  # 50ms update rate
        self.level_timer.timeout.connect(self.update_audio_level)

        layout.addWidget(level_group)

        # Recording controls
        controls_group = QGroupBox("Recording Controls")
        controls_layout = QHBoxLayout(controls_group)

        self.record_btn = QPushButton("Start Recording")
        self.record_btn.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_btn)

        self.save_btn = QPushButton("Save Recording")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_recording)
        controls_layout.addWidget(self.save_btn)

        layout.addWidget(controls_group)

        # Recording status
        status_group = QGroupBox("Recording Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)

        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        status_layout.addWidget(self.timer_label)

        layout.addWidget(status_group)

        # Add spacer
        layout.addStretch(1)

    def initialize_microphone(self):
        """Initialize the microphone."""
        try:
            # Populate device list
            self.populate_devices()

            # Get default device
            default_device = Microphone.get_default_device()
            device_index = default_device["index"] if default_device else None

            # Create microphone
            self.microphone = Microphone(
                device_index=device_index,
                sample_rate=16000,
                channels=1,
                format="float32"
            )

            # Set up visualization callback
            self.microphone.set_visualization_callback(self.on_audio_level)

            # Start the audio level timer
            self.level_timer.start()

            self.status_label.setText("Microphone initialized")

        except Exception as e:
            self.status_label.setText(f"Error initializing microphone: {str(e)}")
            QMessageBox.critical(
                self,
                "Microphone Error",
                f"Could not initialize microphone: {str(e)}"
            )

    def populate_devices(self):
        """Populate the device selection combo box."""
        self.device_combo.clear()

        try:
            devices = Microphone.list_devices()

            for i, device in enumerate(devices):
                name = device.get("name", f"Device {i}")
                is_default = device.get("default", False)

                if is_default:
                    name += " (Default)"

                self.device_combo.addItem(name, device.get("index"))

            self.device_combo.currentIndexChanged.connect(self.on_device_changed)

            if not devices:
                self.device_combo.addItem("No devices found")

        except Exception as e:
            self.device_combo.addItem(f"Error listing devices: {str(e)}")

    def on_device_changed(self, index):
        """Handle device selection changes."""
        if self.is_recording:
            return

        try:
            # Get device index
            device_index = self.device_combo.currentData()

            # Close existing microphone
            if self.microphone:
                self.microphone.close()

            # Create new microphone with selected device
            self.microphone = Microphone(
                device_index=device_index,
                sample_rate=16000,
                channels=1,
                format="float32"
            )

            # Set up visualization callback
            self.microphone.set_visualization_callback(self.on_audio_level)

            self.status_label.setText(f"Switched to device: {self.device_combo.currentText()}")

        except Exception as e:
            self.status_label.setText(f"Error changing device: {str(e)}")

    def toggle_recording(self):
        """Toggle recording state."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording audio."""
        if not self.microphone:
            self.status_label.setText("No microphone available")
            return

        try:
            # Start recording
            self.microphone.start_recording()
            self.is_recording = True

            # Update UI
            self.record_btn.setText("Stop Recording")
            self.save_btn.setEnabled(False)
            self.status_label.setText("Recording...")

            # Reset timer
            self.start_time = time.time()

            # Start timer for updating recording time
            self.update_timer()

        except Exception as e:
            self.status_label.setText(f"Error starting recording: {str(e)}")

    def stop_recording(self):
        """Stop recording audio."""
        if not self.microphone or not self.is_recording:
            return

        try:
            # Stop recording and get audio
            self.recording = self.microphone.stop_recording()
            self.is_recording = False

            # Update UI
            self.record_btn.setText("Start Recording")
            self.save_btn.setEnabled(True)
            self.status_label.setText(
                f"Recording stopped: {len(self.recording.data)} samples "
                f"({self.recording.duration:.2f} seconds)"
            )

        except Exception as e:
            self.status_label.setText(f"Error stopping recording: {str(e)}")

    def update_timer(self):
        """Update the recording timer display."""
        if not self.is_recording:
            return

        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        # Update timer label
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

        # Schedule next update
        QTimer.singleShot(1000, self.update_timer)

    def update_audio_level(self):
        """Update the audio level meter."""
        if not self.microphone:
            return

        # Ensure microphone is reading audio for visualization
        if not self.is_recording:
            # Read a small chunk to update visualization
            self.microphone.read(512)

    def on_audio_level(self, levels):
        """Handle audio level updates."""
        self.level_meter.update_levels(levels)

    def save_recording(self):
        """Save the recording to a file."""
        if not self.recording:
            return

        try:
            # Get save file name
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Recording",
                os.path.expanduser("~/recording.wav"),
                "WAV Files (*.wav);;All Files (*)"
            )

            if not file_path:
                return

            # Save the recording
            self.recording.save(file_path)

            self.status_label.setText(f"Recording saved to: {file_path}")

        except Exception as e:
            self.status_label.setText(f"Error saving recording: {str(e)}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save recording: {str(e)}"
            )


class PlayerTab(QWidget):
    """Tab for playing audio files."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Audio components
        self.player: Optional[AudioPlayer] = None
        self.current_file: Optional[str] = None

        # Set up UI
        self.init_ui()

        # Initialize player
        self.initialize_player()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Device selection
        device_group = QGroupBox("Output Device")
        device_layout = QVBoxLayout(device_group)

        self.device_combo = QComboBox()
        self.device_combo.setToolTip("Select audio output device")
        device_layout.addWidget(self.device_combo)

        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.clicked.connect(self.populate_devices)
        device_layout.addWidget(refresh_btn)

        layout.addWidget(device_group)

        # File selection
        file_group = QGroupBox("Audio File")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label)

        open_btn = QPushButton("Open File")
        open_btn.clicked.connect(self.open_file)
        file_layout.addWidget(open_btn)

        layout.addWidget(file_group)

        # Playback progress
        progress_group = QGroupBox("Playback Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setToolTip("Playback position")
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        progress_layout.addWidget(self.position_slider)

        time_layout = QHBoxLayout()
        self.time_elapsed = QLabel("00:00")
        time_layout.addWidget(self.time_elapsed)

        time_layout.addStretch(1)

        self.time_total = QLabel("00:00")
        time_layout.addWidget(self.time_total)

        progress_layout.addLayout(time_layout)

        layout.addWidget(progress_group)

        # Playback controls
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QHBoxLayout(controls_group)

        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_btn)

        layout.addWidget(controls_group)

        # Add spacer
        layout.addStretch(1)

        # Set up timer for position updates
        self.update_timer = QTimer()
        self.update_timer.setInterval(500)  # 500ms update rate
        self.update_timer.timeout.connect(self.update_position)

    def initialize_player(self):
        """Initialize the audio player."""
        try:
            # Populate device list
            self.populate_devices()

            # Get default device
            default_device = AudioPlayer.get_default_device()
            device_index = default_device["index"] if default_device else None

            # Create player
            self.player = AudioPlayer(
                device_index=device_index,
                sample_rate=44100,
                channels=2,
                format="float32"
            )

            # Set up completion callback
            self.player.on_playback_complete(self.on_playback_complete)

        except Exception as e:
            self.file_label.setText(f"Error initializing player: {str(e)}")
            QMessageBox.critical(
                self,
                "Player Error",
                f"Could not initialize audio player: {str(e)}"
            )

    def populate_devices(self):
        """Populate the device selection combo box."""
        self.device_combo.clear()

        try:
            devices = AudioPlayer.list_devices()

            for i, device in enumerate(devices):
                name = device.get("name", f"Device {i}")
                is_default = device.get("default", False)

                if is_default:
                    name += " (Default)"

                self.device_combo.addItem(name, device.get("index"))

            self.device_combo.currentIndexChanged.connect(self.on_device_changed)

            if not devices:
                self.device_combo.addItem("No devices found")

        except Exception as e:
            self.device_combo.addItem(f"Error listing devices: {str(e)}")

    def on_device_changed(self, index):
        """Handle device selection changes."""
        if self.player and self.player.is_playing():
            self.stop_playback()

        try:
            # Get device index
            device_index = self.device_combo.currentData()

            # Close existing player
            if self.player:
                self.player.close()

            # Create new player with selected device
            self.player = AudioPlayer(
                device_index=device_index,
                sample_rate=44100,
                channels=2,
                format="float32"
            )

            # Set up completion callback
            self.player.on_playback_complete(self.on_playback_complete)

            # If we have a file, reload it
            if self.current_file:
                self.open_file(self.current_file)

        except Exception as e:
            self.file_label.setText(f"Error changing device: {str(e)}")

    def open_file(self, file_path=None):
        """Open an audio file."""
        if not file_path:
            # Get file name
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Audio File",
                os.path.expanduser("~"),
                "Audio Files (*.wav *.mp3 *.ogg *.flac);;All Files (*)"
            )

            if not file_path:
                return

        try:
            # Stop current playback
            if self.player and self.player.is_playing():
                self.player.stop()

            # Load the file
            self.player.play(file_path)
            self.player.pause()  # Don't start playing immediately

            # Update UI
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))

            # Update duration
            duration = self.player.get_duration()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            self.time_total.setText(f"{minutes:02d}:{seconds:02d}")

            # Set up slider
            self.position_slider.setMaximum(int(duration * 100))  # 100 steps per second
            self.position_slider.setValue(0)

            # Enable buttons
            self.play_btn.setEnabled(True)
            self.play_btn.setText("Play")
            self.stop_btn.setEnabled(True)

        except Exception as e:
            self.file_label.setText(f"Error opening file: {str(e)}")
            QMessageBox.critical(
                self,
                "File Error",
                f"Could not open audio file: {str(e)}"
            )

    def toggle_playback(self):
        """Toggle between play and pause."""
        if not self.player:
            return

        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setText("Play")
            self.update_timer.stop()
        else:
            self.player.resume()
            self.play_btn.setText("Pause")
            self.update_timer.start()

    def stop_playback(self):
        """Stop playback."""
        if not self.player:
            return

        self.player.stop()
        self.play_btn.setText("Play")
        self.position_slider.setValue(0)
        self.update_timer.stop()
        self.time_elapsed.setText("00:00")

    def update_position(self):
        """Update position display and slider."""
        if not self.player or not self.player.is_playing():
            return

        # Get current position
        position = self.player.get_position()

        # Update slider (without triggering events)
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(int(position * 100))
        self.position_slider.blockSignals(False)

        # Update time display
        minutes = int(position // 60)
        seconds = int(position % 60)
        self.time_elapsed.setText(f"{minutes:02d}:{seconds:02d}")

    def on_slider_released(self):
        """Handle slider position changes."""
        if not self.player:
            return

        # Get slider position
        position = self.position_slider.value() / 100.0

        # Seek to position
        self.player.seek(position)

        # Update time display
        minutes = int(position // 60)
        seconds = int(position % 60)
        self.time_elapsed.setText(f"{minutes:02d}:{seconds:02d}")

    def on_playback_complete(self):
        """Handle playback completion."""
        self.play_btn.setText("Play")
        self.update_timer.stop()

        # Reset position to beginning
        self.position_slider.setValue(0)
        self.time_elapsed.setText("00:00")


class MainWindow(QMainWindow):
    """Main window for the FMUS-VOX GUI application."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("FMUS-VOX Audio Tool")
        self.setMinimumSize(600, 400)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tabs
        self.tabs = QTabWidget()

        # Add recorder tab
        self.recorder_tab = RecorderTab()
        self.tabs.addTab(self.recorder_tab, "Recorder")

        # Add player tab
        self.player_tab = PlayerTab()
        self.tabs.addTab(self.player_tab, "Player")

        layout.addWidget(self.tabs)

    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up resources
        if hasattr(self.recorder_tab, "microphone") and self.recorder_tab.microphone:
            self.recorder_tab.microphone.close()

        if hasattr(self.player_tab, "player") and self.player_tab.player:
            self.player_tab.player.close()

        event.accept()


def check_dependencies():
    """Check if PyQt6 is available."""
    if not PYQT_AVAILABLE:
        print("PyQt6 is not installed. Please install it with:")
        print("pip install PyQt6")
        return False
    return True


def run_app():
    """Run the FMUS-VOX GUI application."""
    if not check_dependencies():
        return 1

    # Create application
    app = QApplication(sys.argv)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())
