# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

from contextvars import ContextVar

request_ctx = ContextVar('zato_django_request', default=None)

def set_request(request):
    request_ctx.set(request)

def get_request():
    return request_ctx.get()

def clear_request():
    request_ctx.set(None)
