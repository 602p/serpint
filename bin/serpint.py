#! /usr/bin/env python

#
#    Copyright (C) 2012  Louis Goessling <louis@goessling.com>
#
#    'GNU General Public Licence' and 'GNU General Public Licence 3' refer to the licence
#     ../licences/licence.txt
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#

print "SERPINT NETWORK GPIO TOOLKIT"
print

try:
	import socket, os, time, thread, sys, imp, gpio #This uses RPi.GPIO 1.0 so I dont have to compile it
	import pyserial as serial
except BaseException as e:
	throw_error(1,e)

global version
version=1

def sendb(conn, byte, q=0):
	try:
		if not q:print "SENDING: "+str(byte)
		conn.send(chr(byte))
	except BaseException as e:
		throw_error(9,e)

def recvo(conn, num=1, q=0):
	try:
		i=ord(conn.recv(num))
		if not q:print "RECIVED: "+str(i)
		return i
	except BaseException as e:
		throw_error(10,e)

def loop_master_connection(conn):
	run=1
	got_OK=0
	n=0
	while not got_OK:
		n=n+1
		print "CONNECTING (TRY "+str(n)+")"
		sendb(conn, 1, 1)
		time.sleep(1)
		i=recvo(conn, 1, 1)
		if i==2:
			got_OK=1
			print
			print "got OK, client is connected"
	while run:
		#recive command
		command=recvo(conn)
		if command==3:
			sendb(conn, 4)
			#shutdown code would go here but this is handled by the main block
			run=0
		elif command==22:
			ext=recvo(conn)
			try:
				print "Initilizing pin "+str(ext)+" as output"
				gpio.setup(ext, gpio.OUT) #initilize as output
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0)
				sendb(conn, 11)
		elif command==23:
			ext=recvo(conn)
			try:
				print "Initilizing pin "+str(ext)+" as input"
				gpio.setup(ext, gpio.IN) #initilize as input
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0)
				sendb(conn, 11)
		elif command==24:
			ext=recvo(conn)
			try:
				print "Reading value from pin "+str(ext)
				sendb(conn, gpio.input(ext)) #read value and send
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0)
				sendb(conn, 0)
				sendb(conn, 11)
		elif command==25:
			ext=recvo(conn)
			try:
				print "Turning pin "+str(ext)+" on"
				gpio.output(ext, 1) #turn on
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0)
				sendb(conn, 11)
		elif command==26:
			ext=recvo(conn)
			try:
				print "Turning pin "+str(ext)+" on"
				gpio.output(ext, 0) #turn off
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0)
				sendb(conn, 11)
		elif command==30:
			print "Client sent keep-alive/ ping"
			sendb(conn, 10)

def create_vsi(ser_addr, port):
	try:
		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.bind(("", port))
		print "Opening VSI Client Socket..."
		thread.start_new_thread(sock.listen, (1,))
		vsi_system_sock(ser_addr,"localhost", port)
		conn, addr=sock.accept()
		print "Connection Established... Address: ", addr
		return conn
	except BaseException as e:
		throw_error(5,e)

def vsi_system_sock(ser_addr, host, port):
	try:
		print "Opening VSI System Socket..."
		time.sleep(1)
		os.system("sudo ./remserial -d -r "+str(host)+" -p "+str(port)+" -l /dev/"+ser_addr+" /dev/ptmx &")
		print "System VSI Socket Online..."
	except BaseException as e:
		throw_error(6,e)

def remove_vsi(ser_addr, conn):
	try:
		print "Closing Socket..."
		conn.close()
		print "Removing System Virtual Socket..."
		os.system("sudo rm /dev/"+ser_addr)
		print "VSI Removed... Please Note That That Your System May Still Have Traces Of VSI Usage Until You Reboot..."	
	except BaseException as e:
		throw_error(8,e)

def serial_to_socket(ser_addr, port):
	try:
		ser=serial.Serial("/dev/"+ser_addr)
		ser.open()
		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.bind(("", port))
		sock.listen(1)
		print "Waiting for remote connection to socket..."
		conn, addr=sock.accept()
		print "Got connection!"
	except BaseException as e:
		throw_error(7,e)
	thread.start_new_thread(ser_to_sock_a, (ser, conn))
	time.sleep(0.1)
	thread.start_new_thread(ser_to_sock_b, (ser, conn))
	while 1:pass

