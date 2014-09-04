#!/usr/bin/env python
import os
import sys

import django
from django.test.utils import setup_test_environment
from django.utils import unittest


os.environ['DJANGO_SETTINGS_MODULE'] = 'WhatManager2.settings'

if __name__ == '__main__':
    setup_test_environment()
    django.setup()

    suite = unittest.TestLoader().discover('integration_tests')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
