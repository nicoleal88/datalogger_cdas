#!/usr/bin/python

import sys
import math
from time import gmtime, strftime, localtime

def utc2hms(utcSec):
  hms = strftime("%d/%m/%Y - %H:%M:%S", localtime(utcSec))
  return hms

valor_utc_uSec = int(raw_input("UNIX microsecond: "))
valor_utc_Sec = valor_utc_uSec / 1000.0

print "Date and time: ", utc2hms(valor_utc_Sec)
