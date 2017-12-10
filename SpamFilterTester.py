#!/usr/bin/env python3

#TODO add vypis do souboru failu

from __future__ import print_function
import os
import sys
import subprocess

SpamFolderName = 'spam'
HamFolderName = 'ham'

Dirs = os.listdir(os.curdir + '/Tests')
if len(sys.argv) > 1:
    Dirs = sys.argv[1:]

SpamCount = 0
HamCount = 0
SpamAccepted = []
HamRejected = []
HamFailed = []
SpamFailed = []


for TestFolder in sorted(Dirs):
    SpamList = os.listdir(os.curdir + '/Tests/' + TestFolder + '/' + SpamFolderName)
    HamList = os.listdir(os.curdir + '/Tests/' + TestFolder + '/' + HamFolderName)

    SpamCount += len(SpamList)
    HamCount += len(HamList)

    SpamList = [w.replace(' ', '\ ') for w in SpamList]
    HamList = [w.replace(' ', '\ ') for w in HamList]

    # prepend location to every e-mail filename
    SpamList = ['./Tests/' + TestFolder + '/' + SpamFolderName + '/{0}'.format(i) for i in SpamList]
    HamList = ['./Tests/' + TestFolder + '/' + HamFolderName + '/{0}'.format(i) for i in HamList]

    SpamOutput = b""
    HamOutput = b""

    IterationCount = len(SpamList) if len(SpamList) > len(HamList) else len(HamList)
    IterationCount /= 1000

    # split to prevent "too many arguments" error
    for i in range(int(IterationCount) + 1):
        SpamOutput += subprocess.check_output('python3 antispam.py ' + " ".join(SpamList[i * 1000 : (i+1) * 1000]), shell=True)
        HamOutput += subprocess.check_output('python3 antispam.py ' + " ".join(HamList[i * 1000 : (i+1) * 1000]), shell=True)

    SpamOutput = SpamOutput.split(b'\n')
    HamOutput = HamOutput.split(b'\n')

    for line in SpamOutput:
        if b'OK' in line:
            SpamAccepted.append(line[:line.find(b'OK')])
        elif b'FAIL' in line:
            SpamFailed.append(line[:line.find(b'FAIL')])

    for line in HamOutput:
        if b'SPAM' in line:
            HamRejected.append(line[:line.find(b'SPAM')])
        elif b'FAIL' in line:
            HamFailed.append(line[:line.find(b'FAIL')])


CorrectSpamPercentage = float(((SpamCount - (len(SpamAccepted) + len(SpamFailed)))/SpamCount) * 100) if SpamCount != 0 else 0
CorrectHamPercentage = float(((HamCount - (len(HamRejected) + len(HamFailed)))/HamCount) * 100) if HamCount != 0 else 0

# write result summarization to terminal
if SpamCount != 0:
    sys.stdout.write("TOTAL SPAM TESTED:\t\t" + str(SpamCount) + "\n")
    sys.stdout.write("\tSPAM MARKED AS SPAM:\t" + "\033[0;32m" + str(SpamCount - (len(SpamAccepted) + len(SpamFailed))) + "\t%.2f" % CorrectSpamPercentage + " %\033[0;0m" + "\n")
    sys.stdout.write("\tSPAM MARKED AS HAM:\t" + "\033[1;31m" + str(len(SpamAccepted)) + "\t%.2f" % ((len(SpamAccepted)/SpamCount) * 100)  + " %\033[0;0m" + "\n")
    sys.stdout.write("\tSPAM FAILED:\t\t" + "\033[1;31m" + str(len(SpamFailed)) + "\t%.2f" % ((len(SpamFailed)/SpamCount) * 100) + " %\033[0;0m" + "\n\n")

if HamCount != 0:
    sys.stdout.write("TOTAL HAM TESTED:\t\t" + str(HamCount) + "\n")
    sys.stdout.write("\tHAM MARKED AS HAM:\t" + "\033[0;32m" + str(HamCount - (len(HamRejected) + len(HamFailed))) + "\t%.2f" % CorrectHamPercentage + " %\033[0;0m" + "\n")
    sys.stdout.write("\tHAM MARKED AS SPAM:\t" + "\033[1;31m" + str(len(HamRejected)) + "\t%.2f" % ((len(HamRejected)/HamCount) * 100)  + " %\033[0;0m" + "\n")
    sys.stdout.write("\tHAM FAILED:\t\t" + "\033[1;31m" + str(len(HamFailed)) + "\t%.2f" % ((len(HamFailed)/HamCount) * 100)  + " %\033[0;0m" + "\n")

CorrectSpamPercentage = round(CorrectSpamPercentage)
CorrectHamPercentage = round(CorrectHamPercentage)

sys.stdout.write("\nYou would obtain: ")
if CorrectHamPercentage >= 95 and CorrectSpamPercentage >= 45:
    sys.stdout.write("8 points! Congrats!")
elif CorrectHamPercentage >= 93 and CorrectSpamPercentage >= 40:
    sys.stdout.write("7 points! Great work!")
elif CorrectHamPercentage >= 91 and CorrectSpamPercentage >= 37:
    sys.stdout.write("6 points! Good job!")
elif CorrectHamPercentage >= 89 and CorrectSpamPercentage >= 34:
    sys.stdout.write("5 points! Nice!")
elif CorrectHamPercentage >= 87 and CorrectSpamPercentage >= 30:
    sys.stdout.write("4 points! Not bad!")
elif CorrectHamPercentage >= 85 and CorrectSpamPercentage >= 26:
    sys.stdout.write("3 points! You can do better than this!")
elif CorrectHamPercentage >= 83 and CorrectSpamPercentage >= 23:
    sys.stdout.write("2 points! Keep working!")
elif CorrectHamPercentage >= 80 and CorrectSpamPercentage >= 20:
    sys.stdout.write("1 points! You've got a long way ahead!")
else:
    sys.stdout.write("0 points! Common!")
sys.stdout.write("\n")

# write result details to files SpamResults.txt, HamResults.txt and FailResults.txt
SpamResults = open("SpamResults.txt", "w")
SpamResults.write("Accepted:\n" + str(SpamAccepted))
SpamResults.write("\n\nFailed:" + str(SpamFailed))
SpamResults.close()

HamResults = open("HamResults.txt", "w")
HamResults.write("Rejected:\n" + str(HamRejected))
HamResults.write("\n\nFailed:" + str(HamFailed))
HamResults.close()

FailResults = open("FailResults.txt", "w")
FailResults.write("Rejected:\n" + str(HamRejected))
FailResults.write("\n\nFailed:" + str(HamFailed))
FailResults.close()
