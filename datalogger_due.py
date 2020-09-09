#!/usr/bin/python2

#Prints raw data and events in files, and periodic updates on screen (Every [delay] seconds)

import argparse
import time
import serial
import os
import glob
import subprocess

#Configure paths
'''
/home/USER
/home/USER/datalogger/software
/home/USER/datalogger/data
'''
userHome = os.getenv("HOME")
softPath = userHome + '/datalogger/software/'
dataPath = userHome + '/datalogger/data/'

#Read configFile
config = {}
with open(softPath + 'configFile.conf','r') as f:
  File = f.readlines()
  for lines in File:
    splittedLine = lines.split('=')
    if len(splittedLine) == 2:
      config[splittedLine[0]] = splittedLine[1][:-1]

building = config['BUILDING'] 

#Make root folder
try:
  os.mkdir(dataPath+building)
except:
  pass

#Parsing
parser = argparse.ArgumentParser()
parser.add_argument("delay", type = int, nargs = '?', default = config['DELAY'] , help = "Delay between data printing [seconds]")
args = parser.parse_args()

###Serial port configuration
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

#Global variables declarations
msTime = 0
vR = 0
vS = 0
vT = 0
iR = 0
iS = 0
iT = 0
iN = 0
fr = 0

def getDataFromSerial(line):
  if len(line) > 0:
    # print (line)
    vrOffset = ord(line[0])
    vsOffset = ord(line[1])
    vtOffset = ord(line[2])
    irOffset = ord(line[3])
    isOffset = ord(line[4])
    itOffset = ord(line[5])
    inOffset = ord(line[6])
    deltaNOffset  = ord(line[7])
    indexLSB = ord(line[8])
    indexMSB = ord(line[9])
        
    index = indexLSB | (indexMSB << 8)
       
    vrIndex = index & (2**2 - 2**0)
    vsIndex = (index & (2**4 - 2**2)) >> 2
    vtIndex = (index & (2**6 - 2**4)) >> 4
    irIndex = (index & (2**8 - 2**6)) >> 6
    isIndex = (index & (2**10 - 2**8)) >> 8
    itIndex = (index & (2**12 - 2**10)) >> 10
    inIndex = (index & (2**14 - 2**12)) >> 12
    deltaNIndex = (index & (2**16 - 2**14)) >> 14
        
    vR_ADC = vrOffset + 256 * vrIndex
    vS_ADC = vsOffset + 256 * vsIndex
    vT_ADC = vtOffset + 256 * vtIndex
    iR_ADC = irOffset + 256 * irIndex
    iS_ADC = isOffset + 256 * isIndex
    iT_ADC = itOffset + 256 * itIndex
    iN_ADC = inOffset + 256 * inIndex
    deltaN  = deltaNOffset  + 256 * deltaNIndex
    
    global msTime    
    msTime = str(int((time.time()*1000)))

    #Values conversion
    global vR
    global vS
    global vT
    global iR
    global iS
    global iT
    global iN
    convFactor_vR = float(config['CONVFACTOR_VR'])		#Coversion factor between ADC Vpp and Vrms
    convFactor_vS = float(config['CONVFACTOR_VS'])
    convFactor_vT = float(config['CONVFACTOR_VT'])
    convFactor_iR = float(config['CONVFACTOR_IR'])
    convFactor_iS = float(config['CONVFACTOR_IS'])
    convFactor_iT = float(config['CONVFACTOR_IT'])
    convFactor_iN = float(config['CONVFACTOR_IN'])

    vR = vR_ADC * convFactor_vR
    vS = vS_ADC * convFactor_vS
    vT = vT_ADC * convFactor_vT
    iR = iR_ADC * convFactor_iR
    iS = iS_ADC * convFactor_iS
    iT = iT_ADC * convFactor_iT
    iN = iN_ADC * convFactor_iN
    
    global fr
    fr = 2000/((4608-deltaN)/102.4)
    #fr = deltaN

def avgList(myList):
  return sum(myList) / float(len(myList))

def trigger():
  flag = False
  items = [vRList, vSList, vTList] # Items to be checked

  for i in items:
    if abs(i[position] - i[position-1]) > vThreshold:
      flag = True
  
  return flag

