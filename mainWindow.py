import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                              QGroupBox, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton)
from PyQt6.QtCore import QTimer, QDateTime, Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chart GUI Application')
        self.setGeometry(100, 100, 800, 600)
        self.frequency = 1.0
        self.wave_range = 1.0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sin)
        self.start_time = QDateTime.currentMSecsSinceEpoch() / 1000.0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.sin_chart = ChartWidget("Time Domain", "Time (Seconds)", "Amplitude")
        self.tab2_chart = ChartWidget("Frequency Domain", "Time (Seconds)", "Amplitude")
        self.tabs.addTab(self.sin_chart, "Time Domain (Sine Wave) Plot")
        self.tabs.addTab(self.tab2_chart, "Frequency Domain (FFT) Plot")
        
        self.time_list = []
        self.y_list = []
        self.max_points = 100
        self.timer.start(10)
        self.update_tab2()

    def update_sin(self):
        current_time = QDateTime.currentMSecsSinceEpoch() / 1000.0
        elapsed_time = current_time - self.start_time
        y = self.wave_range * np.sin(2*np.pi*self.frequency*elapsed_time)
        if len(self.time_list) >= self.max_points:
            self.time_list.pop(0)
            self.y_list.pop(0)
        self.time_list.append(elapsed_time)
        self.y_list.append(y)
        self.sin_chart.plot_data(self.time_list, self.y_list, color='green')

    def update_tab2(self):
        x = np.random.rand(50)
        y = np.random.rand(50)
        self.tab2_chart.plot_data(x, y, color='black')

    def create_control_panel(self):
        control_group = QGroupBox("Signal Control Panel")
        cpanel_layout = QVBoxLayout()
        range_layout = QHBoxLayout()
        freq_layout = QHBoxLayout()

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


        
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_chart_view)
        cpanel_layout.addWidget(reset_btn)
        
        control_group.setLayout(cpanel_layout)
        return control_group

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
        self.tab2_chart.reset_view()

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

    def plot_data(self, x_data, y_data, color='blue'):
        self.axes.clear()
        self.axes.plot(x_data, y_data, color=color)
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