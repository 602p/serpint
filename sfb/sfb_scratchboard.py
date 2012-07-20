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
				print "Formatting..."
				binary_value=expand_bin(bin(value).replace("0b", "", 1),10)
				binary_sensor=expand_bin(bin(pins.index(i)).replace("0b", "", 1),4)
				highbyte="1"+binary_sensor+binary_value[0]+binary_value[1]+binary_value[2]
				lowbyte="0"+binary_value[3]+binary_value[4]+binary_value[5]+binary_value[6]+binary_value[7]+binary_value[8]+binary_value[9]
				#print value
				#print pins.index(i)
				#print
				#print binary_value
				#print binary_sensor
				#print
				#print highbyte
				#print lowbyte
				#print
				highchr=chr(int(highbyte, 2))
				lowchr=chr(int(lowbyte, 2))
				print "Sending..."
				sock.send(highchr)
				time.sleep(0.04)
				sock.send(lowchr)
				time.sleep(0.04)
				print "Sent!"
			print "Sending Vesion Number (0x04)"
			sock.send(chr(int("11111000", 2)))
			time.sleep(0.04)
			sock.send(chr(int("00000100", 2)))
			time.sleep(0.04)

import sys, time, serial, socket

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
		
		
		