#Variables
nzLast = 0
msTimeLast = 0

vRList = []			#Voltage buffer list for events log
vSList = []
vTList = []
iRList = []                     #Current buffer lists for events log 
iSList = []
iTList = []
iNList = []
frList = []			#Frequency buffer list for events log

timeBufferLength = 16000			#Amount of time saved in the buffers[ms]
linePeriod = 32					#Line typical period [ms]
listLength = timeBufferLength/linePeriod	#Buffer length (10 seconds, 10000ms)
position = 100					#Position in buffer where events are detected
dataDelay = (listLength) * linePeriod 		#(20 = 10000ms/500)
i1 = 0				
printN = 0			#Remaining lines to print in events file
event = 0			#Event counter

vThreshold = int(config['VTHRESHOLD'])			#Voltage difference required to trigger an event
vNoiseFilter = -1		#Voltage below this value is considered noise
printFlag = False		#Allows saving events
errorFlag = False		#Avoids events after serial error

# vPlotList = []			#Voltage buffer list for plotting
# fPlotList = []			#Frequency buffer list for plotting
# iPlotList = []			#Current buffer list for plotting
# plotListLength = 50		#Plot length
# i2 = 0

while True:
  try:
    if ser.isOpen() == True:
      if errorFlag == False:
        serialLine = ser.readline()
      else:
        errorFlag = False
        pass
      #Data reading
      getDataFromSerial(serialLine)
      #Data lists
      if i1 < listLength and vR > vNoiseFilter and vS > vNoiseFilter and vT > vNoiseFilter:
        vRList.append(vR)
        vSList.append(vS)
        vTList.append(vT)
        frList.append(fr)
        iRList.append(iR)
        iSList.append(iS)
        iTList.append(iT)
        iNList.append(iN)
        i1 += 1
      elif i1 >= listLength and vR > vNoiseFilter and vS > vNoiseFilter and vT > vNoiseFilter:
        vRList.pop(0)
        vRList.append(vR)
        vSList.pop(0)
        vSList.append(vS)
        vTList.pop(0)
        vTList.append(vT)
        frList.pop(0)
        frList.append(fr)
        iRList.pop(0)
        iRList.append(iR)
        iSList.pop(0)
        iSList.append(iS)
        iTList.pop(0)
        iTList.append(iT)
        iNList.pop(0)
        iNList.append(iN) 

      #Log writing and Screen printing (Periodic data every Delay seconds)
      if (int(msTime) >= (int(msTimeLast) + (args.delay * 1000)) and vR > vNoiseFilter and vS > vNoiseFilter and vT > vNoiseFilter):
        logInfo = "%.d \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.d \n"  % (int(msTime), vRList[-1], vSList[-1], vTList[-1], iRList[-1], iSList[-1], iTList[-1], iNList[-1], fr, event)

        #Make year folder
        try:
          yearFolder = dataPath + building + '/' + time.strftime("%Y")
          os.mkdir(yearFolder)
        except:
          pass#print 'Error making year folder'

        #Make month folder
        try:
          monthFolder = yearFolder + '/' + time.strftime("%m")
          os.mkdir(monthFolder)
        except:
          pass#print 'Error making month folder'

        logFilePath = monthFolder + '/' + time.strftime("%Y-%m-%d") + '-' + building.upper() + '.tsv'

        with open(logFilePath,'a') as f:
          f.write(logInfo)
        
        hour = time.strftime("%d/%m/%Y - %H:%M:%S")

        print (logInfo)

        msTimeLast = msTime
      else:
        pass
       
      #Event writing (Prints data every 500us when an event occurs)
      #Event detection
      if trigger() and i1 == listLength and printN == 0:
        printFlag = eval(config['SAVE_EVENTS'])        ##################  Habilitar para guardar eventos!!! #####################
        printN = listLength
        event += 1
      else:
        pass
          #Event writing
      if printFlag == True and printN > 0:
        eventInfo = "%.d \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.2f \t %.d \t %.d \n"  % ((int(msTime) - dataDelay), vRList[0], vSList[0], vTList[0], iRList[0], iSList[0], iTList[0], iNList[0], frList[0], event, printN)

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