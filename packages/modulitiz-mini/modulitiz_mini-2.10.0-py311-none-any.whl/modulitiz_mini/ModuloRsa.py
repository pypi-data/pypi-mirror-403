from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from modulitiz_nano.ModuloStringhe import ModuloStringhe


class ModuloRsa(object):
	DEFAULT_HASH_TYPE=hashes.SHA256()
	KEY_SIZE=4096
	
	NOMEFILE_PUBLIC_KEY="public.key"
	NOMEFILE_PRIVATE_KEY="private.key"
	
	def __init__(self):
		self.publicKey:RSAPublicKey|None=None
		self.privateKey:RSAPrivateKey|None=None
		
	def generateKeys(self):
		self.privateKey = rsa.generate_private_key(
			public_exponent=65537, key_size=self.KEY_SIZE, backend=default_backend()
		)
		self.publicKey = self.privateKey.public_key()
	
	#
	# save
	#
	def savePublicKey(self,nomefile=NOMEFILE_PUBLIC_KEY):
		pem = self.publicKey.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
		)
		with open(nomefile, 'wb') as fp:
			fp.write(pem)
	
	def savePrivateKey(self, nomefile=NOMEFILE_PRIVATE_KEY):
		pem = self.privateKey.private_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PrivateFormat.TraditionalOpenSSL,
			encryption_algorithm=serialization.NoEncryption()
		)
		with open(nomefile, 'wb') as fp:
			fp.write(pem)
	
	#
	# read
	#
	def readPublicKey(self,nomefile=NOMEFILE_PUBLIC_KEY):
		with open(nomefile, "rb") as fp:
			pem=fp.read()
		self.publicKey = serialization.load_pem_public_key(pem, backend=default_backend())
	
	def readPrivateKey(self,nomefile=NOMEFILE_PRIVATE_KEY):
		with open(nomefile, "rb") as fp:
			pem=fp.read()
		self.privateKey = serialization.load_pem_private_key(pem, password=None, backend=default_backend())
	
	
	def encrypt(self,messaggio):
		encryptedMsg = self.publicKey.encrypt(
			messaggio.encode(ModuloStringhe.CODIFICA_UTF8),
			self.__generatePadding()
		)
		return encryptedMsg
	
	def decrypt(self,encryptedMsg):
		originalMessage = self.privateKey.decrypt(
			encryptedMsg,
			self.__generatePadding()
		).decode(ModuloStringhe.CODIFICA_UTF8)
		return originalMessage
	
	def __generatePadding(self):
		hashType=self.DEFAULT_HASH_TYPE
		paddingObj=padding.OAEP(
			mgf=padding.MGF1(algorithm=hashType),
			algorithm=hashType,
			label=None
		)
		return paddingObj
