# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

import uuid

import requests
from requests.auth import HTTPBasicAuth

from django_zato import settings
from django_zato.ctx import get_request

class ZatoClient:

    def invoke(self, service, data=None, request=None):
        """
        Invoke a Zato service.

        Args:
            service: Name of the service to invoke
            data: Request data (dict or string)
            request: Optional Django request for context propagation

        Returns:
            Response data from the service
        """
        url = settings.get_url()
        username = settings.get_username()
        password = settings.get_password()

        headers = self._build_headers(request)

        params = {'service': service}

        response = requests.post(
            url,
            json=data,
            params=params,
            auth=HTTPBasicAuth(username, password),
            headers=headers,
        )

        response.raise_for_status()

        return response.json()

    def _build_headers(self, request=None):
        """
        Build headers for the request, including propagated context.
        """
        if request is None:
            request = get_request()

        headers = {}

        if request is None:
            return headers

        if hasattr(request, 'user') and request.user.is_authenticated:
            headers['X-Zato-User'] = str(request.user.username)

        correlation_id = request.META.get('HTTP_X_ZATO_CORRELATION_ID')
        if not correlation_id:
            correlation_id = uuid.uuid4().hex
        headers['X-Zato-Correlation-Id'] = correlation_id

        forwarded_for = request.META.get('REMOTE_ADDR')
        if forwarded_for:
            headers['X-Zato-Forwarded-For'] = forwarded_for

        return headers
