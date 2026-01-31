from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('constec_db', '0002_module_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='module',
            name='level',
        ),
    ]
