"""
第一步：检测电脑中的串口，打印输出电脑中现有的串口，让使用者进行选择。（已完成）
第二步：
本test文件目的：
测试串口程序与modbus03读命令的联动。
"""
import minimalmodbus
import serial
import time
import struct


class SensorReader:
    def __init__(self, port, slave_address, baudrate=9600):
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.instrument.serial.baudrate = baudrate
        # 默认的是8N1
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 1.0
        # 默认模式是modbusRTU
        self.instrument.mode = minimalmodbus.MODE_RTU
        self.instrument.clear_buffers_before_each_transaction = True

    def read_float(self, register_address):
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

            return round(float_value, 2)  # 保留两位小数
        except Exception as e:
            print(f"读取错误: {e}")
            return None


def main():
    PORT = input("请输入串口号 (例如 'COM3'): ")
    SLAVE_ADDRESS = int(input("请输入从机地址 (1-247): "))
    BAUDRATE = int(input("请输入波特率 (默认9600): ") or "9600")
    REGISTER_ADDRESS = int(input("请输入测量值的寄存器地址: "))

    try:
        sensor = SensorReader(PORT, SLAVE_ADDRESS, BAUDRATE)

        print("开始读取数据，按 Ctrl+C 停止...")
        while True:
            float_value = sensor.read_float(register_address=REGISTER_ADDRESS)
            if float_value is not None:
                print(f"测量值: {float_value} kg")
            time.sleep(1)  # 设置每隔几秒读取一次数据

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        print("程序结束")


if __name__ == "__main__":
    main()
