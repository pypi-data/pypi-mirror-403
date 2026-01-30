# Hyphen Python SDK

The official Python SDK for [Hyphen](https://hyphen.ai) - providing feature toggles, IP geolocation, and link shortening services.

## Installation

```bash
pip install hyphen
```

For development:
```bash
pip install hyphen[dev]
```

## Quick Start

### Environment Variables

You can set API credentials using environment variables:

```bash
export HYPHEN_API_KEY="your_api_key"
export HYPHEN_PUBLIC_API_KEY="your_public_api_key"
export HYPHEN_APPLICATION_ID="your_application_id"
export HYPHEN_ORGANIZATION_ID="your_organization_id"
```

## Feature Toggles

Manage feature flags for your application with targeting support.

* [Website](https://hyphen.ai)
* [Guides](https://docs.hyphen.ai)

### Basic Usage

```python
from hyphen import FeatureToggle, ToggleContext

toggle = FeatureToggle(
    application_id='your_application_id',
    api_key='your_api_key',
    environment='production',  # Optional, defaults to HYPHEN_ENVIRONMENT or "production"
)

# Get a boolean toggle with default value
enabled = toggle.get_boolean('my-feature', default=False)
print('Feature enabled:', enabled)
```

### Targeting Context

Use targeting context to evaluate toggles based on user attributes:

```python
from hyphen import FeatureToggle, ToggleContext

# Set a default context for all evaluations
toggle = FeatureToggle(
    application_id='your_application_id',
    api_key='your_api_key',
    default_context=ToggleContext(
        targeting_key='user_123',
        user={'id': 'user_123', 'email': 'user@example.com'},
    )
)

# Or pass context per request
context = ToggleContext(
    targeting_key='user_456',
    ip_address='192.168.1.1',
    custom_attributes={'plan': 'premium', 'beta_tester': True}
)
enabled = toggle.get_boolean('premium-feature', default=False, context=context)
```

### Type-Safe Toggle Methods

```python
from hyphen import FeatureToggle

toggle = FeatureToggle(
    application_id='your_application_id',
    api_key='your_api_key',
)

# Boolean toggles
enabled = toggle.get_boolean('feature-flag', default=False)

# String toggles
theme = toggle.get_string('ui-theme', default='light')

# Numeric toggles
max_items = toggle.get_number('max-items', default=10)

# JSON object toggles
config = toggle.get_object('feature-config', default={'enabled': False})
```

### Get Multiple Toggles

```python
from hyphen import FeatureToggle

toggle = FeatureToggle(
    application_id='your_application_id',
    api_key='your_api_key',
)

toggles = toggle.get_toggles(['feature-a', 'feature-b', 'feature-c'])
print('Toggles:', toggles)  # {'feature-a': True, 'feature-b': 42, 'feature-c': 'enabled'}
```

### Error Handling

```python
from hyphen import FeatureToggle

def handle_toggle_error(error):
    print(f'Toggle evaluation failed: {error}')

toggle = FeatureToggle(
    application_id='your_application_id',
    api_key='your_api_key',
    on_error=handle_toggle_error,  # Errors call this instead of raising
)

# Returns default value on error instead of raising
enabled = toggle.get_boolean('my-feature', default=False)
```

Toggles support multiple data types:
- Boolean: `True` or `False`
- Number: `42` (int or float)
- String: `"Hello World!"`
- JSON: `{"id": "Hello World!"}`

## NetInfo - IP Geolocation

Look up IP address geolocation information.

* [Website](https://hyphen.ai)
* [Guides](https://docs.hyphen.ai)

### Get Single IP Information

```python
from hyphen import NetInfo

net_info = NetInfo(api_key='your_api_key')

ip_info = net_info.get_ip_info('8.8.8.8')
print('IP Info:', ip_info)
```

### Get Multiple IP Information

```python
from hyphen import NetInfo

net_info = NetInfo(api_key='your_api_key')

ips = ['8.8.8.8', '1.1.1.1']
ip_infos = net_info.get_ip_infos(ips)
print('IP Infos:', ip_infos)
```

## Link - Short Code Service

Create and manage short URLs and QR codes.

* [Website](https://hyphen.ai/link)
* [Guides](https://docs.hyphen.ai/docs/create-short-link)
* [API Reference](https://docs.hyphen.ai/reference/post_api-organizations-organizationid-link-codes)

### Creating a Short Code

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.create_short_code(
    long_url='https://hyphen.ai',
    domain='test.h4n.link',
    options={
        'tags': ['sdk-test', 'unit-test'],
    }
)
print('Short Code Response:', response)
```

### Updating a Short Code

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.update_short_code(
    code='code_1234567890',
    options={
        'title': 'Updated Short Code',
        'tags': ['sdk-test', 'unit-test'],
        'long_url': 'https://hyphen.ai/updated',
    }
)
print('Update Response:', response)
```

### Getting a Short Code

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.get_short_code('code_1234567890')
print('Short Code:', response)
```

### Getting Short Codes

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.get_short_codes(
    title='My Short Codes',
    tags=['sdk-test', 'unit-test']
)
print('Short Codes:', response)
```

### Getting Organization Tags

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

tags = link.get_tags()
print('Tags:', tags)
```

### Get Short Code Stats

```python
from hyphen import Link
from datetime import datetime

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

stats = link.get_short_code_stats(
    code='code_1234567890',
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)
print('Stats:', stats)
```

### Deleting a Short Code

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.delete_short_code('code_1234567890')
print('Delete Response:', response)
```

### Creating a QR Code

```python
from hyphen import Link, QrSize

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.create_qr_code(
    code='code_1234567890',
    options={
        'title': 'My QR Code',
        'backgroundColor': '#ffffff',
        'color': '#000000',
        'size': QrSize.MEDIUM,
    }
)
print('QR Code:', response)
```

### Get QR Code by ID

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.get_qr_code('code_1234567890', 'qr_1234567890')
print('QR Code:', response)
```

### Get QR Codes for a Short Code

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.get_qr_codes('code_1234567890')
print('QR Codes:', response)
```

### Deleting a QR Code

```python
from hyphen import Link

link = Link(
    organization_id='your_organization_id',
    api_key='your_api_key',
)

response = link.delete_qr_code('code_1234567890', 'qr_1234567890')
print('Delete Response:', response)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/Hyphen/python-sdk.git
cd python-sdk

# Install dependencies
pip install -e ".[dev]"
```

### Testing

Create a `.env` file with your test credentials:

```bash
HYPHEN_PUBLIC_API_KEY=your_public_api_key
HYPHEN_API_KEY=your_api_key
HYPHEN_APPLICATION_ID=your_application_id
HYPHEN_LINK_DOMAIN=your_link_domain
HYPHEN_ORGANIZATION_ID=your_organization_id
```

Run tests:

```bash
pytest
```

### Linting

```bash
ruff check hyphen tests
```

### Type Checking

```bash
mypy hyphen
```

### Releasing

Releases are published to [PyPI](https://pypi.org/project/hyphen/) automatically when a GitHub Release is created.

To release a new version:

1. Update the version in `pyproject.toml` and `hyphen/__init__.py`
2. Commit the version change: `git commit -am "chore: bump version to X.Y.Z"`
3. Push to main: `git push origin main`
4. Create a new [GitHub Release](https://github.com/Hyphen/python-sdk/releases/new):
   - Tag: `vX.Y.Z` (e.g., `v0.1.0`)
   - Title: `vX.Y.Z`
   - Description: Release notes
5. The release workflow will automatically run tests and publish to PyPI

**Note:** Publishing uses PyPI's trusted publisher (OIDC) - no API token needed.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and commit them with clear messages:
   - `feat: describe the feature`
   - `fix: describe the bug fix`
   - `chore: describe maintenance task`
4. Run tests and linting to ensure quality
5. Push your changes to your forked repository
6. Create a pull request to the main repository

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

Copyright © 2025 Hyphen, Inc. All rights reserved.
