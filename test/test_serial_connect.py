"""
python调用串口程序尝试
最终目的，调用PC串口接收、修改传感器中的参数。
这个test里，需要熟悉，调用PC串口，使用PC串口发送数据，接收数据，设置数据格式
"""
import time
import serial
import serial.tools.list_ports

ports_list = list(serial.tools.list_ports.comports())
if len(ports_list) <= 0:
    print("无串口设备。")
else:
    print("可用的串口设备如下：")
    for comport in ports_list:
        print(comport.device, comport.description)

# print("断点专用")
# 设置串口1参数然后打开，检查是否打开成功，
try:
    # 假设我们使用第一个可用的串口
    if ports_list:
        port = input("输入想要设置并打开的串口号（标准格式：COM+数字）：")
        # 设置串口参数
        ser = serial.Serial(
            port=port,
            baudrate=9600,  # 波特率
            bytesize=serial.EIGHTBITS,  # 数据位
            parity=serial.PARITY_NONE,  # 校验位
            stopbits=serial.STOPBITS_TWO,  # 停止位
            timeout=None  # 读取超时设置
        )

        if ser.is_open:
            print(f"串口 {port} 已成功打开")
            print(f"串口参数：{ser.get_settings()}")
        else:
            print(f"串口 {port} 打开失败")

        # 发送数据
        ser.write(b'Hello, Serial Port!')
        # 接收数据
        # received_data = ser.read(10)  # 读取10个字节
        # print(f"接收到的数据: {received_data}")

        time.sleep(1)
        ser.close()
        print("串口已关闭")
    else:
        print("没有可用的串口")
except serial.SerialException as e:
    print(f"打开串口时发生错误: {e}")
#-------------------------------------测试成功------------------------------------

# 接下来测试，串口接收信息功能

# ---------------------------------------------------

# 持续发送



