from django.conf import settings
from django.test import TestCase

class StoatTestCase(TestCase):
    fixtures = ['stoat_test_data.json']
    urls = 'stoat.tests.urls'

    def setUp(self):
        self.OLD_TINYCMS_TEMPLATES = getattr(settings, 'TINYCMS_TEMPLATES')
        settings.TINYCMS_TEMPLATES = {
            'Default': ('stoat/tests/default.html', (
                ('Body',            'text'),
                ('Sidebar Heading', 'char'),
                ('Sidebar Body',    'text'),
            )),
            'Other': ('stoat/tests/other.html', (
                ('Body',            'text'),
                ('Test Int',        'int'),
            )),
            'Navigation': ('stoat/tests/navigation.html', (
            )),
        }

        self.OLD_TINYCMS_DEFAULT_TEMPLATE = getattr(settings, 'TINYCMS_DEFAULT_TEMPLATE')
        settings.TINYCMS_DEFAULT_TEMPLATE = 'Default'

        self.OLD_INSTALLED_APPS = getattr(settings, 'INSTALLED_APPS')
        settings.INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'stoat',)

        self.OLD_MIDDLEWARE_CLASSES = getattr(settings, 'MIDDLEWARE_CLASSES')
        settings.MIDDLEWARE_CLASSES = (
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'stoat.middleware.StoatMiddleware',)

    def tearDown(self):
        settings.TINYCMS_TEMPLATES = self.OLD_TINYCMS_TEMPLATES
        settings.TINYCMS_DEFAULT_TEMPLATE = self.OLD_TINYCMS_DEFAULT_TEMPLATE
        settings.INSTALLED_APPS = self.OLD_INSTALLED_APPS
        settings.MIDDLEWARE_CLASSES = self.OLD_MIDDLEWARE_CLASSES


def get(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

