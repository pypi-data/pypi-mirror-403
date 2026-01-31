# django-zato-plugin

A client library for invoking Zato services from Django applications.

Zato is an integration platform that orchestrates and automates your to APIs, databases, queues, and other systems.

Learn more here: https://zato.io

With this plugin, Django delegates integration work to Zato - your views call Zato services,
Zato handles the rest. Less code in Django, all integrations in one place.

## Installation

```bash
pip install django-zato-plugin
```

## Configuration

Add to your Django settings:

```python
ZATO_URL = 'http://localhost:11223/django'
ZATO_USERNAME = 'django'
ZATO_PASSWORD = 'password' # Use your Zato password, e.g. from the Zato_Password env. variable
```

## Usage

```python
# views.py
from django.http import JsonResponse
from django_zato import client

def block_ip(request):

    # Get request data
    ip_address = request.POST['ip_address']
    reason = request.POST['reason']

    # Block on firewall
    client.invoke('firewall.block-ip', {'ip_address': ip_address})

    # Log incident in SIEM
    client.invoke('siem.log-incident', {
        'ip_address': ip_address,
        'reason': reason,
        'action': 'blocked',
    })

    return JsonResponse({'status': 'ok'})
```
