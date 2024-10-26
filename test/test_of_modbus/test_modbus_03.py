import time
import datetime
from collections import deque
import statistics
import struct

import minimalmodbus
import serial


class SensorReader:
    def __init__(self, port, slave_address, baudrate=9600):
        """
        初始化传感器读取器的相关参数

        :param port: 串口选择
        :param slave_address: 从机地址
        :param baudrate: 波特率
        :param sample_rate: 采样率（默认是1hz）

        还包括：数据位、停止位、校验位（默认是8N1），modbus通讯模式等等
        """
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.instrument.serial.baudrate = baudrate
        # 默认的是8N1
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 0.05
        # 默认模式是modbusRTU
        self.instrument.mode = minimalmodbus.MODE_RTU
        self.instrument.clear_buffers_before_each_transaction = True

        # 添加一个列表来存储所有读取的值
        self.all_values = []

    def read_float(self, register_address, precision_bit=2):
        """
        读取浮点数。包括了接收信息向浮点数的转换

        :param register_address: 寄存器地址
        :param precision_bit: 精度位数
        :return: 传感器数值
        """
        try:
            # 读取4个字节（2个寄存器）的原始数据
            raw_data = self.instrument.read_registers(
                registeraddress=register_address,
                number_of_registers=2,
                functioncode=3
            )
            # 将两个16位整数合并为一个32位整数
            combined = (raw_data[0] << 16) | raw_data[1]
            # 使用struct将32位整数解析为浮点数
            float_value = struct.unpack('>f', struct.pack('>I', combined))[0]

            rounded_value = round(float_value, precision_bit)
            # 将读取的值添加到列表中
            self.all_values.append(rounded_value)
            return rounded_value
        except Exception as e:
            print(f"读取错误: {e}")
            return None

def convert_address(address, is_hex=True):
    """
    转换地址格式
    :param address: 输入的地址
    :param is_hex: 是否是十六进制输入
    :return : modbus协议地址
    """
    if is_hex:
        # 如果是十六进制输入 (例如 0x0206)
        if isinstance(address, str):
            if address.startswith('0x'):
                address = address[2:]
        hex_address = int(address, 16)
        plc_address = 40001 + hex_address  # PLC地址
        modbus_address = hex_address  # Modbus协议地址
    else:
        # 如果是十进制输入 (例如 40519)
        plc_address = int(address)
        modbus_address = plc_address - 40001  # 转换为Modbus协议地址

    return modbus_address, plc_address

def main():
    PORT = input("请输入串口号 (例如 'COM3'): ")
    SLAVE_ADDRESS = int(input("请输入从机地址 (1-247): "))
    BAUDRATE = int(input("请输入波特率 (默认9600): ") or "9600")

    # 选择地址输入方式
    address_type = input("选择地址输入方式 (1:十六进制[默认] 2:十进制): ") or "1"
    is_hex = address_type == "1"

    if is_hex:
        print("\n请输入十六进制地址:")
        print("示例: 对于PLC地址40519, 应输入0206或206")
        address_input = input("请输入寄存器地址: ")
    else:
        print("\n请输入十进制PLC地址:")
        print("示例: 40519")
        address_input = input("请输入PLC地址: ")

    # 转换地址
    modbus_address, plc_address = convert_address(address_input, is_hex)

    print(f"\n地址信息:")
    print(f"PLC地址: {plc_address}")
    print(f"Modbus协议地址: {modbus_address} (十六进制: 0x{modbus_address:04X})")   # 04x是用于转换modbus_address为十六进制显示
    print(f"实际通信地址: 0x{modbus_address:04X}\n")

    sensor = SensorReader(PORT, SLAVE_ADDRESS, BAUDRATE)
    print("\n开始读取数据，按 Ctrl+C 停止...")
    sample_count = 0
    start_time = time.perf_counter()

    try:
        while True:
            value = sensor.read_float(register_address=modbus_address)
            if value is not None:
                sample_count += 1
    except KeyboardInterrupt:
        end_time = time.perf_counter()
        duration = end_time - start_time
        actual_rate = sample_count / duration if duration > 0 else 0
        print(f"\n程序结束")
        print(f"总运行时间: {duration:.2f} 秒")
        print(f"总采样次数: {sample_count}")
        print(f"实际平均采样率: {actual_rate:.2f} Hz")

        # 输出所有读取到的传感器值
        print("\n所有读取到的传感器值:")
        for i, value in enumerate(sensor.all_values, 1):
            print(f"读取 {i}: {value}")

        # 如果数据量很大，可以只打印统计信息
        if len(sensor.all_values) > 100:
            print("\n数据统计:")
            print(f"总数据点: {len(sensor.all_values)}")
            print(f"最小值: {min(sensor.all_values)}")
            print(f"最大值: {max(sensor.all_values)}")
            print(f"平均值: {sum(sensor.all_values) / len(sensor.all_values):.2f}")


if __name__ == "__main__":
    main()
