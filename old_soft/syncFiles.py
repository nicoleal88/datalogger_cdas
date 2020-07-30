#!/usr/bin/python2.7

import subprocess

#Read configFile
config = {}
with open('configFile.cnf','r') as f:
  File = f.readlines()
  for lines in File:
    splittedLine = lines.split('=')
    if len(splittedLine) == 2:
      config[splittedLine[0]] = splittedLine[1][:-1]

def sync():

  SERVER_USER = config['SERVER_USER']
  SERVER_IP = config['SERVER_IP']
  SERVER_PATH = config['SERVER_PATH']

  args = []
  args = ["rsync", "-az",('PAO'+''), (SERVER_USER+"@"+SERVER_IP+":"+SERVER_PATH)]
  exitCode = subprocess.call(args)
  print args
  return exitCode

sync()
