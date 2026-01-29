import pypdf

from modulitiz_mini.files.pdf.AbstractPdf import AbstractPdf


class WritePdf(AbstractPdf):
	
	def __init__(self):
		super().__init__()
		self.pdfObj=pypdf.PdfWriter()
	
	def write(self,filename:str):
		with open(filename,"wb") as outStream:
			self.pdfObj.write(outStream)
