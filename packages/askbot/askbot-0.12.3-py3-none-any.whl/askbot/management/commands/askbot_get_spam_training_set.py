"""Outputs a JSON file: {"spam": [...], "ham": [...]}
ham - legitimate posts
spam - spam posts
"""
import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from askbot.models import Post, User
from askbot import const

POST_TYPES = ('question', 'answer', 'comment')

def get_content(posts):
    """Returns list with markdown source of the posts"""
    return [post.text for post in posts]

class Command(BaseCommand):
    """The management command class"""

    def add_arguments(self, parser):
        """Defines command line arguments"""

        parser.add_argument('--output', dest='file_name',
                            nargs='?', default='./spam-ham.json',
                            help='Path to the output file')

        parser.add_argument('--min-rep', dest='min_rep',
                            nargs='?', default=10, type=int,
                            help="Minimum reputation of the user to select ham posts")

        parser.add_argument('--size', dest='size',
                            nargs='?', default=3000, type=int,
                            help="Maximum number of ham and spam posts to output")


    def handle(self, *args, **kwargs):
        # get users with reputation more than min rep

        if os.path.exists(kwargs['file_name']):
            raise CommandError(f'File {kwargs["file_name"]} already exists')

        users = User.objects.filter(askbot_profile__reputation__gte=kwargs['min_rep'])
        users = users.order_by('-askbot_profile__reputation')
        ham = self.get_content_sample(users, kwargs['size'])

        users = User.objects.filter(askbot_profile__reputation=const.MIN_REPUTATION,
                                    askbot_profile__status='b')
        users = users.annotate(post_count=Count('posts'))
        users = users.filter(post_count=1)
        spam = self.get_content_sample(users, kwargs['size'])
        self.print_output(spam, ham, kwargs["file_name"])


    def get_content_sample(self, users, size):
        """Returns list of ham posts"""
        # if total number of posts from these users is less than size,
        # then we can just take all of them
        # otherwise, loop over users until we grab "size" number of posts
        all_posts = Post.objects.filter(author__in=users, post_type__in=POST_TYPES)

        if all_posts.count() <= size:
            return get_content(all_posts.only('text'))

        users_count = users.count()
        ham_post_ids = []
        bad_user_ids = []
        index = 0
        while len(ham_post_ids) < size:
            if len(ham_post_ids) % 100 == 0:
                print(f'post {len(ham_post_ids) + 1}')

            if index in bad_user_ids:
                index = (index + 1) % users_count
                continue

            user = users[index]
            post = user.posts.exclude(pk__in=ham_post_ids).filter(post_type__in=POST_TYPES).only('pk').first()
            if post:
                ham_post_ids.append(post.pk)
                index = (index + 1) % users_count
            else:
                bad_user_ids.append(index)

        ham_posts = Post.objects.filter(pk__in=ham_post_ids).only('text')
        return get_content(ham_posts)


    def print_output(self, spam, ham, file_name):
        """Creates the output file as array in python format,
        new post starts with new line."""
        with open(file_name, 'w', encoding='utf-8') as output_file:
            output_file.write(json.dumps({'spam': spam, 'ham': ham}, indent=2))
