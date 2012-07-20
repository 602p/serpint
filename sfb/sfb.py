import sys, time, serial, socket

def GPIOFORMAT_ping():return "IAMGPIOFORMAT"
def GPIOFORMAT_run(port, ser_addr, ser_addr2, init_function):
	sock, ser=init_function.__call__(port, ser_addr, ser_addr2)
	time.sleep(2)
	print "SFB started"
	try: main(sock, ser)
	except BaseException as e:
		print "-"*30
		print "An error occoured inside of the SFB script."
		print "Error no. 13, ERROR13_INTERNAL_SFB_ERROR"
		print "Debug information: "+str(e)
		sys.exit(1)
		
#to use SFB from python copy this at the end of your python script, it initilizes and calls main(sock, ser)
