#!/usr/bin/python2.7

# Use with mc_line_voltage_06.ino
# Prints raw data and events in files, and periodic updates on screen (Every [delay] seconds)

import argparse
import time
import serial
import os
import glob
import subprocess

# Read configFile
config = {}
with open('configFile_battery.conf', 'r') as f:
    File = f.readlines()
    for lines in File:
        splittedLine = lines.split('=')
        if len(splittedLine) == 2:
            config[splittedLine[0]] = splittedLine[1][:-1]


# Parsing
parser = argparse.ArgumentParser()
parser.add_argument("delay", type=int, nargs='?', default=config['DELAY'], help="Delay between data printing [seconds]")
args = parser.parse_args()

# ##Serial port configuration
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
        print 'No se encuentra puerto' + config['PORT']
    except IndexError:
        print 'No se encuentra puerto' + config['PORT']
    return port


# ser.port = getSerialPort()
ser.port = config['PORT']
ser.open()

# Global variables declarations
msTime = 0
vBat = 0


def getDataFromSerial(line):
    if len(line) > 0:
        # print line
        vBat_ADC = float(line)
        # print vBat_ADC
        '''
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
        '''

        global msTime
        msTime = str(int((time.time()*1000)))

        # Values conversion
        global vBat

        convFactor_vBat = float(config['CONVFACTOR_VBAT'])		# Coversion factor between ADC Vpp and Vrms

        vBat = vBat_ADC * convFactor_vBat


def avgList(myList):
    return sum(myList) / float(len(myList))


building = config['BUILDING']

# Make folder
try:
    folder = building.upper()
    os.mkdir(folder)
except:
    pass

# Variables
nzLast = 0
msTimeLast = 0

vBatList = []			# Voltage buffer list for events log

timeBufferLength = 10000			# Amount of time saved in the buffers[ms]
linePeriod = 20					# Line typical period [ms]
listLength = timeBufferLength/linePeriod  # Buffer length (10 seconds, 10000ms)
position = 100					# Position in buffer where events are detected
dataDelay = (listLength) * linePeriod 		# (20 = 10000ms/500)
i1 = 0
printN = 0			# Remaining lines to print in events file
event = 0			# Event counter

vThreshold = int(config['VTHRESHOLD'])			# Voltage difference required to trigger an event
vNoiseFilter = -1		# Voltage below this value is considered noise
printFlag = False		# Allows saving events
errorFlag = False		# Avoids events after serial error

vBatPlotList = []			# Voltage buffer list for plotting
plotListLength = 50		# Plot length
i2 = 0

while True:
  try:
    if ser.isOpen() is True:
      if errorFlag is False:
        serialLine = ser.readline()
      else:
        errorFlag = False
        pass
      # Data reading
      getDataFromSerial(serialLine)
      # Data lists
      if i1 < listLength:
        vBatList.append(vBat)

        i1 += 1
      elif i1 >= listLength:
        vBatList.pop(0)
        vBatList.append(vBat)


      # Log writing and Screen printing (Periodic data every Delay seconds)
      if (int(msTime) >= (int(msTimeLast) + (args.delay * 1000))):

        logInfo = "%.d \t %.2f \t %.d \n"  % (int(msTime), vBatList[len(vBatList)-1], event)

        logFilePath = folder + '/' + time.strftime("%Y-%m-%d") + '-' + building.upper() + '.tsv'

        with open(logFilePath, 'a') as f:
          f.write(logInfo)

        hour = time.strftime("%d/%m/%Y - %H:%M:%S")

        print logInfo

        msTimeLast = msTime
      else:
        pass

      # Event writing (Prints data every 500us when an event occurs)
      # Event detection

      # if (abs(vBatList[position]-vBatList[position-1]) > vThreshold) and i1 == listLength and printN == 0:
      if (vBatList[position] < vThreshold) and i1 == listLength and printN == 0 and event < 3:
        printFlag = eval(config['SAVE_EVENTS'])        ##################  Habilitar para guardar eventos!!! #####################
        printN = listLength
        event += 1
      else:
        pass

          #Event writing
      if printFlag == True and printN > 0:
        eventInfo = "%.d \t %.2f \t %.d \t %.d \n"  % ((int(msTime) - dataDelay), vBatList[0], event, printN)

        logFilePath = folder + '/' + time.strftime("%Y-%m-%d") + '-' + building.upper() + '.tsv'
        with open(logFilePath,'a') as f:
          f.write(eventInfo)
        printN -= 1
      else:
        printFlag = False

      if vBat >= vThreshold and printN == 0:
          event = 0


    else:
      try:
        ser.port = getSerialPort()
        ser.open()
	print "Trying to open serial port"
      except serial.serialutil.SerialException:
        print 'Buscando puerto' + config['PORT']
        time.sleep(5)
      except IndexError:
        pass

  except IndexError:
    pass
  except ValueError:
    pass
  except serial.serialutil.SerialException:
    print 'Serial Error!'
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
    print '\n'
    print "Exiting..." + '\n'
    break
