import serial
import time
import os

ZERO_READING = 0
INTERVAL_PER_AMP = 46/11

ser = serial.Serial("COM5", 9600)
path = base_name = 'reading.csv'

if not os.path.exists(base_name):
    base_name
else:
    filename, extension = os.path.splitext(base_name)
    counter = 1
    while True:
        new_path = f"{filename} ({counter}){extension}"
        if not os.path.exists(new_path):
            path = new_path
            break
        counter += 1
            

file = open(path, "w")

data = ''
start_time = time.time()
count = 0

while True:
    value = ser.readline().decode().strip()
    print(value)
    current = (int(value) - ZERO_READING) / INTERVAL_PER_AMP

    time_passed = int((time.time() - start_time) * 1000)
    
    print('Time:{}ms\tReading:{}\tCurrent:{}'.format(time_passed, value, current))
    data += '{},{}\n'.format(time_passed, value)
    count += 1

    if count%10 == 0:
        file.write(data)
        file.flush()
        file.close()
        file = open(path, 'w')
        print('Reading saved')
                
file.close()

