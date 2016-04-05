from .models import QuailUser, CASClient
from django.core.exceptions import ObjectDoesNotExist

class QuailCustomBackend(object):

	def authenticate(self, username=None, password=None, request=None):

		# is the user logged into CAS?
		# C = CASClient(request)
		# if 'ticket' in request.GET:
		# 	netid = C.Authenticate()
		# 	if not netid:
		# 		return None
		# 	if netid != username:
		# 		return None

		try:
			user = QuailUser.objects.get(netid=username)
		except ObjectDoesNotExist:
			return None
		return user

	def get_user(self, user_id):
		try:
			return QuailUser.objects.get(pk=user_id)
		except ObjectDoesNotExist:
			return None
