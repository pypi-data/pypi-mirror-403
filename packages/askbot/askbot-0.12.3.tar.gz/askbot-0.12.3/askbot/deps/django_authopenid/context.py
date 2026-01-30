from django.conf import settings as django_settings
from askbot.utils.functions import encode_jwt
from askbot.utils import forms
from .forms import LoginForm
from .util import get_unique_enabled_login_provider, is_signin_page_used

def get_after_login_url(request):
    """returns url where user should go after successful login"""
    #next_url is first priority value of "next"
    #second priority - LOGIN_REDIRECT_URL
    #third priority - current page
    login_redirect = getattr(django_settings, 'LOGIN_REDIRECT_URL', None)
    if login_redirect in (None, django_settings.ASKBOT_URL):
        #after login stay on current page
        default_next = request.path
    else:
        #after login go to the special page
        default_next = login_redirect
    return forms.get_next_url(request, default_next)

def login_context(request):
    """Context necessary for the login functionality
    for the edge case when there is only one login provider.

    In that case the signin page is not necessary, and the login
    form is displayed in the site header.

    See `jinja2/components/login_link.html`.
    """
    # guards against use of this context outside of the mentioned edge case
    if is_signin_page_used():
        return {}

    next_url = get_after_login_url(request)
    next_jwt = encode_jwt({'next_url': next_url})
    return {
        'unique_enabled_login_provider': get_unique_enabled_login_provider(),
        'login_form': LoginForm(initial={'next': next_jwt})
    }
