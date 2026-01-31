# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

from django.conf import settings

def get_url():
    return getattr(settings, 'ZATO_URL', 'http://localhost:17010/django')

def get_username():
    return getattr(settings, 'ZATO_USERNAME', 'django')

def get_password():
    return getattr(settings, 'ZATO_PASSWORD', '')
