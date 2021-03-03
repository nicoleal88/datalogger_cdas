#!/usr/bin/python2

# Prints raw data and events in files, and periodic updates on screen (Every [delay] seconds)

import argparse
import time
import serial
import os
import glob
import subprocess

# Configure paths
userHome = os.getenv("HOME")
softPath = userHome + '/homeOffice/CDAS/datalogger_cdas/software/'
dataPath = userHome + '/homeOffice/CDAS/datalogger_cdas/data/'

# Read configFile
config = {}
with open(softPath + 'configFile.conf','r') as f:
  File = f.readlines()
  for lines in File:
    splittedLine = lines.split('=')
    if len(splittedLine) == 2:
      config[splittedLine[0]] = splittedLine[1][:-1]

building = config['BUILDING'] 

# Make root folder
try:
  os.mkdir(dataPath+building)
except:
  pass

# Parsing
parser = argparse.ArgumentParser()
parser.add_argument("delay", type = int, nargs = '?', default = config['DELAY'] , help = "Delay between data printing [seconds]")
args = parser.parse_args()

### Serial port configuration
ser = serial.Serial()
ser.baudrate = 115200
ser.timeout = 1.0

def getSerialPort():
  try:
    ports = glob.glob(config['PORT'])
    port = ports[0]
    sttyCommand = "stty -F " + port + " 115200 -raw"
    subprocess.call(sttyCommand, shell=True)
  except serial.serialutil.SerialException:
    print ('No se encuentra puerto'+ config['PORT'])
  except IndexError:
    print ('No se encuentra puerto'+ config['PORT'])
  return port

ser.port = getSerialPort()
ser.open()

# Global variables declarations
msTime = 0
A0 = 0
A1 = 0
A2 = 0
A3 = 0
A4 = 0
A5 = 0
A6 = 0
A7 = 0
A8 = 0
A9 = 0
A10 = 0
A11 = 0
fr = 0

def getDataFromSerial(line):
  if len(line) > 0:
    # print (line)
    A0Offset = ord(line[0])
    A1Offset = ord(line[1])
    A2Offset = ord(line[2])
    A3Offset = ord(line[3])
    A4Offset = ord(line[4])
    A5Offset = ord(line[5])
    A6Offset = ord(line[6])
    deltaNOffset  = ord(line[7])
    indexA06fLSB = ord(line[8])
    indexA06fMSB = ord(line[9])
    A7Offset = ord(line[10])
    A8Offset = ord(line[11])
    A9Offset = ord(line[12])
    A10Offset = ord(line[13])
    indexA710 = ord(line[14])
    A11_low = ord(line[15])
    A11_up = ord(line[16])
        
    indexA06f = indexA06fLSB | (indexA06fMSB << 8)
       
    A0Index = indexA06f & (2**2 - 2**0)
    A1Index = (indexA06f & (2**4 - 2**2)) >> 2
    A2Index = (indexA06f & (2**6 - 2**4)) >> 4
    A3Index = (indexA06f & (2**8 - 2**6)) >> 6
    A4Index = (indexA06f & (2**10 - 2**8)) >> 8
    A5Index = (indexA06f & (2**12 - 2**10)) >> 10
    A6Index = (indexA06f & (2**14 - 2**12)) >> 12
    deltaNIndex = (indexA06f & (2**16 - 2**14)) >> 14
        
    A0_ADC = A0Offset + 256 * A0Index
    A1_ADC = A1Offset + 256 * A1Index
    A2_ADC = A2Offset + 256 * A2Index
    A3_ADC = A3Offset + 256 * A3Index
    A4_ADC = A4Offset + 256 * A4Index
    A5_ADC = A5Offset + 256 * A5Index
    A6_ADC = A6Offset + 256 * A6Index
    deltaN  = deltaNOffset  + 256 * deltaNIndex
    
    A7Index = indexA710 & (2**2 - 2**0)
    A8Index = (indexA710 & (2**4 - 2**2)) >> 2
    A9Index = (indexA710 & (2**6 - 2**4)) >> 4
    A10Index = (indexA710 & (2**8 - 2**6)) >> 6

    A7_ADC = A7Offset + 256 * A7Index
    A8_ADC = A8Offset + 256 * A8Index
    A9_ADC = A9Offset + 256 * A9Index
    A10_ADC = A10Offset + 256 * A10Index

    A11_ADC = A11_low | (A11_up << 8)

    global msTime    
    msTime = str(int((time.time()*1000)))

    # Values conversion
    global A0
    global A1
    global A2
    global A3
    global A4
    global A5
    global A6
    global A7
    global A8
    global A9
    global A10
    global A11
    convFactor_A0 = float(config['CONVFACTOR_A0'])		# Conversion factor
    convFactor_A1 = float(config['CONVFACTOR_A1'])
    convFactor_A2 = float(config['CONVFACTOR_A2'])
    convFactor_A3 = float(config['CONVFACTOR_A3'])
    convFactor_A4 = float(config['CONVFACTOR_A4'])
    convFactor_A5 = float(config['CONVFACTOR_A5'])
    convFactor_A6 = float(config['CONVFACTOR_A6'])
    convFactor_A7 = float(config['CONVFACTOR_A7'])
    convFactor_A8 = float(config['CONVFACTOR_A8'])
    convFactor_A9 = float(config['CONVFACTOR_A9'])
    convFactor_A10 = float(config['CONVFACTOR_A10'])
    convFactor_A11 = float(config['CONVFACTOR_A11'])

    A0 = A0_ADC * convFactor_A0
    A1 = A1_ADC * convFactor_A1
    A2 = A2_ADC * convFactor_A2
    A3 = A3_ADC * convFactor_A3
    A4 = A4_ADC * convFactor_A4
    A5 = A5_ADC * convFactor_A5
    A6 = A6_ADC * convFactor_A6
    A7 = A7_ADC * convFactor_A7
    A8 = A8_ADC * convFactor_A8
    A9 = A9_ADC * convFactor_A9
    A10 = A10_ADC * convFactor_A10
    A11 = A11_ADC * convFactor_A11
    
    global fr
    fr = 2000/((4608-deltaN)/102.4)
    # fr = deltaN

