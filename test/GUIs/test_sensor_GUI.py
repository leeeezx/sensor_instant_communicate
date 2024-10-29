import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox)
from PyQt6.QtCore import QTimer, pyqtSlot
import pyqtgraph as pg
from collections import deque

# 从现有文件导入必要的类和函数
from test.test_of_modbus.test_modbus_03 import SensorReader, convert_address


class SensorMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("传感器数据监视器")
        self.setGeometry(100, 100, 800, 600)

        # 数据存储
        self.data_length = 100
        self.times = deque(maxlen=self.data_length)
        self.values = deque(maxlen=self.data_length)
        self.start_time = time.time()

        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 创建控制面板
        self.create_control_panel()

        # 创建图表
        self.create_plot()

        # 初始化传感器相关变量
        self.sensor = None
        self.modbus_address = None
        self.is_running = False

        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.update_interval = 1000  # 1秒更新一次

    def create_control_panel(self):
        control_layout = QHBoxLayout()

        self.port_label = QLabel("串口:")
        self.port_input = QLineEdit("COM3")
        control_layout.addWidget(self.port_label)
        control_layout.addWidget(self.port_input)

        self.slave_label = QLabel("从机地址:")
        self.slave_input = QLineEdit("1")
        control_layout.addWidget(self.slave_label)
        control_layout.addWidget(self.slave_input)

        self.baud_label = QLabel("波特率:")
        self.baud_input = QLineEdit("9600")
        control_layout.addWidget(self.baud_label)
        control_layout.addWidget(self.baud_input)

        self.addr_type_label = QLabel("地址类型:")
        self.addr_type_select = QComboBox()
        self.addr_type_select.addItems(["十六进制", "十进制"])
        control_layout.addWidget(self.addr_type_label)
        control_layout.addWidget(self.addr_type_select)

        self.addr_label = QLabel("寄存器地址:")
        self.addr_input = QLineEdit("0206")
        control_layout.addWidget(self.addr_label)
        control_layout.addWidget(self.addr_input)

        self.start_button = QPushButton("启动")
        self.start_button.clicked.connect(self.toggle_monitoring)
        control_layout.addWidget(self.start_button)

        self.layout.addLayout(control_layout)

    def create_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("传感器实时数据", color="b", size="30pt")
        self.plot_widget.setLabel('left', '测量值 (kg)')
        self.plot_widget.setLabel('bottom', '时间 (s)')
        self.plot_widget.showGrid(x=True, y=True)
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color=(255, 0, 0), width=2))

        self.layout.addWidget(self.plot_widget)

    def toggle_monitoring(self):
        if not self.is_running:
            try:
                port = self.port_input.text()
                slave_address = int(self.slave_input.text())
                baudrate = int(self.baud_input.text())
                is_hex = self.addr_type_select.currentText() == "十六进制"
                address = self.addr_input.text()

                self.modbus_address, _ = convert_address(address, is_hex)

                self.sensor = SensorReader(port, slave_address, baudrate)

                self.times.clear()
                self.values.clear()
                self.start_time = time.time()

                self.timer.start(self.update_interval)
                self.is_running = True
                self.start_button.setText("停止")

            except Exception as e:
                print(f"启动错误: {e}")
                return
        else:
            self.timer.stop()
            self.is_running = False
            self.start_button.setText("启动")
            if self.sensor:
                self.sensor.instrument.serial.close()
                self.sensor = None

    @pyqtSlot()
    def update_plot(self):
        if self.sensor and self.modbus_address is not None:
            value = self.sensor.read_float(self.modbus_address, precision_bit=2)
            if value is not None:
                current_time = time.time() - self.start_time
                self.times.append(current_time)
                self.values.append(value)

                self.curve.setData(list(self.times), list(self.values))


def main():
    app = QApplication(sys.argv)
    window = SensorMonitorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
