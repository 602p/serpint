#! /usr/bin/env python

#
#    Copyright (C) 2012  Louis Goessling <louis@goessling.com>
#
#    'GNU General Public Licence' and 'GNU General Public Licence 3' refers to the licence
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

ver=22

print "SERPINT NETWORK GPIO TOOLKIT"
print "           V"+str(ver)+"             "
#print "PLEASE USE ^C IF YOU NEED TO FORCE EXIT, ONLY USE ^Z IF YOU WANT TO EXIT WITHOUT CLEANUP"
print

try:
	import socket, os, time, thread, sys, imp, gpio #This uses RPi.GPIO 1.0 so I dont have to compile it
	import pyserial as serial
except BaseException as e:
	throw_error(1,e) #Cant find module error

def sendb(conn, byte, q=0): #send chr(byte) over socket conn, and report if q[iet]=0
	try:
		if not q:print "SENDING: "+str(byte)
		conn.send(chr(byte))
	except BaseException as e:
		throw_error(9,e) #TX (sending) error

def recvo(conn, num=1, q=0): #read num bytes, then run ord() on them, and report if q[iet]=0
	try:
		i=ord(conn.recv(num))
		if not q:print "RECIVED: "+str(i)
		return i
	except BaseException as e:
		throw_error(10,e) #RX (reciving) error

def master_connection_init(conn):
	while 1:
		i=recvo(conn)
		if i==2:
			break
	thread.interrupt_main()

def loop_master_connection(conn): #Run the master GPIO command interpereter over the socket conn
	run=1
	got_OK=0
	n=0
	try:
		thread.start_new_thread(master_connection_init, (conn,))
		while not got_OK: #Loop until connected
			n=n+1
			print "CONNECTING (TRY "+str(n)+")"
			sendb(conn, 1, 1) #Send a 1 (acknowlage me!)
			time.sleep(4)
	except KeyboardInterrupt:
		print "Got OK, client connected"
		sendb(conn,10)
	while run:
		#recive command
		command=recvo(conn)
		if command==3: #3 is shutdown
			sendb(conn, 4) #4 is shutting down
			conn.close()
			run=0
		elif command==22: #22 is initilize pin as output
			ext=recvo(conn) #read pin to be initilized as output
			try:
				print "Initilizing pin "+str(ext)+" as output"
				gpio.setup(ext, gpio.OUT) #initilize as output
				sendb(conn, 10) #send back OK
			except BaseException as e:
				throw_error(4,e,0) #Throw ERROR4_GPIO_ERROR, dont quit the program, this is recoverable
				sendb(conn, 11) #Send back 11, error
		elif command==23: #23 is init as input
			ext=recvo(conn) #recive pin number to init
			try:
				print "Initilizing pin "+str(ext)+" as input"
				gpio.setup(ext, gpio.IN) #initilize as input
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0) #Throw error
				sendb(conn, 11)
		elif command==24: #24 is read from pin
			ext=recvo(conn) #recive pin to read from
			try:
				print "Reading value from pin "+str(ext)
				sendb(conn, int(gpio.input(ext))) #read value and send
				sendb(conn, 10) 
			except BaseException as e:
				throw_error(4,e,0) #Throw error, send 0 value in place of being read, send 11 so they know an error occoured, not just value is 0
				sendb(conn, 0)
				sendb(conn, 11)
		elif command==25: #25 is turn pin on
			ext=recvo(conn) #recive pin# to turn on
			try:
				print "Turning pin "+str(ext)+" on"
				gpio.output(ext, 1) #turn on
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0) #throw error
				sendb(conn, 11)
		elif command==26: #26 is turn pin off
			ext=recvo(conn) #recive pin# to turn off
			try:
				print "Turning pin "+str(ext)+" on"
				gpio.output(ext, 0) #turn off
				sendb(conn, 10)
			except BaseException as e:
				throw_error(4,e,0) #throw error
				sendb(conn, 11)
		elif command==30: #30 is a keepalive/ping signal, send back 10 (OK) so they know we are alive
			print "Client sent keep-alive/ ping"
			sendb(conn, 10)

def create_vsi(ser_addr, port): #Create a Virtual Socket Interface, bolth system and client
	try:
		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM) #open socket and bind to localhost:port
		sock.bind(("", port))
		print "Opening VSI Client Socket..."
		thread.start_new_thread(sock.listen, (1,)) #start a new thread listening for connections
		vsi_system_sock(ser_addr,"localhost", port) #call vsi_system_sock to open the system VSI
		conn, addr=sock.accept() # accept connection, get conn, addr
		print "Connection Established... Address: ", addr
		return conn #return connection that is controlling the Virtual Socket
	except BaseException as e:
		throw_error(5,e) #throw VSI_INIT_ERROR

def vsi_system_sock(ser_addr, host, port): #create the system VSI socket with a call to remserial
	try:
		print "Opening VSI System Socket..."
		time.sleep(3) #wait for the client to be ready/the socket to have finished
		os.system("sudo ./remserial_"+os.popen("arch").read().strip("\n")+" -d -r "+str(host)+" -p "+str(port)+" -l /dev/"+ser_addr+" /dev/ptmx &") #put out a call to remserial to create a virtual socket and connect it to host:port
		print "System VSI Socket Online..."
	except BaseException as e:
		throw_error(6,e) #throw VSI_SYS_INIT_ERROR

def remove_vsi(ser_addr): #close a VSI
	try:
		print "Removing VSI '"+ser_addr+"'..."
		os.system("sudo rm -f /dev/"+ser_addr) #wait, remove the virtual socket
	except BaseException as e:
		throw_error(8,e) #error removing the VSI

