import random


pins=[0,1,2,3,4,5,6,7]
def expand_bin(bin, length):
	return "0"*(length-len(bin))+bin

def main(sock, ser):
	ser.write(chr(2))
	for i in pins:
		ser.write(chr(22))
		ser.write(chr(i))
		if ord(ser.read(1))!=10:
			print "ERROR! Pin "+str(i)+" could not be cast as input"
		else:
			print "Pin "+str(i)+" set as input"
	while 1:
		recived=ord(sock.recv(1))
		ser.write(chr(30))
		if ord(ser.read(1))==10: print "Beggining sending..."
		if recived==1:
			for i in pins:
				ser.write(chr(24))
				ser.write(chr(i))
				value=ord(ser.read(1))
				if ord(ser.read(1))!=10: print "ERROR! Pin "+str(i)+" could not be read!"
				sock.send("Pin "+str(i)+" is "+str(value))

import sys, time, socket
import pyserial as serial

def GPIOFORMAT_ping():return "IAMGPIOFORMAT"
def GPIOFORMAT_run(port, ser_addr, ser_addr2, init_function):
	sock, ser=init_function.__call__(port, ser_addr, ser_addr2)
	time.sleep(2)
	print "SFB started"
	try: 
		main(sock, ser)
	except BaseException as e:
		print "-"*30
		print "An error occoured inside of the SFB script."
		print "Error no. 13, ERROR13_INTERNAL_SFB_ERROR"
		print "Debug information: "+str(e)
		sys.exit(1)
		
		
		
