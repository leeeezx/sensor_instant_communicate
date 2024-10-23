import time
import struct
import serial
import crcmod.predefined


def calculate_crc(data):
    crc16 = crcmod.predefined.mkCrcFun('modbus')
    return struct.pack('<H', crc16(data))


class SensorReader:
    def __init__(self, port, slave_address, baudrate=9600):
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=0.05
        )
        self.slave_address = slave_address

    def read_float(self, register_address):
        try:
            # Construct Modbus RTU message
            message = struct.pack('>BBHH', self.slave_address, 0x03, register_address, 40)
            message += calculate_crc(message)

            # Send request
            self.serial.write(message)

            # Read response
            response = self.serial.read(
                9)  # 1 byte slave address + 1 byte function code + 1 byte length + 4 bytes data + 2 bytes CRC

            if len(response) != 9:
                return None

            # Extract float value
            value = struct.unpack('>f', response[3:7])[0]
            return value
        except Exception:
            return None

    def close(self):
        self.serial.close()


def main():
    PORT = input("请输入串口号 (例如 'COM3'): ")
    SLAVE_ADDRESS = int(input("请输入从机地址 (1-247): "))
    BAUDRATE = int(input("请输入波特率 (默认9600): ") or "9600")
    modbus_address = int(input("请输入Modbus地址 (十进制): "))

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
    finally:
        sensor.close()


if __name__ == "__main__":
    main()
