from machine import *
from display import *
import gc
import time
from smartcar import *
from seekfree import *

# 开发板上的 C19 是拨码开关
end_switch = Pin('C19', Pin.IN, pull=Pin.PULL_UP_47K, value = True)

# # # # # # # # # # # # # # # 无线串口 # # # # # # # # # # # # # 
wireless = WIRELESS_UART(460800)
# # # # # # # # # # # # # # # 无线串口 # # # # # # # # # # # # # 


# # # # # # # # # # # # # # # 按键# # # # # # # # # # # # # # # 
key = KEY_HANDLER(10)
key_a = 0
# # # # # # # # # # # # # # # 按键# # # # # # # # # # # # # # # 

# # # # # # # # # # # # # # # 屏幕# # # # # # # # # # # # # # # 
# 定义控制引脚
rst = Pin('B9' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
dc  = Pin('B8' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
blk = Pin('C4' , Pin.OUT, pull=Pin.PULL_UP_47K, value=1)
drv = LCD_Drv(SPI_INDEX=1, BAUDRATE=60000000, DC_PIN=dc, RST_PIN=rst, LCD_TYPE=LCD_Drv.LCD200_TYPE)
lcd = LCD(drv)
lcd.color(0xFFFF, 0x0000)
lcd.mode(2)
lcd.clear(0x0000)
# # # # # # # # # # # # # # # 屏幕# # # # # # # # # # # # # # # 


# # # # # # # # # # # # # # # 电机# # # # # # # # # # # # # # # 
motor_l = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C25_DIR_C27, 13000, duty = 1, invert = True)
motor_r = MOTOR_CONTROLLER(MOTOR_CONTROLLER.PWM_C24_DIR_C26, 13000, duty = 1, invert = True)
motor_dir = 0
motor_duty = 1500
motor_duty_max = 2000
# # # # # # # # # # # # # # # 电机# # # # # # # # # # # # # # # 


# # # # # # # # # # # # # # # 编码器# # # # # # # # # # # # # # # 
encoder_l = encoder("D0", "D1", True)
encoder_r = encoder("D2", "D3")
encl_data = 0
encr_data = 0
# # # # # # # # # # # # # # # 编码器# # # # # # # # # # # # # # # 


# # # # # # # # # # # # # # # CCD
# 调用 TSL1401 模块获取 CCD 实例
# 参数是采集周期 调用多少次 capture 更新一次数据
# 默认参数为 1 调整这个参数相当于调整曝光时间倍数
ccd = TSL1401(10)
ccd_data1 = ccd.get(0)
ccd_data2 = ccd.get(1)
# # # # # # # # # # # # # # # CCD




# # # # # # # # # # # # # # # 定时中断
# 定义一个回调函数
def time_pit_handler1(time):
    global ticker_flag1
    global ticker_count1
    ticker_flag1 = True
    ticker_count1 = (ticker_count1 + 1) if (ticker_count1 < 100) else (1)
    
def time_pit_handler2(time):
    global ticker_flag2
    global ticker_count2
    ticker_flag2 = True
    ticker_count2 = (ticker_count2 + 1) if (ticker_count2 < 100) else (1)
    
def time_pit_handler3(time):
    global ticker_flag3
    global ticker_count3
    ticker_flag3 = True
    ticker_count3 = (ticker_count3 + 1) if (ticker_count3 < 100) else (1)
    


pit1 = ticker(1)
pit1.capture_list(ccd)
pit1.callback(time_pit_handler1)
pit1.start(5)

pit2 = ticker(2)
pit2.capture_list(encoder_l, encoder_r)
pit2.callback(time_pit_handler2)
pit2.start(2)


pit3 = ticker(0)
pit3.capture_list(key)
pit3.callback(time_pit_handler3)
pit3.start(10)
# # # # # # # # # # # # # # # 定时中断


# 需要注意的是 ticker 是底层驱动的 这导致 Thonny 的 Stop 命令在这个固件版本中无法停止它
# 因此一旦运行了使用了 ticker 模块的程序 要么通过复位核心板重新连接 Thonny
# 或者像本示例一样 使用一个 IO 控制停止 Ticker 后再使用 Stop/Restart backend 按钮
ticker_flag1 = False
ticker_count1 = 0
runtime_count1 = 0
ticker_flag2 = False
ticker_count2 = 0
runtime_count2 = 0
ticker_flag3 = False
ticker_count3 = 0
runtime_count3 = 0


while True:
    if (ticker_flag1):
        ccd_data1 = ccd.get(0)
        ccd_data2 = ccd.get(1)
        wireless.send_ccd_image(WIRELESS_UART.CCD1_BUFFER_INDEX)
        #wireless.send_ccd_image(WIRELESS_UART.CCD2_BUFFER_INDEX)
    # # # # # # # # # # # # # V
    if (ticker_flag2):
        if motor_dir == 1 and motor_duty > 0:
            motor_duty = motor_duty
        if motor_dir == 0 and motor_duty > 0:
            motor_duty = -motor_duty
        motor_l.duty(motor_duty)
        motor_r.duty(motor_duty)
        encl_data = encoder_l.get()
        encr_data = encoder_r.get()
    # # # # # # # # # # # # # V
    if (ticker_flag3):
        key_data = key.get()
        # 按键数据为三个状态 0-无动作 1-短按 2-长按
        if key_data[0]:
            key_a = 1
            key.clear(1)
        if key_data[1]:
            key_a = 2
            key.clear(2)
        if key_data[2]:
            key_a = 3
            key.clear(3)
        if key_data[3]:
            key_a = 4
            key.clear(4)
        
        ticker_flag = False
    # # # # # # # # # # # # # V
    
    lcd.str16(0,130,"encoder_l={:>3d}.".format(encl_data),0xFFFF)
    lcd.str16(0,146,"encoder_r={:>3d}.".format(encr_data),0xFFFF)
    lcd.str16(0,162,"key={:>3d}.".format(key_a),0xFFFF)
    lcd.wave(0,  0, 128, 64, ccd_data1)
    lcd.wave(0, 64, 128, 64, ccd_data2)
    gc.collect()
    if end_switch.value() == 0:
        pit1.stop()
        pit2.stop()
        pit3.stop()
        lcd.clear()
        break









 
