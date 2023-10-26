# receive_data.py
# receive serial data from mc and save it to csv

# proposed path: /usr/bin/env python3
# serial code credit to The Robotics Back-End
# https://roboticsbackend.com/raspberry-pi-arduino-serial-communication/

import serial
import datetime
import time
import os, threading
import glob

# er shell command to use uhubctl: sudo uhubctl -l 1-1 -a 1/0
def toggleUSBBus(onOrOff):
  binaryOnOff = "1" if onOrOff else "0"
  os.system("sudo uhubctl -l 1-1 -a " + binaryOnOff)

def monitorQuit():
  while 1:
    sentence = input()
    if sentence == "exit" or sentence == "quit":
      # turn USB bus on
      toggleUSBBus(True)
      os.kill(os.getpid(),9)

if __name__ == '__main__':
  # ensure USB bus on
  toggleUSBBus(True)

  # setup quit monitor to reopen USB bus on quit
  monitor = threading.Thread(target=monitorQuit)
  monitor.start()

  proj_path = "/home/pi/st_pi/"

  # values for operating time here:
  start_hour = 21  # 9 pm
  end_hour = 9  # 9 am

  while True:
    # turn USB bus back on
    toggleUSBBus(True)

    # initialize serial communication with Arduino UNO
    dev_list = glob.glob("/dev/tty*")
    dev_path = ""
    for device in dev_list:
      if "ACM" in device:
        dev_path = device
        break
    if dev_path == "":  # if didn't find port
      print("Couldn't find Arduino device to communicate with; terminating")
      os.kill(os.getpid(),9)  # kill process

    # expect every 10s
    ser = serial.Serial(dev_path, 9600, timeout=15)
    ser.reset_input_buffer()
    current_hour = datetime.datetime.now().hour
    csv_lines = ["time,x,y,temp\n"]

    # operating hours from start_hour to end_hour
    while current_hour >= start_hour or current_hour < end_hour:
      current_hour = datetime.datetime.now().hour
      if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        print(line)
        point_time = datetime.datetime.now().strftime("%X")  # HH:MM:SS
        csv_lines.append(point_time + line.split(" ").join(",") + "\n")

    # with sleep sensing period done, turn off port and halt until next period
    # turn off usb port to arduino
    toggleUSBBus(False)

    # write to file
    fname = "sleepdata_"
    fname += str(datetime.datetime.now().month) + "-"
    fname += str(datetime.datetime.now().day) + "-"
    fname += str(datetime.datetime.now().year)
    fp = open(proj_path + fname, "w+")  # create and open
    fp.writelines(csv_lines)
    fp.close()

    # sleep until next night sensing period
    while not (current_hour >= start_hour or current_hour < end_hour):
      t = datetime.datetime.now()
      current_hour = t.hour
      print("sleeping")
      time.sleep(10)
      # sleep_for_s = (start_hour * 3600) - (t.hour * 3600) - (t.minute * 60) - t.second
      # print("sleeping for " + str(sleep_for_s) + " seconds")
      # time.sleep(sleep_for_s)