def serial_to_socket(ser_addr, port): #forward data from a virtual serial port to a socket, I would use remserial, but it only works with proper (non-virtual) serial ports
	try:
		ser=serial.Serial("/dev/"+ser_addr) #open the serial port
		ser.open()
		sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM) #open and bind the socket
		sock.bind(("", port))
		sock.listen(1)
		print "Waiting for remote connection to socket..." #wait for the other machine to run SOCKTOSERIAL
		conn, addr=sock.accept()
		print "Got connection!"
	except BaseException as e:
		throw_error(7,e) #error initilizing
	thread.start_new_thread(ser_to_sock_a, (ser, conn)) #start thread a (forwarding from serial to socket)
	time.sleep(0.1) #slight delay to keep the serial port psuedo-threadsafe
	thread.start_new_thread(ser_to_sock_b, (ser, conn)) #start thread b (forwarding from socket to serial)
	while 1:pass #keep running, as not to close the process with still-running threads

def ser_to_sock_a(ser, sock): #read information from ser and write it to sock
	while 1:
		try:
			time.sleep(0.1)
			i=ser.read(1)
			print "Just relayed "+str(ord(i))+" from serial to socket"
			if ord(i) in [3,4]:
				sock.send(i)
				print "Thread A ready for exit"
				break
			sock.send(i)
		except BaseException as e:
			throw_error(3,e)

def ser_to_sock_b(ser, sock): #read information from sock and write it to ser
	while 1:
		try:
			time.sleep(0.1)
			i=sock.recv(1)
			print "Just relayed "+str(ord(i))+" from socket to serial"
			if ord(i) in [3,4]:
				ser.write(i)
				print "Thread B ready for exit"
				print "Interrupting main thread"
				thread.interrupt_main()
				break
			ser.write(i)
		except BaseException as e:
			throw_error(2,e)

def serial_format_bridge(ser_addr, port, ser_addr2, modulepath): #create a bridge between one VSI and another so that the data can be reformatted from "raw" GPIO interpreter data to formatted data that would be useful for other programs
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
	if str(debug) in ["", "1", "\nUse 'serpint.py help' for information", "1\nUse 'serpint.py help' for information"]:
		return
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
	elif sys.argv[1].upper()=="SERIALTOSOCK":
		serial_to_socket(sys.argv[2], int(sys.argv[3])) #device, port
	elif sys.argv[1].upper()=="SOCKTOSERIAL":
		vsi_system_sock(sys.argv[2], sys.argv[3], int(sys.argv[4])) #device, host, port
	elif sys.argv[1].upper()=="SERIALFORMATBRIDGE":
		serial_format_bridge(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]) #device, port, target device, module
	elif sys.argv[1].upper()=="CLEANUP":
		print "Scanning for virtual serial ports..."
		for i in os.popen("ls /dev").readlines():
			if i.startswith("ttyS"):
				z=os.popen("stat /dev/"+i.strip("\n")+"|grep link").readline().strip("\n")
				if z!="":
					print "Cleaning port /dev/"+i.strip("\n")+" ..."
					remove_vsi(i.strip('\n'))
		print "Done"
	elif sys.argv[1].upper()=="HELP": #show help
		if len(sys.argv)==3:
			if sys.argv[2].upper()=="DEVINFO":
				os.system("cat ../doc/devinfo | more")
			if sys.argv[2].upper()=="SFBINFO":
				os.system("cat ../doc/sfbinfo | more")
		else:
			os.system("cat ../doc/help | more")
	elif sys.argv[1].upper()=="DEMO": #give a demo
		print "This is a demo"
		print "When it pauses, press enter, and in any popup windows that ask for your password, give it to them"
		print
		print "Now starting the GPIOTOSERIAL command"
		print "running './serpint gpiotoserial ttyS44 1234'"
		os.system("gnome-terminal -x sudo ./serpint gpiotoserial ttyS44 1234")
		#time.sleep(3)
		raw_input()
		print "that window is waiting for a connection."
		print "Now connecting..."
		print "running './serping serialtosock ttyS44 1235'"
		os.system("gnome-terminal -x sudo ./serpint serialtosock ttyS44 1235")
		raw_input()
		print "now connecting to socket 1235 from python"
		s = None
		for res in socket.getaddrinfo('localhost', 1235, socket.AF_UNSPEC, socket.SOCK_STREAM):
		    af, socktype, proto, canonname, sa = res
		    try:
			s = socket.socket(af, socktype, proto)
 		    except socket.error, msg:
			s = None
			continue
 		    try:
			s.connect(sa)
		    except socket.error, msg:
			s.close()
			s = None
			continue
		sock=s
		print 'connected, sending an ok (0x02)'
		sock.send(chr(2))
		print 'got back 0x'+str(hex(int(ord(sock.recv(1)))))
		print 'connected and online! :)'
		time.sleep(7)
		print 'closing'
		sock.send(chr(3))
		sock.recv(1)
		sock.close()
		print "Please close any other open windows, then press enter"
		raw_input()
		print "cleaning up"
		print "running './serpint cleanup'"
		os.system("gnome-terminal -x sudo ./serpint cleanup")
		print "Exiting"
	else:
		throw_error(11, 'No arguments specified; Use "serpint.py help" for information', 0)
		raw_input('Press enter to close')
except BaseException as e:
	throw_error(11,str(e)+"\nUse 'serpint.py help' for information") #This is a error meaning that the command line arguments werent interpereted correctly


