from django.conf import settings as django_settings
from askbot.utils.loading import load_function

is_spam = load_function(django_settings.ASKBOT_SPAM_CHECKER_FUNCTION)

def get_params_from_request(request):
    """Returns a dictionary of parameters to be passed to the spam checker"""
    username, email = None, None
    if request.user.is_authenticated:
        username = request.user.username
        email = request.user.email
    return {
        'username': username,
        'email': email,
        'ip_addr': request.META.get('REMOTE_ADDR', None),
        'user_agent': request.META.get('HTTP_USER_AGENT', None),
    }