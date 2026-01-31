from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('constec_db', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='level',
            field=models.CharField(
                choices=[('organization', 'Organization Level'), ('company', 'Company Level')],
                default='company',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='OrganizationModule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('settings', models.JSONField(blank=True, default=dict)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_modules', to='constec_db.module')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_modules', to='constec_db.organization')),
            ],
            options={
                'db_table': 'core"."organization_modules',
                'unique_together': {('organization', 'module')},
            },
        ),
    ]
