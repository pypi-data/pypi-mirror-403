"""Custom built spam checker for Askbot"""
import logging
import requests
from django.conf import settings as django_settings

def is_spam(text, **kwargs): # pylint: disable=unused-argument
    """Returns True if the text is spam, `kwargs` are ignored.
    If there is an error while calling the spam checker API, it returns False.
    The reason for the latter is that we don't want to block the user from posting.
    If the admin enables the moderation queue, the post will be sent to the queue.
    """
    try:
        api_key = django_settings.ASKBOT_SPAM_CHECKER_API_KEY
        api_url = django_settings.ASKBOT_SPAM_CHECKER_API_URL
        timeout = django_settings.ASKBOT_SPAM_CHECKER_TIMEOUT_SECONDS
        data = {"api_key": api_key, "text": text}
        response = requests.post(api_url, json=data, timeout=timeout)
    except Exception as error: # pylint: disable=broad-except
        logging.critical('Error while calling spam checker API %s', str(error))
        return False

    try:
        if response.status_code == 200:
            return response.json()["spam_score"] > 0.5
    except Exception as error: # pylint: disable=broad-except
        logging.critical('Error while parsing spam checker API response %s', str(error))
        return False

    return False
