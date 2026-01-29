class FtpReturnBean(object):
	
	def __init__(self,percorso_remoto,nomefile,isFile,countFiles,countDirs):
		self.percorso_remoto=percorso_remoto
		self.nomefile=nomefile
		self.isFile=isFile
		self.countFiles=countFiles
		self.countDirs=countDirs
	
