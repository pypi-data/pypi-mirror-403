from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import activate as activate_language
from askbot import const
from askbot.mail.messages import InstantEmailAlert
from askbot.models import Activity, Post, User
from askbot import exceptions as askbot_exceptions

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--post-id', type=int, dest='post_id', required=True)
        parser.add_argument('--user-id', default=None, type=int, dest='user_id')
        parser.add_argument('--email', default=None, type=str, dest='email')

    def handle(self, *args, **options):
        post = self.get_post(options['post_id'])
        user = self.get_user(options['user_id'], options['email'])
        recipient_email = self.get_email(user, options['email'])
        update_activity = self.get_latest_edit_activity(post)
        activate_language(post.language_code)

        email = InstantEmailAlert({
            'to_user': user,
            'from_user': update_activity.user,
            'post': post,
            'update_activity': update_activity
        })
        try:
            email.send([recipient_email])
        except askbot_exceptions.EmailNotSent as error:
            raise CommandError('%s, error=%s', recipient_email, error)
        else:
            print(f'Email sent to {recipient_email}')

    def get_latest_edit_activity(self, post):
        """Returns the latest edit activity for the post"""
        content_type = ContentType.objects.get_for_model(post)
        act_types = const.RESPONSE_ACTIVITY_TYPES_FOR_INSTANT_NOTIFICATIONS
        act_qs = Activity.objects.filter(content_type=content_type,
                                         object_id=post.id,
                                         activity_type__in=act_types)
        return act_qs.latest('id')

    def get_post(self, post_id):
        try:
            assert type(post_id) == int
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise CommandError('Post with id=%s does not exist' % post_id)
        except AssertionError:
            raise CommandError('value of --post-id must be an integer')

    def get_user(self, user_id, email):
        """If there is no user_id, then use email to find the user"""
        # either user_id or email must be provided
        if user_id is None and email is None:
            raise CommandError('Either --recipient-user-id or --recipient-email must be provided')
        if user_id:
            try:
                assert type(user_id) == int
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f'User with id={user_id} does not exist')
            except AssertionError:
                raise CommandError('value of --recipient-user-id must be an integer')

        try:
            validate_email(email)
        except ValidationError:
            raise CommandError(f'Value of --recipient-email is not a valid email address: {email}')

        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'User with email={email} does not exist')

    def get_email(self, user, email):
        if not email:
            return user.email
        return email