def avgList(myList):
  return sum(myList) / float(len(myList))

def trigger():
  flag = False
  items = [A0List, A1List, A2List, A7List]	# Items to be checked

  for i in items:
    if abs(i[position] - i[position-1]) > vThreshold:
      flag = True
  
  return flag

# Variables
nzLast = 0
msTimeLast = 0

A0List = []			# buffer list for events log
A1List = []
A2List = []
A3List = []
A4List = []
A5List = []
A6List = []
A7List = []
A8List = []
A9List = []
A10List = []
A11List = []
frList = []

timeBufferLength = 16000			# Amount of time saved in the buffers[ms]
linePeriod = 32					# Line typical period [ms]
listLength = timeBufferLength/linePeriod	# Buffer length (10 seconds, 10000ms)
position = 100					# Position in buffer where events are detected
dataDelay = (listLength) * linePeriod 		# (20 = 10000ms/500)
i1 = 0				
printN = 0					# Remaining lines to print in events file
event = 0					# Event counter

NOISE_A0 = int(config['NOISE_TRIGGER_A0'])	# Noise trigger for A0 port
NOISE_A1 = int(config['NOISE_TRIGGER_A1'])	# Noise trigger for A1 port
NOISE_A2 = int(config['NOISE_TRIGGER_A2'])	# Noise trigger for A2 port
NOISE_A3 = int(config['NOISE_TRIGGER_A3'])	# Noise trigger for A3 port
NOISE_A4 = int(config['NOISE_TRIGGER_A4'])	# Noise trigger for A4 port
NOISE_A5 = int(config['NOISE_TRIGGER_A5'])	# Noise trigger for A5 port
NOISE_A6 = int(config['NOISE_TRIGGER_A6'])	# Noise trigger for A6 port
NOISE_A7 = int(config['NOISE_TRIGGER_A7'])	# Noise trigger for A7 port
NOISE_A8 = int(config['NOISE_TRIGGER_A8'])	# Noise trigger for A8 port
NOISE_A9 = int(config['NOISE_TRIGGER_A9'])	# Noise trigger for A9 port
NOISE_A10 = int(config['NOISE_TRIGGER_A10'])	# Noise trigger for A10 port
NOISE_A11 = int(config['NOISE_TRIGGER_A11'])	# Noise trigger for A11 port
NOISE_F = int(config['NOISE_TRIGGER_F'])	# Noise trigger for fr
vThreshold = int(config['THRESHOLD_A0'])	# Voltage difference required to trigger an event
vNoiseFilter = -1				# Voltage below this value is considered noise
printFlag = False				# Allows saving events
errorFlag = False				# Avoids events after serial error

