"""
crc校验
"""
import struct


# 假设这些函数已经在其他地方定义
def _check_bytes(data, description):
    if not isinstance(data, bytes):
        raise TypeError(f"{description} must be of type bytes.")


def _num_to_two_bytes(value, lsb_first=True):
    if lsb_first:
        return struct.pack('<H', value)
    return struct.pack('>H', value)


# CRC16 查找表
_CRC16TABLE = (
    0,
    49345,
    49537,
    320,
    49921,
    960,
    640,
    49729,
    50689,
    1728,
    1920,
    51009,
    1280,
    50625,
    50305,
    1088,
    52225,
    3264,
    3456,
    52545,
    3840,
    53185,
    52865,
    3648,
    2560,
    51905,
    52097,
    2880,
    51457,
    2496,
    2176,
    51265,
    55297,
    6336,
    6528,
    55617,
    6912,
    56257,
    55937,
    6720,
    7680,
    57025,
    57217,
    8000,
    56577,
    7616,
    7296,
    56385,
    5120,
    54465,
    54657,
    5440,
    55041,
    6080,
    5760,
    54849,
    53761,
    4800,
    4992,
    54081,
    4352,
    53697,
    53377,
    4160,
    61441,
    12480,
    12672,
    61761,
    13056,
    62401,
    62081,
    12864,
    13824,
    63169,
    63361,
    14144,
    62721,
    13760,
    13440,
    62529,
    15360,
    64705,
    64897,
    15680,
    65281,
    16320,
    16000,
    65089,
    64001,
    15040,
    15232,
    64321,
    14592,
    63937,
    63617,
    14400,
    10240,
    59585,
    59777,
    10560,
    60161,
    11200,
    10880,
    59969,
    60929,
    11968,
    12160,
    61249,
    11520,
    60865,
    60545,
    11328,
    58369,
    9408,
    9600,
    58689,
    9984,
    59329,
    59009,
    9792,
    8704,
    58049,
    58241,
    9024,
    57601,
    8640,
    8320,
    57409,
    40961,
    24768,
    24960,
    41281,
    25344,
    41921,
    41601,
    25152,
    26112,
    42689,
    42881,
    26432,
    42241,
    26048,
    25728,
    42049,
    27648,
    44225,
    44417,
    27968,
    44801,
    28608,
    28288,
    44609,
    43521,
    27328,
    27520,
    43841,
    26880,
    43457,
    43137,
    26688,
    30720,
    47297,
    47489,
    31040,
    47873,
    31680,
    31360,
    47681,
    48641,
    32448,
    32640,
    48961,
    32000,
    48577,
    48257,
    31808,
    46081,
    29888,
    30080,
    46401,
    30464,
    47041,
    46721,
    30272,
    29184,
    45761,
    45953,
    29504,
    45313,
    29120,
    28800,
    45121,
    20480,
    37057,
    37249,
    20800,
    37633,
    21440,
    21120,
    37441,
    38401,
    22208,
    22400,
    38721,
    21760,
    38337,
    38017,
    21568,
    39937,
    23744,
    23936,
    40257,
    24320,
    40897,
    40577,
    24128,
    23040,
    39617,
    39809,
    23360,
    39169,
    22976,
    22656,
    38977,
    34817,
    18624,
    18816,
    35137,
    19200,
    35777,
    35457,
    19008,
    19968,
    36545,
    36737,
    20288,
    36097,
    19904,
    19584,
    35905,
    17408,
    33985,
    34177,
    17728,
    34561,
    18368,
    18048,
    34369,
    33281,
    17088,
    17280,
    33601,
    16640,
    33217,
    32897,
    16448,
)
r"""CRC-16 lookup table with 256 elements.

Built with this code::

    poly=0xA001
    table = []
    for index in range(256):
        data = index << 1
        crc = 0
        for _ in range(8, 0, -1):
            data >>= 1
            if (data ^ crc) & 0x0001:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
        table.append(crc)
    output = ''
    for i, m in enumerate(table):
        if not i%11:
            output += "\n"
        output += "{:5.0f}, ".format(m)
    print output
"""


def _calculate_crc(inputbytes: bytes) -> bytes:
    """Calculate CRC-16 for Modbus RTU."""
    _check_bytes(inputbytes, description="CRC input bytes")
    register = 0xFFFF
    for current_byte in inputbytes:
        register = (register >> 8) ^ _CRC16TABLE[(register ^ current_byte) & 0xFF]
    return _num_to_two_bytes(register, lsb_first=True)


# 模拟主站发送 Modbus 03 命令
def send_modbus_03_command(slave_address, start_register, register_count):
    # 构建命令（不包含CRC）
    command = struct.pack('>BBHH', slave_address, 0x03, start_register, register_count)

    # 计算CRC
    crc = _calculate_crc(command)

    # 将CRC添加到命令末尾
    full_command = command + crc

    print(f"发送的完整命令: {full_command.hex()}")
    return full_command


# 模拟从站接收并验证 Modbus 03 命令
def receive_and_verify_modbus_03_command(received_data):
    if len(received_data) != 8:  # Modbus 03 命令固定长度为8字节
        print("接收到的数据长度不正确")
        return False

    # 分离命令和接收到的CRC
    command = received_data[:6]
    received_crc = received_data[6:]

    # 重新计算CRC
    calculated_crc = _calculate_crc(command)

    # 比较计算得到的CRC和接收到的CRC
    if calculated_crc == received_crc:
        print("CRC校验通过，命令有效")
        return True
    else:
        print("CRC校验失败，命令无效")
        return False


# 示例使用
if __name__ == "__main__":
    # 主站发送命令
    slave_address = 1
    start_register = 0
    register_count = 2

    sent_command = send_modbus_03_command(slave_address, start_register, register_count)

    # 模拟数据传输（这里我们直接使用发送的命令，实际中可能会有传输错误）
    received_command = sent_command

    # 从站接收并验证命令
    is_valid = receive_and_verify_modbus_03_command(received_command)

    if is_valid:
        print("从站可以处理该命令")
    else:
        print("从站将忽略该命令")
