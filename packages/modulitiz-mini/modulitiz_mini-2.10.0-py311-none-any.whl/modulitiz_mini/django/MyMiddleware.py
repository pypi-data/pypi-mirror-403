class MyMiddleware(object):
	
	def __init__(self, getResponse):
		self.getResponse = getResponse
	
	def __call__(self, request):
		response = self.getResponse(request)
		# allow iframe tag to be loaded
		response['X-Frame-Options'] = 'SAMEORIGIN'
		return response
