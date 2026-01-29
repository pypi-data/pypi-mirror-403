"""
python manage.py collectstatic
python manage.py runserver 0.0.0.0:80
"""

from modulitiz_nano.ModuloStringhe import ModuloStringhe


class ModuloDjango(object):
	@staticmethod
	def isLocalhost(request)->bool:
		return ModuloStringhe.contains(request.path, 'localhost') or ModuloStringhe.contains(request.path, '127.0.0.1')
	
	@classmethod
	def init_modelmap(cls,request,pageTitle:str)->dict:
		modelMap = {
			'page_title': pageTitle,
			'is_localhost': cls.isLocalhost(request)
		}
		return modelMap
