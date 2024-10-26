"""
本程序的目的：
能够使用三维力传感器的通讯模式2ascii主动发送模式，与pc端正常通信。
"""
import serial
import time

from PyQt6.QtQml import kwargs

port_name = 'COM10'
baudrate = 19200
timeout = 1
# 配置串口
ser = serial.Serial(port_name, baudrate, timeout)  # 根据实际情况修改端口和波特率

# 假设串口在GUI中被打开
# 如果在GUI中选择的是通讯模式2acsii自动发送（这个在GUI程序中进行判断）
# 调用本程序的api


class AcsiiSendModel():


    def __init__(self,
                 minimum_packet_interval=None,
                 byte_num_of_one_message=7,
                 buffer_size=None,
                 **kwargs):
        """
        参数初始化

        :param minimum_packet_interval: 最小包间隔。acsii模式只能保证实际包间隔时间大于仪表的设定值
        :param byte_num_of_one_message: 一个报文的字节数、
        :param buffer_size: 串口缓冲区大小
        :param kwargs: 其它参数
        """

        self.minimum_packet_interval = minimum_packet_interval
        self.byte_num_of_one_message = byte_num_of_one_message

        # 检查额外的参数
        if kwargs:
            raise ValueError('猪头，压根没有这玩意！： {!r}'.format(kwargs))


    def read_sensor_data(self):
        """
        在ascii通讯模式下，读取串口中的传感器数据

        :return:
        """
        # 检查串口是否打开
        if not ser.is_open:
            raise serial.SerialException("串口未打开")

        buffer = bytearray()                # 创建了一个空的字节串对象
        last_receive_time = time.time()     # 建立开始时间戳

        # 如果检测到对应串口打开且有数据累积，开始执行数据读取
        while True:
            if ser.in_waiting:              # 检查是否串口中是否有数据被读取
                byte = ser.read(1)          # ！！！效率低！！！从串口中读取一个字节的数据。read以字节为单位对串口数据进行读取。
                buffer += byte              # ！！！效率低！！！将读取的数据赋值给buffer。原buffer的所有字节后跟着byte的内容
                last_receive_time = time.time() # 更新时间戳，目的是记录最后一次接收数据的时间

                # 方法1：检查是否以回车符结束
                if byte == b'\r':
                    yield buffer.decode('ascii').strip()
                    buffer = b''


            #     # 方法2：检查是否达到固定长度。！！！！逻辑不对，不一定达到了七个字节就是一个符合标准的报文。
            #     if len(buffer) == 7:
            #         yield buffer.decode('ascii').strip()
            #         buffer = b''
            #
            # # 方法3：检查时间间隔。！！！！这里逻辑也不一定对。
            # elif time.time() - last_receive_time > 0.1:  # 假设最小间隔为100ms
            #     if buffer:
            #         yield buffer.decode('ascii').strip()
            #         buffer = b''
            #

    # # 使用示例
    # for data in read_sensor_data():
    #     try:
    #         value = float(data.replace(' ', ''))
    #         print(f"接收到的数值: {value}")
    #     except ValueError:
    #         print(f"无效数据: {data}")
