# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

from django_zato.client import ZatoClient

client = ZatoClient()

__all__ = ['client', 'ZatoClient']
