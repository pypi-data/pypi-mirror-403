import os
import socket
from _socket import gaierror
from contextlib import closing
from uuid import getnode

from scapy.all import ARP
from scapy.all import Ether
from scapy.all import arping

from modulitiz_nano.ModuloListe import ModuloListe
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloNetworking(object):
	@staticmethod
	def getMacAddress()->str:
		mac=("%012X" % getnode())
		return mac
	
	@classmethod
	def fromMacToIp(cls,mac:str,retries:int=5)->str|None:
		"""
		On Linux requires root privileges.
		Slow function, requires some seconds.
		"""
		for _ in range(retries):
			ip=cls.__fromMacToIp(mac)
			if ip is not None:
				return ip
		return None
	
	@classmethod
	def __fromMacToIp(cls,mac: str) -> str|None:
		localNetwork=cls.getLocalIp().rsplit(".",1)[0]
		ans,_unans=arping(localNetwork+".0/24",verbose=False)
		for s,r in ans:
			if r[Ether].src==mac:
				return s[ARP].pdst
		return None
	
	@staticmethod
	def getLocalIp()->str|None:
		"""
		Returns private local IP address.
		"""
		sockObj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sockObj.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		try:
			# doesn't even have to be reachable
			sockObj.connect(('255.255.255.255', 1))
			indirizzoIp = sockObj.getsockname()[0]
		except gaierror:
			indirizzoIp = None
		finally:
			sockObj.close()
		return indirizzoIp

	@staticmethod
	def isHttpPortOpen(host:str|None,port:int)->bool:
		# controllo host
		if host is None:
			host="127.0.0.1"
		# controllo porta
		with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
			if sock.connect_ex((host, port)) == 0:
				return True
		return False

	@staticmethod
	def checkPing(ipAddress:str)->bool:
		# build command
		cmd="ping "
		textToSearch="="
		if ModuloSystem.isWindows():
			cmd+="-n"
			textToSearch=" TTL"+textToSearch
		elif os.name=='posix':
			cmd+="-W 5 -c"
			textToSearch=" ttl"+textToSearch
		else:
			raise ExceptionRuntime("Tipologia del sistema operativo non riconosciuta: "+os.name)
		cmd+=" 1 "+ipAddress
		# execute command
		outputComando=ModuloStringhe.normalizzaEol(ModuloSystem.systemCallReturnOutput(cmd,None))
		rows=outputComando.split("\n")
		rows=ModuloListe.eliminaElementiVuoti(rows)
		rowsMatching=[x for x in rows if ModuloStringhe.contains(x,textToSearch)]
		return len(rowsMatching)==1
