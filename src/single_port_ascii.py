"""
模块功能描述：
单通道ascii模式数据采集、解码、分析
*********************************
版本：1.0
最近一次修改日期：2024-10-29

修改日志：
2024-10-29，优化程序，添加单独的测试模块
"""
import logging
from typing import Optional, List, Dict, Any
import serial
import time


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsciiSendModel():
    """
    关于传感器ascii模式的类，包括参数设置和工具函数
    """

    def __init__(self,
                 port_name: Optional[str] = None,
                 baudrate: int = 115200,
                 bytesize: int = 8,
                 parity: str = 'N',
                 stopbits: int = 1,
                 timeout: float = 1,
                 minimum_packet_interval: Optional[float] = None,
                 byte_num_of_one_message: int = 7,
                 buffer_size: Optional[int] = None,
                 **kwargs: Any):
        """
        参数初始化

        :param port_name: 串口名称
        :param baudrate: 波特率
        :param bytesize: 数据位
        :param parity: 校验位 ('N', 'E', 'O', 'M', 'S')
        :param stopbits: 停止位
        :param timeout: 超时时间
        :param minimum_packet_interval: 最小包间隔。ascii模式只能保证实际包间隔时间大于仪表的设定值
        :param byte_num_of_one_message: 一个报文的字节数
        :param buffer_size: 串口缓冲区大小
        :param kwargs: 其它参数
        """
        self.port_name = port_name
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.minimum_packet_interval = minimum_packet_interval
        self.byte_num_of_one_message = byte_num_of_one_message

        # 检查额外的参数
        if kwargs:
            raise ValueError('猪头，压根没有这玩意！： {!r}'.format(kwargs))

        # 配置并打开串口
        self.ser = serial.Serial(
            port=self.port_name,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            timeout=self.timeout
        )

    def close(self) -> None:
        """显式关闭串口"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
            logger.info("串口已关闭")


    """
    *********************工具函数***********************
    """

    def read_sensor_data(self,
                         standard_message_length: int = 7,
                         report_count: int = 50,
                         chunk_size: int = 512) -> List[str]:
        """
        在ascii通讯模式下读取串口数据：
        1. 首先找到第一个回车符(0D)作为数据同步点
        2. 之后的数据才开始正式接收和解码处理

        :param standard_message_length: 标准通讯模式下，符合标准的默认报文长度（以字节为单位）
        :param report_count: 一次抛出的报文数量限制（已经转换为仪表数值，kg为单位）
        :param chunk_size: 缓冲区大小

        :return: 解码后的报文列表
        """
        if not self.ser.is_open:
            logger.error("串口未打开")
            raise serial.SerialException("串口未打开")


        buffer = bytearray()  # 创建空的字节串
        reports = []  # 创建报文空列表

        while True:                     # 进入数据处理循环
            # 读取新数据并添加到buffer
            if self.ser.in_waiting:     # 如果串口中有数据等待
                # print('串口有数据')
                chunk = self.ser.read(min(self.ser.in_waiting, chunk_size))  # 从等待区和设置的chunk区中，选一个较小的区，进行读取操作
                buffer.extend(chunk)    # 添加到buffer中

            while len(buffer) >= standard_message_length:         # 当buffer超过默认报文长度7
                cr_index = buffer.find(b'\r')       # cr_index作为空格符的索引
                if cr_index == -1 or cr_index < standard_message_length - 1:  # 如果cr_index不存在或小于6。防止串口刚开始接收数据时，数据被截断。
                    break                   # 没有完整报文，退出循环

                valid_data = buffer[:cr_index + 1]
                buffer = buffer[cr_index + 1:]  # 更新buffer

                try:
                    decoded_data = valid_data.decode('ascii').strip()
                    reports.append(decoded_data)
                    # print('report添加完毕')
                    if len(reports) >= report_count:
                        # print('report已抛出')
                        # total_reports += len(reports)       # 采集率计算
                        yield reports
                        reports = []
                except UnicodeDecodeError as e:
                    logging.error(f"解码错误：{e}，丢弃无效数据")

            # 如果buffer过大，可能表示数据积压，清理旧数据
            if len(buffer) > chunk_size * 2:
                buffer = buffer[-chunk_size:]
                logger.warning("数据积压，清理旧数据")

            # 如果没有足够的报文，短暂等待更多数据到达
            if not reports:
                time.sleep(0.005)  # 等待时间，可根据需要调整


class TestInfo:
    """
    专门用于测试的类
    """
    def __init__(self):
        self.start_time: float = time.time()
        self.total_reports: int = 0              # 采集率初始计数设置0
        self.all_data: List[str] = []

    def add_reports(self, reports: List[str]) -> None:
        """
        添加新的报告数据

        :param reports: 新的报告数据列表
        """
        self.total_reports += len(reports)
        self.all_data.extend(reports)

    def get_results(self) -> Dict[str, Any]:
        """
        获取测试结果

        :return: 包含测试结果的字典
        """
        end_time = time.time()
        duration = end_time - self.start_time
        sampling_rate = self.total_reports / duration if duration > 0 else 0
        return {
            "duration": duration,
            "sampling_rate": sampling_rate,
            "total_reports": self.total_reports,
            "all_data": self.all_data
        }

    def print_results(self) -> None:
        """打印测试结果"""
        results = self.get_results()
        logger.info(f"平均采集率: {results['sampling_rate']:.2f} 个/秒")
        logger.info("所有采集到的数值:")
        for i, data in enumerate(results['all_data'], 1):
            logger.info(f"{i}: {data}")

def run_ascii_send_model(run_duration: Optional[float] = None,
                         enable_test_info: bool = True
                         ) -> None:
    """
    运行ASCII发送模型

    :param run_duration: 运行持续时间（秒），如果为None则一直运行，操作者可以手动停止
    :param enable_test_info: 是否启用测试信息收集
    """
    ascii_model = None
    test_info = TestInfo() if enable_test_info else None

    try:
        ascii_model = AsciiSendModel(port_name='COM10',
                                     baudrate=115200,
                                     )
        print('马上开始')

        start_time = time.time()
        for reports in ascii_model.read_sensor_data():  # 积累了指定数量的数据后，返回一次reports。即由ascii_model.read_sensor_data()来触发循环
            if enable_test_info:
                test_info.add_reports(reports)

            if time.time() - start_time > run_duration:
                break

    except Exception as e:
        logger.error(f"发生错误: {e}", exc_info=True)
    finally:
        if ascii_model:
            ascii_model.close()

        if enable_test_info and test_info:
            test_info.print_results()

if __name__ == "__main__":
    # 测试运行，包含测试功能
    run_ascii_send_model(run_duration=10, enable_test_info=True)
