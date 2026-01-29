import ftplib
import os

from modulitiz_nano.ModuloListe import ModuloListe
from modulitiz_nano.ModuloStringhe import ModuloStringhe
from modulitiz_nano.files.ModuloFiles import ModuloFiles
from modulitiz_mini.rete.ftp.FtpReturnBean import FtpReturnBean


class ModuloFtp(object):
	DEFAULT_FTP_PORT=ftplib.FTP_PORT
	
	def __init__(self,host,username,password):
		self.host=host
		self.porta=self.DEFAULT_FTP_PORT
		self.username=username
		self.password=password
		self.conn=None
		self.msgBenvenuto=None
	
	def connect(self):
		conn=ftplib.FTP(encoding=ModuloStringhe.CODIFICA_LATIN1)
		try:
			conn.connect(self.host,self.porta)
			self.msgBenvenuto=conn.welcome
		except UnicodeDecodeError as udError:
			self.msgBenvenuto=udError.object.decode(ModuloStringhe.CODIFICA_ASCII,'ignore')
		conn.login(self.username,self.password)
		self.conn=conn
	
	def uploadCartella(self,root_locale,rootRemota,excludeFiles,excludeDirs,min_byte_size,max_byte_size):
		root_locale=ModuloFiles.normalizzaPercorsoLocale(root_locale)
		rootRemota=ModuloFiles.normalizzaPercorsoRemoto(rootRemota)
		countFiles=countDirs=0
		
		for percorsoLocaleRel,percorsoLocaleAbs,folders,nomefiles in ModuloFiles.walk(root_locale,excludeFiles,excludeDirs,min_byte_size,max_byte_size):
			percorso_remoto_abs=ModuloFiles.normalizzaPercorsoRemoto(ModuloFiles.pathJoin(rootRemota,percorsoLocaleRel))
			# carico i file contenuti nella cartella corrente
			for nomefile in nomefiles:
				self.uploadFile(percorsoLocaleAbs,percorso_remoto_abs,nomefile,False)
				countFiles+=1
				yield FtpReturnBean(percorso_remoto_abs,nomefile,True,countFiles,countDirs)
			# upload folders
			for cartella in folders:
				cartella=ModuloFiles.normalizzaPercorsoRemoto(ModuloFiles.pathJoin(percorso_remoto_abs,cartella))
				try:
					self.conn.mkd(cartella)
				except Exception:
					pass
				countDirs+=1
				yield FtpReturnBean(percorso_remoto_abs,cartella,False,countFiles,countDirs)
	
	def uploadFile(self,percorso_locale,percorso_remoto,nomefile,renameIfExist)->str:
		nomefile_locale=ModuloFiles.pathJoin(percorso_locale,nomefile)
		nomefile_remoto=ModuloFiles.normalizzaPercorsoRemoto(ModuloFiles.pathJoin(percorso_remoto,nomefile))
		if renameIfExist is True:
			# se il file esiste gia' sul server gli aggiungo il timestamp
			if self.isFile(nomefile_remoto):
				nomefile_remoto=ModuloStringhe.aggiungiTimestamp(nomefile_remoto)
		# carico il file
		with open(nomefile_locale,'rb') as fp:
			self.conn.storbinary("STOR "+nomefile_remoto,fp)
		return nomefile_remoto
	
	def downloadCartella(self,percorso_remoto,percorso_locale,excludeFiles,excludeDirs):
		percorso_remoto=ModuloFiles.normalizzaPercorsoRemoto(percorso_remoto)
		return self.__downloadCartella(percorso_remoto,percorso_locale,excludeFiles,excludeDirs)
	
	def downloadFile(self,nomefile_server,nomefile_locale):
		nomefile_server=ModuloFiles.normalizzaPercorsoRemoto(nomefile_server)
		nomefile_locale=ModuloFiles.normalizzaPercorsoLocale(nomefile_locale)
		# creo le cartelle locali
		cartella_locale=os.path.dirname(nomefile_locale)
		os.makedirs(cartella_locale,exist_ok=True)
		# scarico il file
		with open(nomefile_locale,"wb") as fp:
			self.conn.retrbinary("RETR "+nomefile_server,fp.write)
	
	def eliminaCartella(self,percorso_remoto,excludeFiles,excludeDirs):
		percorso_remoto=ModuloFiles.normalizzaPercorsoRemoto(percorso_remoto)
		return self.__eliminaCartella(percorso_remoto,'.',excludeFiles,excludeDirs)
	
	def listaContenutoCartella(self,percorso_remoto):
		elementi = []
		if self.isFile(percorso_remoto) is True:
			return elementi
		if percorso_remoto.startswith(('.','/')) is False:
			percorso_remoto="./"+percorso_remoto
		cmd = "NLST -a "+percorso_remoto
		try:
			self.conn.retrlines(cmd, elementi.append)
			elementi.sort()
			# elimino . e ..
			elementi=elementi[2:]
		except ftplib.error_perm:
			pass
		return elementi
	
	def mkdirs(self,percorso_remoto):
		percorso_remoto=ModuloFiles.normalizzaPercorsoRemoto(percorso_remoto)
		dirs=ModuloListe.eliminaElementiVuoti(percorso_remoto.split("/"))
		percorso_corrente=""
		for cartella in dirs:
			percorso_corrente=ModuloFiles.normalizzaPercorsoRemoto(ModuloFiles.pathJoin(percorso_corrente,cartella))
			try:
				self.conn.mkd(percorso_corrente)
			except Exception:
				pass
	
	def chiudi(self):
		"""
		chiude la connessione
		"""
		if self.conn is None:
			return
		try:
			self.conn.quit()
		except Exception:
			self.conn.close()
		self.conn=None
	
	
	def getFileSize(self,nomefile):
		try:
			self.conn.voidcmd('TYPE I')
			size=self.conn.size(nomefile)
			return size
		except Exception:
			return
	
	def isFile(self,elemento):
		"""
		controlla se un oggetto e' un file o una cartella
		"""
		return self.getFileSize(elemento) is not None
	
	def goParentDir(self):
		# bisogna per forza usare 2 punti, se c'e' anche lo slash finale non funziona
		self.conn.cwd("..")
	
	'''
	FUNZIONI PRIVATE
	'''
	
	def __downloadCartella(self,percorso_remoto,percorso_locale,excludeFiles,excludeDirs,
			countFiles:int=0,countDirs:int=1):
		"""
		funzione ricorsiva
		"""
		# ciclo ogni elemento
		elementi=self.listaContenutoCartella(percorso_remoto)
		for elemento in elementi:
			elemento_rel_path=elemento
			if elemento_rel_path.startswith("/"):
				elemento_rel_path=elemento_rel_path[1:]
			elemento_remoto=ModuloFiles.normalizzaPercorsoRemoto(elemento)
			elemento_locale=ModuloFiles.pathJoin(percorso_locale,elemento_rel_path)
			# controllo se l'elemento e' un file o una cartella
			if self.isFile(elemento_remoto):
				os.makedirs(os.path.dirname(elemento_locale),exist_ok=True)
				if elemento_remoto not in excludeFiles:
					self.downloadFile(elemento_remoto,elemento_locale)
					countFiles+=1
					yield FtpReturnBean(percorso_remoto,elemento,True,countFiles,countDirs)
			else:
				countDirs+=1
				# creo la cartella
				if ModuloListe.stringContainsCollection(elemento_remoto,excludeDirs) is True:
					yield FtpReturnBean(percorso_remoto,elemento,True,countFiles,countDirs)
					break
				os.makedirs(elemento_locale,exist_ok=True)
				yield FtpReturnBean(percorso_remoto,elemento,False,countFiles,countDirs)
				# entro ed elaboro la sottocartella
				for bean in self.__downloadCartella(elemento_remoto,percorso_locale,excludeFiles,excludeDirs,
						countFiles,countDirs):
					countFiles=bean.countFiles
					countDirs=bean.countDirs
					yield bean
	
	def __eliminaCartella(self,rootRemota,percorsoRemotoRel,excludeFiles,excludeDirs):
		"""
		funzione ricorsiva
		"""
		# ciclo ogni elemento
		countFiles=countDirs=0
		elementi=self.listaContenutoCartella(percorsoRemotoRel)
		for elemento in elementi:
			elemento_remoto_rel=elemento
			elemento_remoto_abs=ModuloFiles.pathJoin("/",elemento)
			# controllo se e' un file o una cartella
			if self.isFile(elemento_remoto_abs):
				if ModuloListe.collectionContainsString(excludeDirs,percorsoRemotoRel) is False and elemento_remoto_rel not in excludeFiles:
					self.conn.delete(elemento_remoto_abs)
					countFiles+=1
					yield FtpReturnBean(percorsoRemotoRel,elemento,True,countFiles,countDirs)
			else:
				# entro ed elaboro la sottocartella
				if ModuloListe.collectionContainsString(excludeDirs,elemento_remoto_rel) is False:
					countFilesSubDir=countDirsSubDir=0
					for bean in self.__eliminaCartella(rootRemota,elemento_remoto_rel,excludeFiles,excludeDirs):
						countFilesSubDir=bean.countFiles+countFiles
						countDirsSubDir=bean.countDirs+countDirs
						bean.countFiles=countFilesSubDir
						bean.countDirs=countDirsSubDir
						yield bean
					countFiles=countFilesSubDir
					countDirs=countDirsSubDir
					# cancello la cartella dopo aver cancellato i file al suo interno
					if ModuloListe.collectionContainsString(excludeDirs,elemento_remoto_rel) is False:
						self.conn.rmd(elemento_remoto_abs)
						countDirs+=1
						yield FtpReturnBean(percorsoRemotoRel,elemento,False,countFiles,countDirs)
