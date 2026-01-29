# Billingrails Python SDK

Official Python SDK for [Billingrails](https://billingrails.com) - Flexible, composable, and intuitive API-first commerce platform.

## Installation

```bash
pip install billingrails
```

## Quick Start

```python
from billingrails import Billingrails

# Initialize the client
client = Billingrails(
    api_key="your-api-key",
    base_url="https://api.billingrails.com"
)

# List accounts
list_response = client.accounts.list()
print(list_response["accounts"])

# Create an account
create_response = client.accounts.create({
    "name": "John Doe",
    "email": "john@example.com",
    "country": "US",
    "default_currency": "USD"
})
print(create_response["account"])

# Retrieve an account
retrieve_response = client.accounts.retrieve("acc_123")
print(retrieve_response["account"])

# Update an account
update_response = client.accounts.update("acc_123", {
    "name": "Jane Doe"
})
print(update_response["account"])

# Get account balances
balances_response = client.accounts.get_balances("acc_123")
print(balances_response["balances"])

# Debit an account
debit_response = client.accounts.debit("acc_123", {
    "amount": 1000,  # Amount in cents
    "currency": "USD"
})
print(debit_response["balances"])
```

## Configuration

### Basic Configuration

```python
client = Billingrails(api_key="your-api-key")
```

### Advanced Configuration

```python
client = Billingrails(
    api_key="your-api-key",
    base_url="https://api.billingrails.com",
    timeout=30,  # Request timeout in seconds
    max_retries=3  # Maximum number of retries for failed requests
)
```

## Error Handling

```python
from billingrails import Billingrails
import requests

client = Billingrails(api_key="your-api-key")

try:
    retrieve_response = client.accounts.retrieve("acc_123")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
except requests.exceptions.RequestException as e:
    print(f"Error occurred: {e}")
```

## Development

```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black billingrails/
isort billingrails/

# Type checking
mypy billingrails/
```

## License

MIT

## Support

For support, please contact [ugo@billingrails.com](mailto:ugo@billingrails.com) or visit our [documentation](https://docs.billingrails.com).

## Todo

- Improve error handling
