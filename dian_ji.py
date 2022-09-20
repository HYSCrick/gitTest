import RPi.GPIO as GPIO
import time
import numpy as np
import requests
import json
import os
import sys
import serial
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # 解决zookeeper 连接问题
sys.path.append(BASE_DIR)                               # 同上
from kazoo.client import KazooClient

#连接检测
def isConnected():
    try:
        html1 = requests.get("http://www.baidu.com", timeout=1)
    except:
        return False
    return True
#获取zookeeper连接
def getZk():
    global zk
    try:
        zk=KazooClient(hosts='43.138.176.76:2181',command_retry=20, connection_retry=20, timeout=60000);
    except:
        print("zookeeper error")
#发送数据
def trans_data_to_app(wavelength, target_spectrum, white_reference_spectrum, black_reference_spectrum): #data为list类型
    headers = {'Content-Type': 'application/json'} # headers中添加上content-type这个参数，指定为json格式
    dict_data={'wavelength' : wavelength,
               'target_spectrum' : target_spectrum,
               'white_reference_spectrum1' : white_reference_spectrum,
               'black_reference_spectrum' : black_reference_spectrum
               }
    ret = requests.post(url=reUrl+'/update-data', headers=headers, data=json.dumps(dict_data)).text
    print(ret)
    return ret
 #更新检测结果
def update_detect_result():       
    target_spectrum = []  # equals to 2048 * number of target，光谱数据
    with open(spectrum_path,'r') as f:
        for line in f:
            target_spectrum.append(round(float(line.strip()), 4))
            
    wavelength = []       # equals to 2048，波长数据
    with open(wavelength_path,'r') as f:
        for line in f:
            wavelength.append(round(float(line.strip()), 4))
    white_reference_spectrum = []  # equals to 2048
    black_reference_spectrum = []  # equals to 2048
    reference_tmp = []    # equals to 2048*3
    with open(reference_path,'r') as f:
        for line in f:
            reference_tmp.append(round(float(line.strip()), 4))

    #处理并整合数据
    white_reference_spectrum = reference_tmp[2048 : 2048*2]
    black_reference_spectrum = reference_tmp[2048*2 : 2048*3]
    #发送监测数据
    trans_data_to_app(wavelength, target_spectrum, white_reference_spectrum, black_reference_spectrum)
    del wavelength, target_spectrum, white_reference_spectrum, black_reference_spectrum   #发完就删，等下一波进来
#新版更新检测结果-----hys修改
def hys_update_detect_result():
    target_spectrum1 = []  
    with open(spectrum_path1,'r') as f:   #处理幅值1数据
        for line in f:
            temp = line.split(',')
    for i in temp:
        target_spectrum1.append(round(float(i.strip()), 4))
    target_spectrum2 = []  
    with open(spectrum_path2,'r') as f:   #处理幅值2数据
        for line in f:
            temp = line.split(',')
    for i in temp:
        target_spectrum2.append(round(float(i.strip()), 4))

    wavelength = []       # equals to 2048  处理波长数据
    with open(wavelength_path,'r') as f:
        for line in f:
            temp = line.split(',')
    for i in temp:
        wavelength.append(round(float(i.strip()), 4))
    white_reference_spectrum = []  # equals to 2048，
    black_reference_spectrum = []  # equals to 2048
    reference_tmp = []    # equals to 2048*3
    with open(reference_path,'r') as f:
        for line in f:
            reference_tmp.append(round(float(line.strip()), 4))

    
    #white_reference_spectrum = reference_tmp[2048 : 2048*2]
    black_reference_spectrum = reference_tmp[2048*2 : 2048*3]
    #发送监测数据
    trans_data_to_app(wavelength, target_spectrum1, target_spectrum2, black_reference_spectrum)
    del wavelength, target_spectrum1, target_spectrum2, black_reference_spectrum   #发完就删，等下一波
#初始化GPIO
def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TERMINAL1, 0)
    GPIO.setup(TERMINAL2, 0)
# 设置电机旋转方向
def set_direction(direction=1):
    GPIO.output(TERMINAL2, direction) 
