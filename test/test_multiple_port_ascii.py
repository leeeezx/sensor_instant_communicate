"""
基于ascii模式，同时使用多通道（串口）进行传感器数据采集解码
"""

import threading
from queue import Queue
import time
import logging
from typing import Dict, List
"""
test专属，移动到src这一句需要去掉
"""
from src.single_port_ascii import AsciiSendModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThreeDimensionalForceModel:
    def __init__(self, port_configs: Dict[str, Dict]):
        """
        初始化三维力传感器模型

        :param port_configs: 包含三个维度串口配置的字典
        """
        self.models = {}
        self.queues = {}
        for dimension, config in port_configs.items():
            self.models[dimension] = AsciiSendModel(**config)
            self.queues[dimension] = Queue()

    def read_dimension_data(self, dimension: str):
        """
        读取特定维度的数据

        :param dimension: 维度名称 ('X', 'Y', 或 'Z')
        """
        model = self.models[dimension]
        for reports in model.read_sensor_data():
            self.queues[dimension].put(reports)

    def start_reading(self):
        """
        开始从所有维度读取数据
        """
        threads = []
        for dimension in self.models.keys():
            thread = threading.Thread(target=self.read_dimension_data, args=(dimension,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        return threads

    def get_data(self) -> Dict[str, List[str]]:
        """
        获取所有维度的数据

        :return: 包含每个维度数据的字典
        """
        data = {dim: [] for dim in self.models.keys()}
        for dimension, queue in self.queues.items():
            while not queue.empty():
                data[dimension].extend(queue.get())
        return data

    def close(self):
        """
        关闭所有串口连接
        """
        for model in self.models.values():
            model.close()

def main():
    # 配置三个串口
    port_configs = {
        'X': {'port_name': 'COM10', 'baudrate': 115200},
        'Y': {'port_name': 'COM11', 'baudrate': 115200},
        'Z': {'port_name': 'COM12', 'baudrate': 115200}
    }

    force_model = ThreeDimensionalForceModel(port_configs)
    threads = force_model.start_reading()

    try:
        start_time = time.time()
        run_duration = 10  # 运行10秒

        while time.time() - start_time < run_duration:
            data = force_model.get_data()
            for dimension, values in data.items():
                if values:
                    logger.info(f"{dimension} 维度数据: {values[:5]}...")  # 只显示前5个数据
            time.sleep(0.1)  # 短暂休眠，避免过度消耗CPU

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    finally:
        force_model.close()
        logger.info("所有串口已关闭")

if __name__ == "__main__":
    main()