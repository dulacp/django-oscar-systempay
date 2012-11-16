#!/usr/bin/env python
import sys
from coverage import coverage
from optparse import OptionParser

from django.conf import settings

if not settings.configured:
    extra_settings = {
        'SYSTEMPAY_SANDBOX_MODE': True,
    }
    # To specify integration settings (which include passwords, hence why they
    # are not committed), create an integration.py module.
    try:
        from integration import *
    except ImportError:
        extra_settings.update({
            'SYSTEMPAY_SITE_ID': '12345678',
            'SYSTEMPAY_CERTIFICATE': '1122334455667788',
        })
    else:
        for key, value in locals().items():
            if key.startswith('SYSTEMPAY'):
                extra_settings[key] = value

    from oscar.defaults import *
    for key, value in locals().items():
        if key.startswith('OSCAR'):
            extra_settings[key] = value
    extra_settings['OSCAR_ALLOW_ANON_CHECKOUT'] = True

    from oscar import get_core_apps, OSCAR_MAIN_TEMPLATE_DIR

    settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    }
                },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'django.contrib.flatpages',
                'systempay',
                'south',
                ] + get_core_apps(),
            MIDDLEWARE_CLASSES=(
                'django.middleware.common.CommonMiddleware',
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.messages.middleware.MessageMiddleware',
                'django.middleware.transaction.TransactionMiddleware',
                'oscar.apps.basket.middleware.BasketMiddleware',
            ),
            DEBUG=False,
            SOUTH_TESTS_MIGRATE=False,
            HAYSTACK_CONNECTIONS={
                'default': {
                    'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
                },
            },
            TEMPLATE_DIRS=(OSCAR_MAIN_TEMPLATE_DIR,),
            SITE_ID=1,
            ROOT_URLCONF='tests.urls',
            NOSE_ARGS=['-s', '--with-spec'],
            **extra_settings
        )

from django_nose import NoseTestSuiteRunner


def run_tests(*test_args):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['tests']

    # Run tests
    test_runner = NoseTestSuiteRunner(verbosity=1)

    c = coverage(source=['systempay'], omit=['*migrations*', '*tests*'])
    c.start()
    num_failures = test_runner.run_tests(test_args)
    c.stop()

    if num_failures > 0:
        sys.exit(num_failures)
    print "Generating HTML coverage report"
    c.html_report()


def generate_migration():
    from south.management.commands.schemamigration import Command
    com = Command()
    com.handle(app='systempay', initial=True)


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