#控制电机    
def Set_RoataionAngle(AngleNum=0):
    for x in range(0,AngleNum):
        if x%2 == 0:
            GPIO.output(TERMINAL1, 1)
        else:
            GPIO.output(TERMINAL1, 0)
        time.sleep(0.0005)              #too fast,need to add more time.sleep
#检测
def Detect_action():
    n=0
    while(n<2):                #160*10=1600,gang hao yi quan
        os.system("sudo /home/pi/Desktop/dianji/avs_amplitude %s %d " % (check_path,n))   # 采集光谱仪的幅值信息
        #金标定
        time.sleep(2)
        if(n>0):
            ck1 = []
            ck2 = []
            t_path = check_path + "/amplitude_%d.txt"%(n)
            t_path0 = check_path + "/amplitude_0.txt"
            # 测试文件权限 如文件权限不足，则会跳过该段代码
            #with open("/home/pi/Desktop/dianji_tempFile/test_2.txt","w") as f:
             #   f.write(t_path)
              #  f.close()
            with open(t_path, "r") as f:
                for line in f:
                    ck1_t = line.split(',')            
            for i in ck1_t:
                ck1.append(float(i))
            with open(t_path0, "r") as f:
                for line in f:
                    ck2_t = line.split(',')
            for i in ck2_t:
                ck2.append(float(i))

            dd = np.array(ck1) - np.array(ck2)
            dd2 = []
            for i in dd:
                dd2.append(str(i))
                dd2.append(',')
            dd2.pop()
            t_path1 = temp_file_path + "amplitude_%d.txt"%(n)
            with open(t_path1,"w") as f:
                for i in dd2:
                    f.write(i)
                f.close()
            os.system("sudo cp -f " + t_path1 + " " + check_path)
            Set_RoataionAngle(3200-640)
        Set_RoataionAngle(320)   #320/2=160ge mai chong zhou qi
    
        time.sleep(1)
        n=n+1
    

#spectrum_path='fuzhi.txt'
#wavelength_path='bochang.txt'
reference_path='/home/pi/Desktop/dianji/Light_Dark.txt'

reUrl = "http://43.138.176.76"
zk=None
TERMINAL1 = 38 # PUL +
TERMINAL2 = 35 # DIR +

os.system("sudo /home/pi/Desktop/dianji/avs_length")       # 采集光谱仪的波长范围信息，只需调用一次即可

temp_file_path = "/home/pi/Desktop/dianji_tempFile/" # 文件复制路径

# 检测是否连网
while not isConnected():   
    pass
#requests.get(reUrl+"/jx-app-order/reset-order").content.decode('UTF-8')
#注意，在这里提取了一次检测结果
getZk()
zk.start()
#zk.create('/jx',ephemeral=False)
##若第一次建立该服务器，则需要运行该代码     #zk.create('/jx/01/',ephemeral=True)   # 创建对应节点
#spectrum_path='/home/pi/Desktop/dianji/Info/1/1/amplitude_1.txt'
#wavelength_path='/home/pi/Desktop/dianji/Info/wavelength.txt'
#hys_update_detect_result()

 
if __name__ == '__main__':     # Program start from here
    setup()
    #GPIO.output(Light, 1)
    n=1;
    username = sys.argv[1]      #username
    check_time = sys.argv[2]    #check time,1 or 2
    check_path = "/home/pi/Desktop/dianji/Info/" + username + "/" + check_time

    
    os.system("sudo mkdir -p /home/pi/Desktop/dianji/Info/%s/%s" % (username,check_time))
    
    try:
        node = zk.get_children('/jx')
        if "01" not in node:
            zk.create('/jx/01',ephemeral=True)
            print(node)
    except:
        print("zookeeper net error")
    pass
    Detect_action()
    if check_time == "2":
        spectrum_path1 = "/home/pi/Desktop/dianji/Info/" + username + "/" + "1/" +  "amplitude_1.txt"
        spectrum_path2 = "/home/pi/Desktop/dianji/Info/" + username + "/" + "2/" +  "amplitude_1.txt"
        wavelength_path='/home/pi/Desktop/dianji/Info/wavelength.txt'
        hys_update_detect_result()
    GPIO.cleanup()

