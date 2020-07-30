#!/usr/bin/python

import sys
from Tkinter import *
import math
from time import gmtime, strftime, localtime


def utc2hms(utcSec):
  hms = strftime("%d/%m/%Y - %H:%M:%S", localtime(utcSec))
  return hms


def onClick():
 try:
  _valor_utcSec = float(entrada_texto_utcSec.get())/1000
  
  hora = utc2hms(_valor_utcSec)
  
  resultado.config(text="%s" % hora)

 except ValueError:
  resultado.config(text="Introduce un numero!")

def borrarDato():
  entrada_texto_utcSec.delete(0,END)


app = Tk()
app.title("ms to date converter")
 
#Ventana Principal
vp = Frame(app)
vp.grid(column=0, row=0, padx=(50,50), pady=(30,30))
vp.columnconfigure(0, weight=1)
vp.rowconfigure(0, weight=1)

timestampMs = Label(vp, text="timestamp (ms)")
timestampMs.grid(column=1, row=1, sticky=(W,E))

resultado = Label(vp, text=" ")
resultado.grid(column=2, row=2, sticky=(W,E), pady=(10,0))
 
botonConversor = Button(vp, text="Convert -> ", command=onClick)
botonConversor.grid(column=1, row=2, pady=(10,0))

timestampAConvertir = ""
entrada_texto_utcSec = Entry(vp, width=13, textvariable=timestampAConvertir)
entrada_texto_utcSec.grid(column=2, row=1)

botonCero = Button(vp, text="(Clear)", command=borrarDato)
botonCero.grid(column=3, row=1, pady=(10,0))

app.mainloop()
