import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
	sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from accounts.models import User
from rest_framework_simplejwt.tokens import AccessToken

username = os.environ.get('GEN_TOKEN_USER', 'ryu04100')
user = User.objects.get(username=username)
print('USER', user.id, user.username)
print('ACCESS', str(AccessToken.for_user(user)))
