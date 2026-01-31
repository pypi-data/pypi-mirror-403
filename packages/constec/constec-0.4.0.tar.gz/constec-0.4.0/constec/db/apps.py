from django.apps import AppConfig


class ConstecDbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'constec.db'
    label = 'constec_db'
    verbose_name = 'Constec Database Models'
