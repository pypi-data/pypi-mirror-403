# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

from django_zato.ctx import clear_request, set_request

class ZatoMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request(request)
        try:
            response = self.get_response(request)
        finally:
            clear_request()
        return response
