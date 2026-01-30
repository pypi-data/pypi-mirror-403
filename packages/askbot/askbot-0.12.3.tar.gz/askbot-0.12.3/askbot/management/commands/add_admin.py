import sys
from django.core.management import BaseCommand
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save

class Command(BaseCommand):
    help = "Turn user into an administrator <user_id> is a numeric user id of the account"
    args = '<user id>'

    def add_arguments(self, parser):
        parser.add_argument('user_id',
            help="the numeric user_id of the existing user that shall become an admin")
        parser.add_argument('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells to NOT prompt the user for input of any kind.')

    def get_user(self, uid_str):
        try:
            uid = int(uid_str)
            return User.objects.get(id=uid)
        except User.DoesNotExist: # pylint: disable=no-member
            print(f'sorry there is no user with id={uid}')
            sys.exit(1)
        except ValueError:
            print(f'user id must be integer, have {uid_str}')
            sys.exit(1)

    def confirm_action(self):
        usr = self.user
        print('')
        prompt = f'Do you really wish to make user (id={usr.id}, ' + \
                 f'name={usr.username}) a site administrator? yes/no: '
        if input(prompt) != 'yes':
            print('action canceled')
            sys.exit(1)

    def remove_signals(self):
        pre_save.receivers = []
        post_save.receivers = []

    def handle(self, *arguments, **options): # pylint: disable=unused-argument
        #destroy pre_save and post_save signals
        #self.parse_arguments(arguments)
        if options.get('user_id') is None:
            print('argument for this command id <user_id>')
            sys.exit(1)
        self.user = self.get_user(options.get('user_id')) # pylint: disable=attribute-defined-outside-init

        if options.get('interactive') is True:
            self.confirm_action()

        self.remove_signals()

        self.user.is_active = True
        self.user.set_status('d')
        self.user.save()
