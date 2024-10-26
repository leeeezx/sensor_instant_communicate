# test
test文件夹下所有.py文件的说明  

## test_GUI
测试图形化界面

## test_of_hex
关于模式3hex快速发送模式的测试程序

## test_of_ascii
关于模式2ascii主动发送协议的测试程序


## test_of_modbus
关于**modbus模式**下的测试程序

### CRC
自动计算crc16校验码

### test_modbus_03
测试modbus03读命令  
**测试进度**:  
20241023
1. 对modbus-slave软件从机有效。受限于软件设置，无法实时变化寄存器中的数值，等于传感器数值固定
2. 测试采集速率，寄存器设置为2时，有50hz左右，数据正常。  
但是寄存器数目修改之后，无法正常读取数据。  
一个仪表的测量值只有两个寄存器，不能修改寄存器数目。  

**重点**：如何加快采集速率，目前采集速率只有60hz。条件：包间隔0.001，波特率115200，  
GPT说理论最大采集频率有404hz。

### faster_sample_rate+0x
带有该名称的.py文件都是为了测试如何提高采集率。  
01是在程序中也控制了对应的包间隔时间
02文件是基于minimalmodbus改进  
03是替换为minimalmodbus自带的read_float

### test_single_time
单次发送接收时间测试