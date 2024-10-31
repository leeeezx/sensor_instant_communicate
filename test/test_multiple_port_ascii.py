"""
基于ascii模式，同时使用多通道（串口）进行传感器数据采集解码
"""

import threading
from queue import Queue
from collections import deque
import numpy as np
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
        初始化三维力传感器模型,创建后面要用的model实例

        :param port_configs: 包含三个维度串口配置的字典。示例，'传感器维度'+'具体维度的配置'，具体配置又是一个字典
        """
        self.models = {}                                            # 用于存储每个维度的AsciiSendModel实例
        self.queues = {}                                            # 用于存储每个维度的数据队列
        for dimension, config in port_configs.items():              # 循环遍历port_config中的每个维度和其对应的配置
            self.models[dimension] = AsciiSendModel(**config)       # 创建实例
            self.queues[dimension] = Queue()                        # 创建Queue实例

    def read_dimension_data(self, dimension: str):
        """
        读取单个特定维度的数据

        :param dimension: 维度名称 ('X', 'Y', 或 'Z')
        """
        model = self.models[dimension]              # 获取指定维度的对象
        for reports in model.read_sensor_data():    # 持续产生数据
            self.queues[dimension].put(reports)     # 将数据存入对应的队列中

    def read_all_dimension(self):
        """
        开始从所有维度读取数据

        :return: 线程列表
        """
        threads = {}                            # 创建一个空列表，用于存储即将创建的所有线程
        for dimension in self.models.keys():    # 开始一个循环,遍历 self.models 字典中的所有键。这些键代表不同的维度(如 'X', 'Y', 'Z')。
            thread = threading.Thread(target=self.read_dimension_data, args=(dimension,))   # threading.Thread 创建一个新的线程对象；target=self.read_dimension_data 指定线程要执行的函数；args=(dimension,) 传递给目标函数的参数,这里是维度名称。
            thread.daemon = True
            thread.start()
            threads[dimension] = thread
        return threads

    def get_dimension_data(self, dimension: str) -> List[str]:
        """
        获取单个维度的数据

        :param dimension:
        :return:
        """
        data = []
        while not self.queues[dimension].empty():
            data.extend(self.queues[dimension].get())
        return data

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
        'X': {'port_name': 'COM8', 'baudrate': 115200},
        'Y': {'port_name': 'COM9', 'baudrate': 115200},
        'Z': {'port_name': 'COM10', 'baudrate': 115200}
    }

    force_model = ThreeDimensionalForceModel(port_configs)

    try:
        threads = force_model.read_all_dimension()      # 开始多线程读取数据
        start_time = time.time()
        run_duration = 10  # 运行10秒

        while time.time() - start_time < run_duration:
            data = force_model.get_data()
            for dimension, values in data.items():
                if values:
                    logger.info(f"{dimension} 维度数据: {values[:5]}...")  # 只显示前5个数据
            # time.sleep(0.1)  # 短暂休眠，避免过度消耗CPU

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    finally:
        force_model.close()
        logger.info("所有串口已关闭")

if __name__ == "__main__":
    main()