import time

from modulitiz_micro.rete.ModuloNetworking import ModuloNetworking
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_nano.sistema.ModuloSystem import ModuloSystem


class ModuloTor(object):
	COMMAND="tor"
	HTTP_PORT=9050
	MAX_RETRIES_CHECK_PORT_OPEN=100
	
	def __init__(self,dirTor:str):
		self.dirTor=dirTor
		self.pid=0
	
	def start(self)->int:
		cmd=ModuloFiles.pathJoin(self.dirTor, self.COMMAND)
		# avvio e aspetto che il servizio si avvii
		for riga in ModuloSystem.systemCallYieldOutput(cmd, None):
			if ModuloStringhe.contains(riga,"100%"):
				break
		# controllo che la porta sia stata aperta
		maxRetries=self.MAX_RETRIES_CHECK_PORT_OPEN
		while maxRetries>0:
			if ModuloNetworking.isHttpPortOpen(None, self.HTTP_PORT):
				maxRetries=-1
			else:
				maxRetries-=1
				time.sleep(0.1)
		if maxRetries==0:
			raise ExceptionRuntime("Tor non ha la porta aperta.")
		# ricavo il pid
		pid=ModuloSystem.findPidByName(self.COMMAND)
		return pid
	
	def stop(self):
		if self.pid==0:
			return
		ModuloSystem.sendCtrlcProcess(self.pid)
	
	def restart(self):
		self.stop()
		self.start()
