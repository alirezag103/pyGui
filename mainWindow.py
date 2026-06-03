import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chart GUI Application')
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        self.tab1_chart = ChartWidget()
        self.tab2_chart = ChartWidget()
        self.tabs.addTab(self.tab1_chart, "Line Plot")
        self.tabs.addTab(self.tab2_chart, "Scatter Plot")
        self.update_tab1()
        self.update_tab2()

    def update_tab1(self):
        x = np.linspace(0, 4*np.pi, 100)
        y = np.sin(x)
        self.tab1_chart.plot_data(x, y, "Sin Wave", "X-axis (radians)", "Y-axis (sin value)", color='green')

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
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.axis = self.figure.add_subplot(111)

    def plot_data(self, x_data, y_data, title, x_label, y_label, color='blue'):
        self.axis.clear()
        self.axis.plot(x_data, y_data, color=color)
        self.axis.set_title(title)
        self.axis.set_xlabel(x_label)
        self.axis.set_ylabel(y_label)
        self.axis.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())