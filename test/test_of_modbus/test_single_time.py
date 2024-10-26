import time
import minimalmodbus
import serial


class SensorReader:
    def __init__(self, port, slave_address, baudrate=9600):
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self.instrument.serial.baudrate = baudrate
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.stopbits = 1
        self.instrument.serial.timeout = 0.05
        self.instrument.mode = minimalmodbus.MODE_RTU
        self.instrument.clear_buffers_before_each_transaction = True

    def read_float(self, register_address):
        try:
            return self.instrument.read_float(
                registeraddress=register_address,
                functioncode=3,
                number_of_registers=2
            )
        except Exception as e:
            print(f"读取错误: {e}")
            return None


def convert_address(address, is_hex=True):
    if is_hex:
        if isinstance(address, str):
            if address.startswith('0x'):
                address = address[2:]
        hex_address = int(address, 16)
        plc_address = 40001 + hex_address
        modbus_address = hex_address
    else:
        plc_address = int(address)
        modbus_address = plc_address - 40001
    return modbus_address, plc_address


def main():
    PORT = input("请输入串口号 (例如 'COM3'): ")
    SLAVE_ADDRESS = int(input("请输入从机地址 (1-247): "))
    BAUDRATE = int(input("请输入波特率 (默认9600): ") or "9600")

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

    modbus_address, plc_address = convert_address(address_input, is_hex)

    print(f"\n地址信息:")
    print(f"PLC地址: {plc_address}")
    print(f"Modbus协议地址: {modbus_address} (十六进制: 0x{modbus_address:04X})")
    print(f"实际通信地址: 0x{modbus_address:04X}\n")

    sensor = SensorReader(PORT, SLAVE_ADDRESS, BAUDRATE)

    # 执行单次读取并测量时间
    start_time = time.perf_counter()
    value = sensor.read_float(register_address=modbus_address)
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"单次读取耗时: {duration:.6f} 秒")
    print(f"理论最大采集率: {1 / duration:.2f} Hz")

    if value is not None:
        print(f"读取的值: {value}")


if __name__ == "__main__":
    main()
