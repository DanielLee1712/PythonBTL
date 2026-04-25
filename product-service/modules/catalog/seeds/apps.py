from django.apps import AppConfig


class SeedsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.catalog.seeds'
    label = 'catalog_seeds'
    verbose_name = 'Catalog Seeds'