while True:
  try:
    if ser.isOpen() == True:
      if errorFlag == False:
        serialLine = ser.readline()
      else:
        errorFlag = False
        pass
      # Data reading
      getDataFromSerial(serialLine)
      # Data lists
      if i1 > listLength:
        A0List.pop(0)
        A1List.pop(0)
        A2List.pop(0)
        A3List.pop(0)
        A4List.pop(0)
        A5List.pop(0)
        A6List.pop(0)
        A7List.pop(0)
        A8List.pop(0)
        A9List.pop(0)
        A10List.pop(0)
        A11List.pop(0)
        frList.pop(0)
      else:
        i1 += 1
      if A0 > NOISE_A0:
        A0List.append(A0)
      else:
        A0List.append(-1)
      if A1 > NOISE_A1:
        A1List.append(A1)
      else:
        A1List.append(-1)
      if A2 > NOISE_A2:
        A2List.append(A2)
      else:
        A2List.append(-1)
      if A3 > NOISE_A3:
        A3List.append(A3)
      else:
        A3List.append(-1)
      if A4 > NOISE_A4:
        A4List.append(A4)
      else:
        A4List.append(-1)
      if A5 > NOISE_A5:
        A5List.append(A5)
      else:
        A5List.append(-1)
      if A6 > NOISE_A6:
        A6List.append(A6)
      else:
        A6List.append(-1)
      if A7 > NOISE_A7:
        A7List.append(A7)
      else:
        A7List.append(-1)
      if A8 > NOISE_A8:
        A8List.append(A8)
      else:
        A8List.append(-1)
      if A9 > NOISE_A9:
        A9List.append(A9)
      else:
        A9List.append(-1)
      if A10 > NOISE_A10:
        A10List.append(A10)
      else:
        A10List.append(-1)
      if A11 > NOISE_A11:
        A11List.append(A11)
      else:
        A11List.append(-1)
      if fr > NOISE_F:
        frList.append(fr)
      else:
        frList.append(-1)

      # Log writing and Screen printing (Periodic data every Delay seconds)
      if int(msTime) >= (int(msTimeLast) + (args.delay * 1000)):
        logInfo = "%.d \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.d \n"  % (int(msTime), A0List[-1], A1List[-1], A2List[-1], A3List[-1], A4List[-1], A5List[-1], A6List[-1], fr, A7List[-1], A8List[-1], A9List[-1], A10List[-1], A11List[-1], event)

        # Make year folder
        try:
          yearFolder = dataPath + building + '/' + time.strftime("%Y")
          os.mkdir(yearFolder)
        except:
          pass	# print 'Error making year folder'

        # Make month folder
        try:
          monthFolder = yearFolder + '/' + time.strftime("%m")
          os.mkdir(monthFolder)
        except:
          pass	# print 'Error making month folder'

        logFilePath = monthFolder + '/' + time.strftime("%Y-%m-%d") + '-' + building.upper() + '.tsv'

        with open(logFilePath,'a') as f:
          f.write(logInfo)
        
        hour = time.strftime("%d/%m/%Y - %H:%M:%S")

        print (logInfo)

        msTimeLast = msTime
      else:
        pass
       
      # Event writing (Prints data every 500us when an event occurs)
      # Event detection
      if trigger() and i1 == listLength and printN == 0:
        printFlag = eval(config['SAVE_EVENTS'])        ##################  Habilitar para guardar eventos!!! #####################
        printN = listLength
        event += 1
      else:
        pass
          # Event writing
      if printFlag == True and printN > 0:
        eventInfo = "%.d \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.d \t %.d \n"  % ((int(msTime) - dataDelay), A0List[0], A1List[0], A2List[0], A3List[0], A4List[0], A5List[0], A6List[0], frList[0], A7List[0], A8List[0], A9List[0], A10List[0], A11List[0], event, printN)

        with open(logFilePath,'a') as f:
          f.write(eventInfo)
        printN -= 1
      else:
        printFlag = False

    else:
      try:
        ser.port = getSerialPort()
        ser.open()
        print ("Trying to open serial port")
      except serial.serialutil.SerialException:
        print ('Buscando puerto' + config['PORT'])
        time.sleep(5)
      except IndexError:
        pass
      
  except IndexError:
    pass
  except ValueError:
    pass
  except serial.serialutil.SerialException:
    print ('Serial Error!')
    errorFlag = True
    errorInfo = "Serial Error - %s \n"  % (hour)

    errorFilePath = 'error_' + building.upper() + time.strftime("%Y-%m-%d") + '.dat'
    with open(errorFilePath,'a') as f:
      f.write(errorInfo)

    ser.close()
    try:
      time.sleep(5)
      ser.port = getSerialPort()
      ser.open()
      pass
    except IndexError:
      pass
  except KeyboardInterrupt:
    print ('\n')
    print ("Exiting..." + '\n')
    break 
