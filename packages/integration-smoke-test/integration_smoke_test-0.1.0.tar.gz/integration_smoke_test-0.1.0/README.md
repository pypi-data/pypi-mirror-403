# integration-smoke-test

A lightweight Python library for fast API integration smoke tests with structured failure classification.

## Usage

```python
from integration_smoke import check_integration

print(check_integration("https://www.google.com"))
