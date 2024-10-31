"""
专门针对多串口ascii模式的GUI

"""
import sys
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QComboBox, QCheckBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
import serial.tools.list_ports
import pyqtgraph as pg

from test.test_multiple_port_ascii import ThreeDimensionalForceModel


class DataSignals(QObject):
    update_data = pyqtSignal(str, list)


class ForceSensorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("三维力传感器数据采集")
        self.setGeometry(100, 100, 1000, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.port_configs = {}
        self.force_model = None
        self.threads = {}
        self.data_signals = DataSignals()
        self.data_signals.update_data.connect(self.update_plot)

        self.plot_data = {'X': [], 'Y': [], 'Z': []}
        self.plot_curves = {}

        self.init_ui()

    def init_ui(self):
        # 串口配置部分
        for dimension in ['X', 'Y', 'Z']:
            port_layout = QHBoxLayout()
            port_layout.addWidget(QLabel(f"{dimension} 维度:"))

            port_combo = QComboBox()
            port_combo.addItems([port.device for port in serial.tools.list_ports.comports()])
            port_layout.addWidget(port_combo)

            baud_combo = QComboBox()
            baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
            baud_combo.setCurrentText('115200')
            port_layout.addWidget(baud_combo)

            collect_checkbox = QCheckBox("采集数据")
            port_layout.addWidget(collect_checkbox)

            self.layout.addLayout(port_layout)

            self.port_configs[dimension] = {
                'port_combo': port_combo,
                'baud_combo': baud_combo,
                'collect_checkbox': collect_checkbox
            }

        # 绘图区域
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Force')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.addLegend()

        colors = {'X': (255, 0, 0), 'Y': (0, 255, 0), 'Z': (0, 0, 255)}
        for dimension in ['X', 'Y', 'Z']:
            self.plot_curves[dimension] = self.plot_widget.plot(pen=colors[dimension], name=dimension)

        # 开始/停止按钮
        self.start_stop_button = QPushButton("开始采集")
        self.start_stop_button.clicked.connect(self.toggle_collection)
        self.layout.addWidget(self.start_stop_button)

        # 更新定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(100)  # 每100ms更新一次

    def toggle_collection(self):
        if self.start_stop_button.text() == "开始采集":
            self.start_collection()
        else:
            self.stop_collection()

    def start_collection(self):
        port_configs = {}
        for dimension, config in self.port_configs.items():
            if config['collect_checkbox'].isChecked():
                port_configs[dimension] = {
                    'port_name': config['port_combo'].currentText(),
                    'baudrate': int(config['baud_combo'].currentText())
                }

        if port_configs:
            self.force_model = ThreeDimensionalForceModel(port_configs)
            self.threads = self.force_model.read_all_dimension()
            self.start_stop_button.setText("停止采集")
        else:
            print("请至少选择一个维度进行数据采集")

    def stop_collection(self):
        if self.force_model:
            self.force_model.close()
            self.force_model = None
            self.threads = {}
        self.start_stop_button.setText("开始采集")

    def update_data(self):
        if self.force_model:
            for dimension, config in self.port_configs.items():
                if config['collect_checkbox'].isChecked():
                    data = self.force_model.get_dimension_data(dimension)
                    if data:
                        self.data_signals.update_data.emit(dimension, data)

    def update_plot(self, dimension, data):
        # 将字符串数据转换为浮点数
        numeric_data = [float(value) for value in data if value.strip()]
        self.plot_data[dimension].extend(numeric_data)

        # 保持最新的1000个数据点
        self.plot_data[dimension] = self.plot_data[dimension][-1000:]

        # 更新曲线
        self.plot_curves[dimension].setData(self.plot_data[dimension])

    def closeEvent(self, event):
        if self.force_model:
            self.force_model.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = ForceSensorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
