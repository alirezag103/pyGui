import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                              QGroupBox, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton,
                              QFileDialog, QMessageBox)
from PyQt6.QtCore import QTimer, QDateTime, QThread, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
import json
import os

class PlaybackThread(QThread):
    data_chunk = pyqtSignal(float, float)
    
    def __init__(self, times, values):
        super().__init__()
        self.times = times
        self.values = values
        self.is_playing = True
        self.current_index = 0
        self.start_time = None
        
    def run(self):
        self.start_time = QDateTime.currentMSecsSinceEpoch() / 1000.0
        while self.is_playing and self.current_index < len(self.times):
            current_time = QDateTime.currentMSecsSinceEpoch() / 1000.0
            elapsed = current_time - self.start_time
            
            # Find all points that should be displayed up to this time
            while (self.current_index < len(self.times) and 
                   self.times[self.current_index] <= elapsed):
                self.data_chunk.emit(self.times[self.current_index], 
                                    self.values[self.current_index])
                self.current_index += 1
            
            self.msleep(10)
    
    def stop(self):
        self.is_playing = False
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chart GUI Application')
        self.setGeometry(100, 100, 900, 700)
        self.frequency = 1.0
        self.wave_range = 1.0

        self.is_recording = False
        self.is_playing_back = False
        self.recorded_times = []
        self.recorded_values = []
        self.playback_thread = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_domain)
        self.start_time = QDateTime.currentMSecsSinceEpoch() / 1000.0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.sin_chart = ChartWidget("Time Domain", "Time (Seconds)", "Amplitude")
        self.freq_chart = ChartWidget("Frequency Domain", "Frequency (Hz)", "Magnitude")
        self.tabs.addTab(self.sin_chart, "Time Domain (Sine Wave) Plot")
        self.tabs.addTab(self.freq_chart, "Frequency Domain (FFT) Plot")
        
        # Initializing Signal
        self.time_list = []
        self.y_list = []
        self.max_points = 200
        self.sampling_rate = 100
        self.timer.start(10)
        self.update_frequency_domain()

    def update_frequency_domain(self):
        if len(self.y_list) < 10:
            return
        y_data = np.array(self.y_list)
        n = len(y_data)
        window = np.hanning(n)
        y_windowed = y_data * window
        fft_vals = np.fft.fft(y_windowed)
        fft_abs = np.abs(fft_vals[:n//2])
        fft_abs = fft_abs / (n/2)

        freq_axis = np.fft.fftfreq(n, 1/self.sampling_rate)[:n//2]
        max_freq = min(20, self.sampling_rate/2)
        mask = freq_axis <= max_freq
        freq_axis = freq_axis[mask]
        fft_abs = fft_abs[mask]
        
        if len(fft_abs) > 0:
            peak_freq = freq_axis[np.argmax(fft_abs)]
            peak_magnitude = np.max(fft_abs)
        else:
            peak_freq = 0
            peak_magnitude = 0
        
        title = f"Frequency Domain - FFT (Peak at {peak_freq:.2f} Hz)"
        self.freq_chart.plot_fft(freq_axis, fft_abs, title, 
                                 "Frequency (Hz)", "Magnitude", 
                                 peak_freq, peak_magnitude)

    def update_time_domain(self):
        if self.is_playing_back:
            return
        current_time = QDateTime.currentMSecsSinceEpoch() / 1000.0
        elapsed_time = current_time - self.start_time
        y = self.wave_range * np.sin(2*np.pi*self.frequency*elapsed_time)
        if self.is_recording:
            self.recorded_times.append(elapsed_time)
            self.recorded_values.append(y)
        if len(self.time_list) >= self.max_points:
            self.time_list.pop(0)
            self.y_list.pop(0)
        self.time_list.append(elapsed_time)
        self.y_list.append(y)
        self.sin_chart.plot_data(self.time_list, self.y_list, color='green')
        self.update_frequency_domain()

    def create_control_panel(self):
        control_group = QGroupBox("Signal Control Panel")
        cpanel_layout = QVBoxLayout()
        range_layout = QHBoxLayout()
        freq_layout = QHBoxLayout()
        record_layout = QHBoxLayout()

        # Range Controls
        range_layout.addWidget(QLabel("Range :"))
        self.range_spinbox = QDoubleSpinBox()
        self.range_spinbox.setRange(0.0, 10.0)
        self.range_spinbox.setSingleStep(0.1)
        self.range_spinbox.setValue(self.wave_range)
        self.range_spinbox.valueChanged.connect(self.update_range)
        range_layout.addWidget(self.range_spinbox)
        self.range_label = QLabel("Current: 1.0")
        range_layout.addWidget(self.range_label)
        range_layout.addStretch()
        cpanel_layout.addLayout(range_layout)
        
        # Frequency Controls
        freq_layout.addWidget(QLabel("Frequency (Hz):"))
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setRange(0.1, 10.0)
        self.freq_spinbox.setSingleStep(0.1)
        self.freq_spinbox.setValue(self.frequency)
        self.freq_spinbox.setSuffix(" Hz")
        self.freq_spinbox.valueChanged.connect(self.update_frequency)
        freq_layout.addWidget(self.freq_spinbox)
        self.freq_label = QLabel("Current: 1.00 Hz")
        freq_layout.addWidget(self.freq_label)
        freq_layout.addStretch()
        cpanel_layout.addLayout(freq_layout)
        
        # Recording Controls
        record_layout.addWidget(QLabel("Recording:"))
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.clicked.connect(self.start_recording)
        record_layout.addWidget(self.record_btn)
        
        self.stop_record_btn = QPushButton("Stop Recording")
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.stop_record_btn.setEnabled(False)
        record_layout.addWidget(self.stop_record_btn)
        
        self.save_btn = QPushButton("Save Recording")
        self.save_btn.clicked.connect(self.save_recording)
        self.save_btn.setEnabled(False)
        record_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Load Recording")
        self.load_btn.clicked.connect(self.load_recording)
        record_layout.addWidget(self.load_btn)
        
        record_layout.addStretch()
        cpanel_layout.addLayout(record_layout)
        
        # Playback Controls
        playback_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play Recording")
        self.play_btn.clicked.connect(self.play_recording)
        self.play_btn.setEnabled(False)
        playback_layout.addWidget(self.play_btn)
        
        self.stop_play_btn = QPushButton("Stop Playback")
        self.stop_play_btn.clicked.connect(self.stop_playback)
        self.stop_play_btn.setEnabled(False)
        playback_layout.addWidget(self.stop_play_btn)
        
        playback_layout.addStretch()
        cpanel_layout.addLayout(playback_layout)

        # Other Controls
        button_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_chart_view)
        button_layout.addWidget(reset_btn)
        clear_btn = QPushButton("Clear Data")
        clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        cpanel_layout.addLayout(button_layout)
        
        control_group.setLayout(cpanel_layout)
        return control_group
    
    def start_recording(self):
        self.recorded_times.clear()
        self.recorded_values.clear()
        self.is_recording = True
        self.record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
        self.save_btn.setEnabled(False)
        self.statusBar().showMessage("Recording started...", 2000)

    def stop_recording(self):
        self.is_recording = False
        self.record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        if len(self.recorded_times) > 0:
            self.save_btn.setEnabled(True)
            self.statusBar().showMessage(f"Recording stopped. {len(self.recorded_times)} points recorded.", 3000)
        else:
            self.statusBar().showMessage("Recording stopped. No data recorded.", 2000)

    def save_recording(self):
        if not self.recorded_times:
            QMessageBox.warning(self, "No Data", "No recorded data to save!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Recording", "", "JSON Files (*.json)")
        if file_path:
            data = {
                'times': self.recorded_times,
                'values': self.recorded_values,
                'sampling_rate': self.sampling_rate
            }
            with open(file_path, 'w') as f:
                json.dump(data, f)
            self.statusBar().showMessage(f"Recording saved to {file_path}", 3000)

    def load_recording(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Recording", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.recorded_times = data['times']
                self.recorded_values = data['values']
                self.play_btn.setEnabled(True)
                self.statusBar().showMessage(f"Loaded {len(self.recorded_times)} points from {file_path}", 3000)
                QMessageBox.information(self, "Load Successful", 
                                       f"Loaded {len(self.recorded_times)} data points.\nClick 'Play Recording' to visualize.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")

    def play_recording(self):
        if not self.recorded_times:
            QMessageBox.warning(self, "No Data", "No recorded data to play!")
            return
        self.timer.stop()
        self.clear_data()
        
        # Start playback thread
        self.is_playing_back = True
        self.playback_thread = PlaybackThread(self.recorded_times, self.recorded_values)
        self.playback_thread.data_chunk.connect(self.add_playback_point)
        self.playback_thread.start()
        
        # Update button states
        self.play_btn.setEnabled(False)
        self.stop_play_btn.setEnabled(True)
        self.record_btn.setEnabled(False)
        self.freq_spinbox.setEnabled(False)
        self.range_spinbox.setEnabled(False)
        
        self.statusBar().showMessage("Playing recording...", 2000)

    def add_playback_point(self, time, value):
        if len(self.time_list) >= self.max_points:
            self.time_list.pop(0)
            self.y_list.pop(0)
        
        self.time_list.append(time)
        self.y_list.append(value)
        self.sin_chart.plot_data(self.time_list, self.y_list, color='green')
        self.update_frequency_domain()

    def stop_playback(self):
        if self.playback_thread:
            self.playback_thread.stop()
            self.playback_thread.wait()
            self.playback_thread = None
        
        self.is_playing_back = False
        self.time_list.clear()
        self.y_list.clear()
        self.timer.start(10)
        
        # Reset button states
        self.play_btn.setEnabled(True)
        self.stop_play_btn.setEnabled(False)
        self.record_btn.setEnabled(True)
        self.freq_spinbox.setEnabled(True)
        self.range_spinbox.setEnabled(True)
        
        self.statusBar().showMessage("Playback stopped", 2000)


    def update_range(self, value):
        self.wave_range = value
        self.update_range_display()

    def update_range_display(self):
        self.range_label.setText(f"Current: {self.wave_range:.2f}")

    def update_frequency(self, value):
        self.frequency = value
        self.update_frequency_display()

    def update_frequency_display(self):
        self.freq_label.setText(f"Current: {self.frequency:.2f} Hz")

    def reset_chart_view(self):
        self.sin_chart.reset_view()
        self.freq_chart.reset_view()

    def clear_data(self):
        self.time_list.clear()
        self.y_list.clear()
        self.start_time = QDateTime.currentMSecsSinceEpoch() / 1000.0
        self.sin_chart.plot_data([], [], color='green')
        self.freq_chart.plot_fft([], [], "Frequency Domain - Cleared", 
                                 "Frequency (Hz)", "Magnitude", 0, 0)

class ChartWidget(QWidget):
    def __init__(self, title, x_label, y_label, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout()
        toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)

    # Time Domain plot draw
    def plot_data(self, x_data, y_data, color='blue'):
        self.axes.clear()
        if x_data and y_data:
            self.axes.plot(x_data, y_data, color=color)
            y_min, y_max = min(y_data), max(y_data)
            y_padding = (y_max - y_min) * 0.1 if y_max != y_min else 0.1
            self.axes.set_ylim(y_min - y_padding, y_max + y_padding)
            if len(x_data) > 1:
                self.axes.set_xlim(max(0, x_data[-1] - 8), x_data[-1])
        else:
            self.axes.set_xlim(0, 10)
            self.axes.set_ylim(-2, 2)
        self.axes.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw_idle()

    # Frequency Domain plot draw
    def plot_fft(self, freq_data, magnitude_data, title, x_label, y_label, 
                 peak_freq=0, peak_magnitude=0):
        self.axes.clear()
        
        if len(freq_data) > 0 and len(magnitude_data) > 0:
            self.axes.stem(freq_data, magnitude_data, linefmt='r-', 
                          markerfmt='ro', basefmt='k-')
            
            if peak_freq > 0 and peak_magnitude > 0:
                self.axes.plot(peak_freq, peak_magnitude, 'bo', markersize=10, 
                              label=f'Peak: {peak_freq:.2f} Hz')
                self.axes.legend()
            
            self.axes.set_xlim(0, max(10, max(freq_data)))
            self.axes.set_ylim(0, max(magnitude_data) * 1.1)
        else:
            self.axes.set_xlim(0, 10)
            self.axes.set_ylim(0, 1)
            self.axes.text(5, 0.5, 'Waiting for data...', 
                          horizontalalignment='center', verticalalignment='center')
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw_idle()
            
    def reset_view(self):
        self.axes.autoscale()
        self.canvas.draw_idle()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())