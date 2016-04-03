from .models import QuailUser, CASClient

## TODO: inline the CAS authentication here, since this essentially does nothing right now. 
class QuailCustomBackend(object):

	def authenticate(self, username=None, password=None):

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
