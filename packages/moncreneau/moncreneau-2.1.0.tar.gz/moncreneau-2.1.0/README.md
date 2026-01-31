# Moncreneau Python SDK

Official Moncreneau API client for Python.

[![PyPI version](https://img.shields.io/pypi/v/moncreneau.svg)](https://pypi.org/project/moncreneau/)
[![Python versions](https://img.shields.io/pypi/pyversions/moncreneau.svg)](https://pypi.org/project/moncreneau/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install moncreneau
```

## Quick Start

```python
from moncreneau import Moncreneau

client = Moncreneau('mk_live_YOUR_API_KEY')

# Create an appointment
appointment = client.appointments.create(
    department_id=5,  # Integer: ID du département
    date_time='2026-01-20T10:00:00',
    name='Jean Dupont'  # Nom du bénéficiaire
)

print(appointment['id'])  # 123
```

## Documentation

Full documentation available at: [https://moncreneau-docs.vercel.app/docs/v1/sdks/python](https://moncreneau-docs.vercel.app/docs/v1/sdks/python)

## Features

- ✅ Full type hints support
- ✅ Automatic error handling
- ✅ Webhook signature verification
- ✅ Comprehensive documentation
- ✅ Python 3.7+ support

## Usage

### Configuration

```python
client = Moncreneau(
    api_key='mk_live_...',
    base_url='https://mc-prd.duckdns.org/api/v1',  # optional
    timeout=30  # optional, in seconds
)
```

### Appointments

```python
# Create
appointment = client.appointments.create(
    department_id=5,  # Integer: ID du département
    date_time='2026-01-20T10:00:00',
    name='Jean Dupont'  # Nom du bénéficiaire
)

# List
appointments = client.appointments.list(
    page=0,
    size=20,
    status='SCHEDULED'
)

# Retrieve
appointment = client.appointments.retrieve('appt_abc123')

# Cancel
client.appointments.cancel('appt_abc123')
```

### Departments

```python
# List departments
departments = client.departments.list()

# Get availability
availability = client.departments.get_availability(
    'dept_123',
    start_date='2026-01-20',
    end_date='2026-01-27'
)
```

### Error Handling

```python
from moncreneau import Moncreneau, MoncreneauError

try:
    appointment = client.appointments.create(...)
except MoncreneauError as error:
    print(f'Code: {error.code}')
    print(f'Message: {error.message}')
    print(f'Status: {error.status_code}')
    print(f'Details: {error.details}')
```

### Webhooks

```python
from moncreneau import Moncreneau

# In your Flask/Django/FastAPI endpoint
@app.route('/webhooks/moncreneau', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Webhook-Signature')
    
    is_valid = Moncreneau.verify_webhook_signature(
        request.json,
        signature,
        os.getenv('WEBHOOK_SECRET')
    )
    
    if not is_valid:
        return 'Invalid signature', 401
    
    # Process webhook
    event = request.json
    print(f"Event type: {event['type']}")
    
    return 'OK', 200
```

## Examples

### Flask Application

```python
from flask import Flask, request, jsonify
from moncreneau import Moncreneau, MoncreneauError
import os

app = Flask(__name__)
client = Moncreneau(os.getenv('MONCRENEAU_API_KEY'))

@app.route('/appointments', methods=['POST'])
def create_appointment():
    try:
        appointment = client.appointments.create(
            department_id=request.json['departmentId'],
            date_time=request.json['dateTime'],
            user_name=request.json['userName'],
            user_phone=request.json['userPhone']
        )
        return jsonify(appointment)
    except MoncreneauError as error:
        return jsonify({
            'error': error.code,
            'message': error.message
        }), error.status_code
```

### Django View

```python
from django.http import JsonResponse
from moncreneau import Moncreneau, MoncreneauError
import json
import os

client = Moncreneau(os.getenv('MONCRENEAU_API_KEY'))

def create_appointment(request):
    try:
        data = json.loads(request.body)
        appointment = client.appointments.create(
            department_id=data['departmentId'],
            date_time=data['dateTime'],
            user_name=data['userName'],
            user_phone=data['userPhone']
        )
        return JsonResponse(appointment)
    except MoncreneauError as error:
        return JsonResponse({
            'error': error.code,
            'message': error.message
        }, status=error.status_code)
```

## Support

- **Documentation**: [https://moncreneau-docs.vercel.app](https://moncreneau-docs.vercel.app)
- **PyPI**: [https://pypi.org/project/moncreneau](https://pypi.org/project/moncreneau)
- **Email**: moncreneau.rdv@gmail.com
- **Issues**: [GitHub Issues](https://github.com/nbsidiki/moncreneau-python/issues)

## License

MIT © Moncreneau
