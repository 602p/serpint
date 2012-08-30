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
import time, sys

print "Welcome to the SERPINT test program."
print "This program expects that you have followed the instructions in doc/demo.odt"
"""port_name=raw_input("What serial port did you use during setup? [i.e. /dev/ttyS44] ")
port=serial.Serial(port_name)
port.write(chr(2))
while 1:
	if ord(port.read())!=1: break
port.write(chr(30))
if ord(port.read())!=10:
	print "ERROR!"
	sys.exit()
"""
#----------------------------------------------------------------------------------------#

getch=_GetchUnix()
print "\n\nPress <space> to toggle the power on GPIO pin 4 [http://elinux.org/images/2/2a/GPIOs.png] and q to quit"
while 1:
	key=getch()
	if key==" ":
		print "Toggling..."
	if key=="q":
		break
