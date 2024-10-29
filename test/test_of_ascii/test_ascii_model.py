"""
本程序的目的：
能够使用三维力传感器的通讯模式2ascii主动发送模式，与pc端正常通信。
"""
import serial
import time


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
        在ascii通讯模式下读取串口数据：
        1. 首先找到第一个回车符(0D)作为数据同步点
        2. 之后的数据才开始正式接收和解码处理
        """
        if not ser.is_open:
            raise serial.SerialException("串口未打开")

        buffer = bytearray()    # 创建空的字节串
        chunk_size = 512       # 增大读取块大小，以适应高频率数据
        report_count = 50       # 一次处理的报文数量
        reports = []  # 创建报文空列表
        # total_reports = 0  # 用于累计总报文数

        while True:             # 进入数据处理循环
            # 读取新数据并添加到buffer
            if ser.in_waiting:  # 如果串口中有数据等待
                # print('串口有数据')
                chunk = ser.read(min(ser.in_waiting, chunk_size))   # 从等待区和设置的chunk区中，选一个较小的区，进行读取操作
                buffer.extend(chunk)    # 添加到buffer中

            # 处理buffer中的数据

            while len(buffer) >= 7:         # 当buffer超过默认报文长度7
                cr_index = buffer.find(b'\r')       # cr_index作为空格符的索引
                if cr_index == -1 or cr_index < 6:  # 如果cr_index不存在或小于6。防止串口刚开始接收数据时，数据被截断。
                    break       # 没有完整报文，退出循环

                valid_data = buffer[:cr_index + 1]
                buffer = buffer[cr_index + 1:]  # 更新buffer
                # print('buffer已经更新')

                try:
                    decoded_data = valid_data.decode('ascii').strip()
                    reports.append(decoded_data)
                    # print('report添加完毕')
                    if len(reports) >= report_count:
                        # print('report已抛出')
                        # total_reports += len(reports)       # 采集率计算
                        yield reports
                        reports = []
                except UnicodeDecodeError:
                    print("解码错误，丢弃无效数据")

            # 如果buffer过大，可能表示数据积压，清理旧数据
            if len(buffer) > 1024:
                buffer = buffer[-512:]
                print("警告：数据积压，清理旧数据")

            # 如果没有足够的报文，短暂等待更多数据到达
            if not reports:
                time.sleep(0.005)  # 等待时间，可根据需要调整


if __name__ == '__main__':
    # 测试代码
    port_name = 'COM10'
    baudrate = 115200
    timeout = 1
    bytesize = 8
    # 配置串口
    ser = serial.Serial(port=port_name,
                        baudrate=baudrate,
                        bytesize=bytesize,
                        timeout=timeout)  # 根据实际情况修改端口和波特率


    try:
        acsii = AcsiiSendModel()
        total_reports = 0           # 采集率初始计数设置0

        print('马上开始')

        start_time = time.time()    # 采集率初始时间标记
        run_duration = 10           # 可选设置，测试时间
        all_data = []               # 创建空列表，用于收集已经解码的数据
        # time.sleep(1)

        for reports in acsii.read_sensor_data():
            # print(reports)
            total_reports += len(reports)       # 循环累加report数量，用于采集率计算。report已经是解码好的数值数据
            all_data.extend(reports)            # 将每一次的report收集起来，用于最后直观展示出来
            if time.time() - start_time > run_duration:     # 如果有测试时间，检查是否达到了测试时间，达到测试时间就停止运行
                break
    finally:
        if 'ser' in locals() and ser.is_open:   # 确保程序结束后关闭串口
            ser.close()
            print("串口已关闭")

        # print出有效的统计数据，方便观察程序的性能
        end_time = time.time()
        duration = end_time - start_time
        sampling_rate = total_reports / duration
        print(f"平均采集率: {sampling_rate:.2f} 个/秒")
        print("\n所有采集到的数值:")
        for i, data in enumerate(all_data, 1):
            print(f"{i}: {data}")