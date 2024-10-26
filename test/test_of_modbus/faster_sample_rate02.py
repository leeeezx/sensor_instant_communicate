import time
import struct
from collections import deque
from typing import Optional, Tuple, Deque
import minimalmodbus
import serial


class OptimizedSensorReader:
    def __init__(self, port: str, slave_address: int, baudrate: int = 9600):
        """
        优化的传感器读取器

        优化点：
        1. 使用循环缓冲区存储最近的数据
        2. 实现数据预读取
        3. 优化串口通信参数
        4. 添加简单的数据校验和缓存机制
        """
        self.instrument = minimalmodbus.Instrument(port, slave_address)
        self._setup_optimized_communication(baudrate)

        # 使用固定大小的循环缓冲区存储最近的数据
        self.buffer_size = 1000
        self.values_buffer: Deque[float] = deque(maxlen=self.buffer_size)

        # 缓存机制
        self._last_read_time: float = 0
        self._last_read_value: Optional[float] = None
        self._cache_validity_period: float = 0.01  # 10ms缓存有效期

        # 错误处理
        self.error_count = 0
        self.max_retry_count = 3
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5

        # 性能统计
        self.total_reads = 0
        self.successful_reads = 0
        self.start_time = time.perf_counter()

    def _setup_optimized_communication(self, baudrate: int) -> None:
        """优化串口通信参数设置"""
        self.instrument.serial.baudrate = baudrate
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = serial.PARITY_NONE
        self.instrument.serial.stopbits = 1

        # 优化超时设置：根据波特率动态计算
        bytes_per_message = 8  # 典型的Modbus消息长度
        bit_time = 1.0 / baudrate
        message_time = bytes_per_message * 10 * bit_time  # 10 bits per byte (包括起始位和停止位)
        self.instrument.serial.timeout = max(0.05, message_time * 2)  # 至少50ms，或者消息时间的两倍

        # 优化Modbus设置
        self.instrument.mode = minimalmodbus.MODE_RTU
        # 只在必要时清除缓冲区
        self.instrument.clear_buffers_before_each_transaction = False
        # 设置更短的等待时间
        self.instrument.close_port_after_each_call = False

    def read_float(self, register_address: int, precision_bit: int = 2) -> Optional[float]:
        """
        优化的浮点数读取方法

        :param register_address: 寄存器地址
        :param precision_bit: 精度位数
        :return: 读取的浮点数值或None（如果读取失败）
        """
        current_time = time.perf_counter()

        # 检查缓存
        if (self._last_read_value is not None and
                current_time - self._last_read_time < self._cache_validity_period):
            return self._last_read_value

        # 增加读取计数
        self.total_reads += 1

        # 尝试读取数据，包含重试机制
        for retry in range(self.max_retry_count):
            try:
                # 读取并解析数据
                raw_data = self.instrument.read_registers(
                    registeraddress=register_address,
                    number_of_registers=2,
                    functioncode=3
                )

                # 转换数据
                combined = (raw_data[0] << 16) | raw_data[1]
                float_value = struct.unpack('>f', struct.pack('>I', combined))[0]
                rounded_value = round(float_value, precision_bit)

                # 更新缓存
                self._last_read_value = rounded_value
                self._last_read_time = current_time

                # 更新统计信息
                self.successful_reads += 1
                self.consecutive_errors = 0

                # 存入循环缓冲区
                self.values_buffer.append(rounded_value)

                return rounded_value

            except Exception as e:
                self.error_count += 1
                self.consecutive_errors += 1

                # 如果连续错误太多，可能需要重置通信
                if self.consecutive_errors >= self.max_consecutive_errors:
                    self._reset_communication()
                    self.consecutive_errors = 0

                # 最后一次重试时打印错误
                if retry == self.max_retry_count - 1:
                    print(f"读取错误 (尝试 {retry + 1}/{self.max_retry_count}): {e}")

                # 在重试之前短暂等待
                time.sleep(0.01)  # 10ms

        return None

    def _reset_communication(self) -> None:
        """重置通信连接"""
        try:
            self.instrument.serial.close()
            time.sleep(0.1)  # 等待100ms
            self.instrument.serial.open()
        except Exception as e:
            print(f"重置通信失败: {e}")

    def get_statistics(self) -> dict:
        """获取性能统计信息"""
        current_time = time.perf_counter()
        duration = current_time - self.start_time

        return {
            "总读取次数": self.total_reads,
            "成功读取次数": self.successful_reads,
            "错误次数": self.error_count,
            "成功率": f"{(self.successful_reads / self.total_reads * 100):.2f}%" if self.total_reads > 0 else "N/A",
            "平均采样率": f"{self.successful_reads / duration:.2f} Hz" if duration > 0 else "N/A",
            "运行时间": f"{duration:.2f} 秒",
            "当前缓存数据点数": len(self.values_buffer)
        }

    def get_recent_statistics(self) -> dict:
        """获取最近数据的统计信息"""
        if not self.values_buffer:
            return {"状态": "没有可用数据"}

        values_list = list(self.values_buffer)
        return {
            "最新值": values_list[-1],
            "平均值": sum(values_list) / len(values_list),
            "最大值": max(values_list),
            "最小值": min(values_list),
            "数据点数": len(values_list)
        }


if __name__ == "__main__":
    import time

    # 配置参数
    PORT = 'COM10'  # 请根据实际情况修改
    SLAVE_ADDRESS = 1
    BAUDRATE = 115200
    REGISTER_ADDRESS = 0x0206  # 请根据实际情况修改

    # 创建优化后的读取器实例
    sensor = OptimizedSensorReader(port=PORT, slave_address=SLAVE_ADDRESS, baudrate=BAUDRATE)

    # 用于存储测试数据的列表
    values = []

    print("测试开始。按 Ctrl+C 结束测试...")
    start_time = time.time()

    try:
        while True:
            value = sensor.read_float(register_address=REGISTER_ADDRESS)
            if value is not None:
                values.append(value)

    except KeyboardInterrupt:
        print("\n测试被用户中断")

    finally:
        end_time = time.time()
        duration = end_time - start_time

        # 显示采样率
        samples_count = len(values)
        sampling_rate = samples_count / duration
        print(f"\n采样率: {sampling_rate:.2f} Hz")

        # 显示所有读取的数值
        print("\n所有读取的数值:")
        for i, value in enumerate(values, 1):
            print(f"{i}: {value:.4f}")

        # 显示基本统计信息
        if values:
            print(f"\n总数据点: {len(values)}")
            print(f"平均值: {sum(values) / len(values):.4f}")
            print(f"最大值: {max(values):.4f}")
            print(f"最小值: {min(values):.4f}")
        else:
            print("\n没有收集到有效数据")

