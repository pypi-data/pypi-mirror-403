# -*- coding: utf-8 -*-

from ..abstract_instrument import AbstractInstrument
import socket

#==============================================================================
ALL_VAL_TYPE = ['PWR_VAL']
ALL_CHANNELS = ['1']

ADDRESS = "192.168.0.27"
CONF_VAL_TYPE = ['CONF:PWR']

#==============================================================================

class NRP2(AbstractInstrument):
	def __init__(self, channels, vtypes, address):
		self.address = address
		self.port = 4002
		self.channels = channels
		self.vtypes = vtypes

	def model(self):
		#self.send("*IDN?")
		#return self.read()
		return "NRP2"

	def connect(self):
		print('Connecting to device @%s:%s...' %(self.address, self.port))
		self.sock = socket.socket(socket.AF_INET,
							 socket.SOCK_STREAM,
							 socket.IPPROTO_TCP)
		self.sock.settimeout(10.0)	# Don't hang around forever
		self.sock.connect((self.address, self.port))
		#self.send("SYST:BEEP")
		print('  --> Ok')
		print(self.model())
		self.configure()

	def configure(self):
		for ch in self.channels:
			self.send(CONF_VAL_TYPE[ALL_VAL_TYPE.index(self.vtypes[self.channels.index(ch)])])
        
	def get_value(self):
		mes = ''
		for ch in self.channels:
			self.send("READ?")
			mesTemp = self.read()
			mes = mes + '\t' + mesTemp
		return mes

	def read(self):
		ans = ''
		nb_data_list = []
		nb_data = ''
		try:
			while ans != '\n':
				ans = self.sock.recv(1).decode('utf-8')
				nb_data_list.append(ans) # Return the number of data
			list_size = len(nb_data_list)
			for j in range (0, list_size):
				nb_data = nb_data+nb_data_list[j]
			return nb_data
		except socket.timeout:
			print ("Socket timeout error when reading.")
			raise

	def disconnect(self):
		#self.send('*RST')
		#self.send("SYST:BEEP")
		self.sock.close()

	def send(self, command):
		self.sock.send(("%s\n"%command).encode('utf-8'))
