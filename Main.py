# Sensor Logic
# Sensor 1 | Region1  | Sensor 2 | Region 2, Light | Sensor 3 | Region 3 | Sensor 4
# Assuming only one person can fit in regions 1 and 3
import mraa, time
from flask import Flask, request, redirect
import re
from firebase import firebase
import requests
import json
import datetime

def get_stop_time(day_time_start):
    now = datetime.datetime.now()
    time_length = now - day_time_start

    i = 0
    while time_length[i] != ".":
        i += 1

    time_length = time_length[0:i]

    day = (convert_month(now.month) + " " + str(now.day))

    post_info = [day, start, time_length]
    return post_info

def convert_month(num):
    month = ["THE 0TH MONTH", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]

    return month[num]

def post_to_database(day, start, time_length):
    day = str(day)
    daysave = day

    J = [{}]
    J = json.JSONEncoder().encode({"time_on" : start, "duration" : time_length})
    p = requests.post("https://iotresearch-e257a.firebaseio.com/Day/"+daysave+".json", J)

    return J

def parse_data(): #sensor number
    i = 0
    data1 = []
    data2 = []
    data3 = []
    data4 = []
    avg_data1 = 0
    avg_data2 = 0
    avg_data3 = 0
    avg_data4 = 0
    avg_data = []
    while(i < 10):
        d1 = mraa.Aio(0) #reading value from sensor
        d2 = mraa.Aio(1)
        d3 = mraa.Aio(2)
        d4 = mraa.Aio(3)
        data1.append(d1.read()) #reading value from data variable
        data2.append(d2.read())
        data3.append(d3.read())
        data4.append(d4.read())
        i += 1
        time.sleep(.001)

    for x in data1:
        x = int(x)
        avg_data1 = avg_data1 + x
    for x in data2:
        x = int(x)
        avg_data2 = avg_data2 + x
    for x in data3:
        x = int(x)
        avg_data3 = avg_data3 + x
    for x in data4:
        x = int(x)
        avg_data4 = avg_data4 + x
    avg_data.append(avg_data1 / len(data1))
    avg_data.append(avg_data2 / len(data2))
    avg_data.append(avg_data3 / len(data3))
    avg_data.append(avg_data4 / len(data4))

    return avg_data

def main():
    led = mraa.Gpio(13)
    led.dir(mraa.DIR_OUT)
    region1 = False
    region2 = 0
    region3 = False
    light = False
    DIFF = 100

    start = -1
    post = 0


    data_old = parse_data()
    while(1):
        data_new = parse_data() #data from sensors

        #region 1
        if ((data_new[0] - data_old[0]) > DIFF): #20 is the difference in distance, so if theres a jump.
            region1  = not region1
        data_old[0] = data_new[0]

        #region 2
        if ((data_new[1] - data_old[1]) > DIFF): #20 is the difference in distance, so if theres a jump.
            if (region1):
                region2 += 1
                region1 = not region1
            else:
                region2 -= 1
                region1 = not region1
        data_old[1] = data_new[1]

        #region 3
        if ((data_new[2] - data_old[2]) > DIFF): #20 is the difference in distance, so if theres a jump.
            if (region3):
                region2 += 1
                region3 = not region3
            else:
                region2 -= 1
                region3 = not region3
        data_old[2] = data_new[2]

        #region 4
        if ((data_new[3] - data_old[3]) > DIFF): #20 is the difference in distance, so if theres a jump.
            region3  = not region3
        data_old[3] = data_new[3]

        #light
        if (region2 > 0):
            led.write(1) #Turn light on
            if (start == -1):
                start_time = datetime.datetime.now()
                start = 0
            post = -1

        else:
            led.write(0) #turn light off
            if (post == -1):       
                now = datetime.datetime.now()
                time_length = now - start_time

                time_length = str(time_length)
                i = 0
                while time_length[i] != ".":
                    i += 1
                time_length = time_length[0:i]

                start_time = str(start_time)
                i = 0
                while start_time[i] != ".":
                    i += 1

                start_time = start_time[11:i]

                day = (convert_month(now.month) + " " + str(now.day))

                post_info = [day, start_time, time_length]
                post_to_database(post_info[0], post_info[1], post_info[2])
                post = 0
            start = -1

        time.sleep(.001)


if __name__ == "__main__":
    main()
