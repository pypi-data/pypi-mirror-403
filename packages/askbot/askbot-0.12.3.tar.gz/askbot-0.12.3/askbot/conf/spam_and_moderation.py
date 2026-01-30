"""Settings for content moderation and spam control"""
from django.conf import settings as django_settings
from django.utils.translation import gettext_lazy as _
from livesettings import values as livesettings
from askbot import const
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import EXTERNAL_SERVICES

SPAM_AND_MODERATION = livesettings.ConfigurationGroup(
    'SPAM_AND_MODERATION',
    _('Akismet spam protection'),
    super_group=EXTERNAL_SERVICES
)

settings.register(
    livesettings.BooleanValue(
        SPAM_AND_MODERATION,
        'SPAM_FILTER_ENABLED',
        description=_('Enable spam filtering'),
        help_text=_('If enabled, posts classified as spam will be ignored.'),
        default=False
    )
)

AKISMET_SPAM_CHECKER_FUNCTION = 'askbot.spam_checker.akismet_spam_checker.is_spam'
if django_settings.ASKBOT_SPAM_CHECKER_FUNCTION == AKISMET_SPAM_CHECKER_FUNCTION:
    settings.register(
        livesettings.StringValue(
            SPAM_AND_MODERATION,
            'AKISMET_API_KEY',
            description=_('Akismet key for spam detection'),
            help_text=_(
                'To get an Akismet key please visit '
                '<a href="%(url)s">Akismet site</a>'
            ) % {'url': const.DEPENDENCY_URLS['akismet']}
        )
    )

ASKBOT_SPAM_CHECKER_FUNCTION = 'askbot.spam_checker.askbot_spam_checker.is_spam'
if django_settings.ASKBOT_SPAM_CHECKER_FUNCTION == ASKBOT_SPAM_CHECKER_FUNCTION:
    settings.register(
        livesettings.StringValue(
            SPAM_AND_MODERATION,
            'ASKBOT_SPAM_CHECKER_API_URL',
            description=_('Askbot spam checker API URL'),
            default='',
        )
    )

    settings.register(
        livesettings.StringValue(
            SPAM_AND_MODERATION,
            'ASKBOT_SPAM_CHECKER_API_KEY',
            description=_('Askbot spam checker API key'),
            default='',
        )
    )
