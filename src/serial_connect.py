"""
展示串口信息，并让操作者进行选择
"""
import serial
import serial.tools.list_ports
import minimalmodbus


class SerialPortManager:
    """
    管理串口连接的类
    """

    def __init__(self):
        """
        初始化SerialPortManager类
        """
        self.available_ports = []
        self.selected_port = None

    def detect_ports(self) -> list:
        """
        检测电脑中可用的串口

        Returns:
            list: 可用串口的列表
        """
        self.available_ports = list(serial.tools.list_ports.comports())
        return self.available_ports

    def print_available_ports(self):
        """
        打印电脑中现有的串口
        """
        if not self.available_ports:
            print("未检测到可用串口")
        else:
            print("可用串口列表：")
            for i, port in enumerate(self.available_ports):
                print(f"{i + 1}. {port.device} - {port.description}")

    def select_port(self) -> str:
        """
        让用户选择一个串口

        ReturnS:
            str: 用户选择的串口名称

        Raises:
            ValueError: 如果用户输入无效
        """
        while True:
            try:
                self.print_available_ports()

                choice = int(input("请选择一个串口（输入对应的数字）："))
                if 1 <= choice <= len(self.available_ports):
                    self.selected_port = self.available_ports[choice - 1].device
                    return self.selected_port
                else:
                    print("无效的选择，请重新输入")
            except ValueError:
                print("请输入有效的数字")


    def select_ports(self) -> list:
        """
        让用户同时选择多个串口

        Returns:
            list: 用户选择的串口名称列表

        Raises:
            ValueError: 如果用户输入无效
        """
        selected_ports = []
        while True:
            self.print_available_ports()
            user_input = input("请输入要选择的串口编号，多个编号用逗号分隔（例如：1,3,5），输入'q'结束选择：")

            if user_input.lower() == 'q':
                break

            try:
                choices = [int(choice.strip()) for choice in user_input.split(',')]
                for choice in choices:
                    if 1 <= choice <= len(self.available_ports):
                        port = self.available_ports[choice - 1].device
                        if port not in selected_ports:
                            selected_ports.append(port)
                    else:
                        print(f"无效的选择：{choice}，已忽略")

                print(f"当前选中的串口：{', '.join(selected_ports)}")
            except ValueError:
                print("请输入有效的数字，并用逗号分隔")

        return selected_ports


def main():
    """
    主函数，用于演示SerialPortManager的使用
    """
    manager = SerialPortManager()
    # 开始选择串口前，必须先检测串口
    manager.detect_ports()

    if manager.available_ports:
        selected_port = manager.select_ports()
        print(f"您选择了串口：{selected_port}")
    else:
        print("没有可用的串口")


if __name__ == "__main__":
    main()
