from abc import ABC

class AbstractPdf(ABC):
	
	def __init__(self):
		self.pdfObj=None
	
	def close(self):
		self.pdfObj.close()