def ser_to_sock_a(ser, sock):
	while 1:
		try:
			time.sleep(0.1)
			i=ser.read(1)
			print "Just relayed "+str(ord(i))+" from serial to socket"
			sock.send(i)
		except BaseException as e:
			throw_error(3,e)

def ser_to_sock_b(ser, sock):
	while 1:
		try:
			time.sleep(0.1)
			i=sock.recv(1)
			print "Just relayed "+str(ord(i))+" from socket to serial"
			ser.write(i)
		except BaseException as e:
			throw_error(2,e)

def serial_format_bridge(ser_addr, port, ser_addr2, modulepath):
	try:
		module=imp.load_source("module", modulepath) #Use imp to import the child module
	except BaseException as e:
		throw_error(1,e)
	try:
		if module.GPIOFORMAT_ping()=="IAMGPIOFORMAT": #Check that the child module is GPIOFORMAT
			module.GPIOFORMAT_run(port, ser_addr, ser_addr2, serial_format_bridge_passable) #Call the child module, passing it the socket port, and bolth serial addresses, and the callable init script
		else:
			throw_error(0,'')
	except BaseException as e:
		throw_error(0,e)

def serial_format_bridge_passable(port, ser_addr, ser_addr2): #A passable function object that is passed to the SFB child module, and then executed, creating the sock and ser objects
	try:
		ser=serial.Serial("/dev/"+ser_addr) #Open serial port
		ser.open()
		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)#Open socket
		sock.bind(("", port))
		sock.listen(1)
		print "Waiting for remote connection to socket..."
		thread.start_new_thread(vsi_system_sock, (ser_addr2,'localhost',port)) #Start the system socket
		conn, addr=sock.accept()#Meanwhile, wait for the system socket to become live
		print "Got connection!"
		print "Opening Phase 2 Port..."
		return conn, ser
	except BaseException as e:
		throw_error(7,e)

def throw_error(errorno, debug, die=1): #report errors, errorno is the error of the list of errors to display in the report
	errors=["ERROR0_MODULE_NOT_GPIOFORMAT", "ERROR1_MODULE_NOT_FOUND", "ERROR2_NETWORK_RELAY_THREAD_B"\
		, "ERROR3_NETWORK_RELAY_THREAD_A", "ERROR4_GPIO_ERROR", "ERROR5_CREATE_VSI", "ERROR6_CREATE_VSI_SYSTEM"\
		, "ERROR7_NETWORK_RELAY_INIT", "ERROR8_VSI_SHUTDOWN", "ERROR9_SOCKET_TX", "ERROR10_SOCKET_RX"\
		, "ERROR11_CLA_INTERP", "ERROR12_EXIT_ERROR"]
	print "-"*60
	print "An error occoured, Error No. "+str(errorno)
	print "Error detail text: "+errors[errorno]
	print "Debug information: "+str(debug)
	print "-"*60
	if die: sys.exit(1)

try:
	if sys.argv[1].upper()=="GPIOTOSERIAL":
		conn=create_vsi(sys.argv[2], int(sys.argv[3])) #device(virtual), port
		loop_master_connection(conn)
		remove_vsi(sys.argv[2], conn)
	elif sys.argv[1].upper()=="SERIALTOSOCK":
		serial_to_socket(sys.argv[2], int(sys.argv[3])) #device, port
	elif sys.argv[1].upper()=="SOCKTOSERIAL":
		vsi_system_sock(sys.argv[2], sys.argv[3], int(sys.argv[4])) #device, host, port
	elif sys.argv[1].upper()=="SERIALFORMATBRIDGE":
		serial_format_bridge(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]) #device, port, target device, module
	else:
		throw_error(11, 'No arguments specified', 0)
		raw_input('Press enter to close')
except BaseException as e:
	if str(e)=='1': #When you call sys.exit it throws an exiterror, this makes it so it doesnt keep bloating the traceback
		throw_error(12, 'Exiterror, this is normal')
	else:
		throw_error(11,e) #This is a error meaning that the command line arguments werent interpereted correctly


