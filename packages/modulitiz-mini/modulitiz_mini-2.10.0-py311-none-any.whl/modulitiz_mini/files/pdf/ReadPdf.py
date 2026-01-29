import pypdf

from modulitiz_mini.files.pdf.AbstractPdf import AbstractPdf
from modulitiz_nano.exceptions.ExceptionRuntime import ExceptionRuntime


class ReadPdf(AbstractPdf):
	
	def __init__(self,filename:str):
		super().__init__()
		self.filename=filename
		self.pdfObj=pypdf.PdfReader(open(filename,"rb"))
	
	def getNumPages(self)->int:
		return len(self.pdfObj.pages)
	
	def getPage(self,pageNum:int):
		"""
		Read a page from a pdf file.
		:param pageNum: pages start with 0 and including extremes.
		"""
		pageNum-=1
		maxPages=self.getNumPages()
		# check if page exist
		if pageNum<0 or pageNum>=maxPages:
			raise ExceptionRuntime("Page number {0} not exists.".format(pageNum))
		return self.pdfObj.pages[pageNum]
