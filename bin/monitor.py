#!/usr/bin/env python

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

import pyserial as serial
import time, sys, os

print "Welcome to the SERPINT test program."
print "This program expects that you have followed the instructions in doc/demo.odt"
port_name=raw_input("What serial port did you use during setup? [i.e. /dev/ttyS44] ")
port=serial.Serial(port_name)
port.write(chr(2))
while 1:
	if ord(port.read())!=1: break
port.write(chr(30))
if ord(port.read())!=10:
	print "ERROR!"
	sys.exit()

#----------------------------------------------------------------------------------------#

getch=_GetchUnix()
print "\n\nPress <space> to toggle the power on GPIO pin 4 [http://elinux.org/images/2/2a/GPIOs.png] and q to quit [close all SERPINT components]"
state=False
port.write(chr(22))
port.write(chr(7))
port.write(chr(26))
port.write(chr(7))
while 1:
	key=getch()
	if key==" ":
		os.system("clear")
		state= not state
		if state:
			port.write(chr(25))
			port.write(chr(7))
			print """
   OOOO       NN         N
  O    O      N  N       N
 O       O    N   N      N                 Connect your volt meter between pin 4
O         O   N    N     N                 [http://elinux.org/images/2/2a/GPIOs.png]
O         O   N     N    N                 And ground
O         O   N      N   N                         IT SHOULD READ 2.5V TO 3V
O         O   N       N  N
 O       O    N        N N
   O    O     N         NN                        github.com/602p/serpint
    000O      N          N
    """
		else:
			print """
   OOOO       FFFFFFFFFFF  FFFFFFFFFFFF
  O    O      F            F
 O       O    F            F               Connect your volt meter between pin 4
O         O   FFFFFFFFFFF  FFFFFFFFFFFF    [http://elinux.org/images/2/2a/GPIOs.png]
O         O   F            F               And ground
O         O   F            F                         IT SHOULD READ 0V
O         O   F            F
 O       O    F            F
   O    O     F            F                      github.com/602p/serpint
    000O      F            F
    """
			port.write(chr(26))
			port.write(chr(7))
	if key=="q":
		break

port.write(chr(3))
port.read()
port.close()
print "Closed"
raw_input("Press enter to exit")
