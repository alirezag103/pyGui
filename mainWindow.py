import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtCore import QTimer, QDateTime
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chart GUI Application')
        self.setGeometry(100, 100, 800, 600)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sin)
        self.start_time = QDateTime.currentMSecsSinceEpoch() / 1000.0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.sin_chart = ChartWidget()
        self.tab2_chart = ChartWidget()
        self.tabs.addTab(self.sin_chart, "Sin Wave Plot")
        self.tabs.addTab(self.tab2_chart, "Scatter Plot")
        
        self.time_list = []
        self.y_list = []
        self.max_points = 100
        self.timer.start(10)
        # self.update_sin()
        self.update_tab2()

    def update_sin(self):
        current_time = QDateTime.currentMSecsSinceEpoch() / 1000.0
        elapsed_time = current_time - self.start_time
        frequency = 1.0
        y = np.sin(2*np.pi*frequency*elapsed_time)
        if len(self.time_list) >= self.max_points:
            self.time_list.pop(0)
            self.y_list.pop(0)
        self.time_list.append(elapsed_time)
        self.y_list.append(y)
        self.sin_chart.plot_data(self.time_list, self.y_list, "Sin Wave", "X-axis (radians)", "Y-axis (sin value)", color='green')

    def update_tab2(self):
        x = np.random.rand(50)
        y = np.random.rand(50)
        self.tab2_chart.plot_data(x, y, "Scatter Plot", "X-axis", "Y-axis", color='black')


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout()
        toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.axes = self.figure.add_subplot(111)

    def plot_data(self, x_data, y_data, title, x_label, y_label, color='blue'):
        self.axes.clear()
        self.axes.plot(x_data, y_data, color=color)
        self.axes.set_title(title)
        self.axes.set_xlabel(x_label)
        self.axes.set_ylabel(y_label)
        self.axes.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())