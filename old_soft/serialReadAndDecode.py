#!/usr/bin/python2.7

import serial

###Serial port configuration

#Serial port configuration
ser = serial.Serial()
ser.port = '/dev/ttyACM0'
ser.baudrate =115200
ser.timeout = 1.0
ser.open()

while True:
  try:
    #Data reading
    line = ser.readline()
    if len(line) > 0:
      #print line
      
      vrOffset = ord(line[0])
      vsOffset = ord(line[1])
      vtOffset = ord(line[2])
      fOffset  = ord(line[3])
      irOffset = ord(line[4])
      isOffset = ord(line[5])
      itOffset = ord(line[6])
      inOffset = ord(line[7])
      indexLSB = ord(line[8])
      indexMSB = ord(line[9])
      
      index = indexLSB | (indexMSB << 8)
      
      vrIndex = index & (2**2 - 2**0)
      vsIndex = (index & (2**4 - 2**2)) >> 2
      vtIndex = (index & (2**6 - 2**4)) >> 4
      fIndex = (index & (2**8 - 2**6)) >> 6
      irIndex = (index & (2**10 - 2**8)) >> 8
      isIndex = (index & (2**12 - 2**10)) >> 10
      itIndex = (index & (2**14 - 2**12)) >> 12
      inIndex = (index & (2**16 - 2**14)) >> 14
      
      Vr = vrOffset + 256 * vrIndex
      Vs = vsOffset + 256 * vsIndex
      Vt = vtOffset + 256 * vtIndex
      F  = fOffset  + 256 * fIndex
      Ir = irOffset + 256 * irIndex
      Is = isOffset + 256 * isIndex
      It = itOffset + 256 * itIndex
      In = inOffset + 256 * inIndex
      
      print "%s %s %s %s %s %s %s %s" % (Vr, Vs, Vt, F, Ir, Is, It, In)
      
  except KeyboardInterrupt:
    ser.close()
    break
  except IndexError:
      print line
