from django.db import migrations
from django.utils import translation
from django.utils.translation import gettext as _
from askbot import const

def forwards(apps, schema_editor):
    Thread = apps.get_model('askbot', 'Thread')
    db_alias = schema_editor.connection.alias
    closed_threads = Thread.objects.using(db_alias).filter(closed=True)
    closed_threads = closed_threads.only('id', 'language_code', 'close_reason', 'closed')
    for thread in closed_threads.iterator():
        translation.activate(thread.language_code)
        #reasons are 1-indexed, but the list is 0-indexed
        reason_text = _(const.CLOSE_REASONS[thread.close_reason - 1][1])
        thread.close_reason_text = reason_text
        thread.save()


class Migration(migrations.Migration):
    
        dependencies = [
            ('askbot', '0023_auto_20230724_0132'),
        ]
    
        operations = [
            migrations.RunPython(forwards),
        ]

