#!/usr/bin/python2.7

import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as md
import datetime
import os
from time import strftime, localtime

v_nom = 230.0
v_nom_inf = v_nom*0.9
v_nom_sup = v_nom*1.1

f_nom = 50.0
f_nom_inf = 49.5
f_nom_sup = 50.5

v_ylim_sup = v_nom_sup * 1.1
v_ylim_inf = v_nom_inf * 0.9
f_ylim_sup = 51
f_ylim_inf = 49
i_ylim_sup = 23.0
i_ylim_inf = 10.0


def utc2hms(utcSec):
    hms = strftime("%a %Y-%m-%d %H:%M:%S", localtime(utcSec))
    return hms

def hms2seconds(hmsInput):
    HH, MM, SS = hmsInput.split(':')
    return int(HH)*3600+int(MM)*60+int(SS)


parser = argparse.ArgumentParser()
parser.add_argument("File", help="File you want to plot")
parser.add_argument("-e", "--events", help="this option plots the events (may take long time to finish)",
                    action="store_true")
parser.add_argument("-f", "--From", help="Begin plot at [HH:MM:SS]")
parser.add_argument("-t", "--To", help="End plot at [HH:MM:SS]")
parser.add_argument("-r", "--resolution", type=int,
                    help="Skip # data for faster plotting")
args = parser.parse_args()


# File opened, sorted and saved as a temporary file: args.File+'s'
with open(args.File, 'r') as File:
    lines = [line.split() for line in File]
    lines.sort()

    with open(args.File+'s', 'w') as sortedFile:
        for i in lines:
            sortedFile.write('{0}\n'.format('\t'.join(i)))


file = open(args.File+'s')

x_uSec = []
x_Sec = []
date_list = []
vBat = []
vS = []
vT = []
iR = []
iS = []
iT = []
iN = []
fr = []

os.remove(args.File+'s')

plotEvents = args.events

setupFlag = 1

for line in file:
    data = line.split()
    # Setup:
    if (setupFlag == 1):
        firstSecondOfTheDay = int(data[0])/1000
        # print firstSecondOfTheDay
        if args.From:
            From = hms2seconds(args.From) + firstSecondOfTheDay
        else:
            From = 0

        if args.To:
            To = hms2seconds(args.To) + firstSecondOfTheDay
        else:
            To = 999999999999

        # print From, To
        setupFlag = 0
    else:
        pass


    if((int(data[0])/1000) >= From and (int(data[0])/1000) <= To):

        if (((len(data) == 2) or (len(data) == 3)) or ((len(data) == 4) and plotEvents == True)):
            x_uSec.append(float(data[0]))
            x_Sec.append(float(data[0])/1000)
            date_list = [datetime.datetime.fromtimestamp(ts) for ts in x_Sec]
            vBat.append(float(data[1]))
            vS.append(0.0)
            vT.append(0.0)
            iR.append(0.0)
            iS.append(0.0)
            iT.append(0.0)
            iN.append(0.0)
            fr.append(0.0)
        else:
            pass

x_uSec.pop(0)
x_Sec.pop(0)
date_list.pop(0)
vBat.pop(0)
vS.pop(0)
vT.pop(0)
fr.pop(0)
iR.pop(0)
iS.pop(0)
iT.pop(0)
iN.pop(0)

init_date = utc2hms(x_Sec[0])
end_date = utc2hms(x_Sec[len(x_Sec)-1])
date_range = "Log from " + str(init_date) + " to " + str(end_date)

f, axarr = plt.subplots(2, sharex=True)
plt.xticks(rotation=25)

jump = args.resolution

axarr[0].plot(date_list[::jump], vBat[::jump], 'r', date_list[::jump], vS[::jump],
              'g', date_list[::jump], vT[::jump], 'b')
axarr[0].set_title(date_range)
axarr[0].set_ylabel('vRMS')
# axarr[0].set_ylim(v_ylim_inf, v_ylim_sup)
# draw a default hline at y=1 that spans the xrange
# l = axarr[0].axhline(y=v_nom_sup, color='black', linestyle='--')
# l = axarr[0].axhline(y=v_nom_inf, color='black', linestyle='--')
p = axarr[0].axhspan(v_nom_inf, v_nom_sup, facecolor='0.5', alpha=0.5)
axarr[0].grid('on')

'''
axarr[1].plot(date_list, iR, 'r', date_list, iS, 'g', date_list, iT, 'b', date_list, iN, 'black')
#axarr[1].set_title(date_range)
axarr[1].set_ylabel('iRMS')
#axarr[1].set_ylim(i_ylim_inf, i_ylim_sup)
axarr[1].grid('on')
'''

axarr[1].set_ylabel('Frequency')
axarr[1].set_ylim(f_ylim_inf, f_ylim_sup)

axarr[1].plot(date_list[::jump], fr[::jump], color='black')
axarr[1].grid('on')
l = axarr[1].axhline(y=52, color='red')
l = axarr[1].axhline(y=47, color='red')
p = axarr[1].axhspan(f_nom_inf, f_nom_sup, facecolor='0.5', alpha=0.5)

xfmt = md.DateFormatter('%Y-%m-%d %H:%M:%S')
ax = plt.gca()
ax.xaxis.set_major_formatter(xfmt)

# manager = plt.get_current_fig_manager()
# manager.full_screen_toggle()
# manager.resize(*manager.window.maxsize())

plotName = str(args.File)[:-4] + ".pdf"
# print plotName
plt.tight_layout()
plt.savefig(plotName, dpi=200)
plt.show()

file.close()
