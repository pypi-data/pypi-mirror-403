# Unepay Python SDK

Python SDK for working with Unepay API. Easy way to create payments, check their status and manage them through Python.

## Installation

```bash
pip install unepay-sdk
```

Or from source:

```bash
pip install .
```

## Quick Start

### Simple payment creation example

```python
from unepay_lib import UnepayClient

# Initialize client
client = UnepayClient(
    api_key="unepay_your_api_key_here"
)

# Create payment
payment = client.create_payment(
    payment_id="order_12345",      # Your internal order ID
    amount=1500.0,                  # Amount in rubles
    expires_in=600,                 # Lifetime in seconds (10 minutes)
    comment="Payment for order #12345"  # Comment (optional)
)

print(f"Payment URL: {payment.payment_url}")
print(f"Payment ID: {payment.id}")
print(f"External ID: {payment.external_id}")  # Your order ID

# Check payment status
status = client.get_payment_status(payment.id)
print(f"Status: {status.status}")
print(f"Is expired: {status.is_expired}")

# Get list of active payments
active_payments = client.list_active_payments()
for p in active_payments:
    print(f"{p.external_id}: {p.amount} RUB - {p.status}")
```

### Full example with error handling

```python
from unepay_lib import UnepayClient, UnepayAuthError, UnepayAPIError

client = UnepayClient(
    api_key="your_api_key"
)

try:
    # Create payment
    payment = client.create_payment(
        payment_id="order_12345",
        amount=1500.0,
        expires_in=600,
        comment="Payment for order"
    )
    
    print(f"✓ Payment created!")
    print(f"  URL: {payment.payment_url}")
    print(f"  ID: {payment.id}")
    
    # Track status
    import time
    while True:
        status = client.get_payment_status(payment.id)
        if status.status == "paid":
            print("✓ Payment completed!")
            break
        elif status.is_expired:
            print("⚠ Payment expired")
            break
        print(f"Status: {status.status}, waiting...")
        time.sleep(5)
        
except UnepayAuthError as e:
    print(f"Authentication error: {e}")
except UnepayAPIError as e:
    print(f"API error: {e}")
```

## API Documentation

### Client initialization

```python
client = UnepayClient(
    api_key: str,
    timeout: int = 30
)
```

**Parameters:**
- `api_key` (required) - Your merchant API key
- `timeout` (optional) - Request timeout in seconds

### Create payment

```python
payment = client.create_payment(
    payment_id: str,
    amount: float,
    expires_in: int,
    comment: Optional[str] = None
) -> Payment
```

**Parameters:**
- `payment_id` - Unique payment ID (your internal identifier)
- `amount` - Payment amount in rubles
- `expires_in` - Payment lifetime in seconds
- `comment` - Payment comment (optional)

**Returns:** `Payment` object with created payment data

**Example:**
```python
payment = client.create_payment(
    payment_id="order_123",
    amount=2500.50,
    expires_in=1800,  # 30 minutes
    comment="Payment for product"
)
```

### Get payment status

```python
payment = client.get_payment_status(payment_id: str) -> Payment
```

**Parameters:**
- `payment_id` - Payment ID (public_id, returned when created)

**Returns:** `Payment` object with current status

**Example:**
```python
payment = client.get_payment_status("n5AvkX5BhasxnL00EnhIVA9kZeXKquTb")
print(f"Status: {payment.status}")
print(f"Amount: {payment.amount} RUB")
print(f"Is expired: {payment.is_expired}")
```

### Get full payment information

```python
payment = client.get_payment(payment_id: str) -> Payment
```

**Parameters:**
- `payment_id` - Payment ID (public_id)

**Returns:** `Payment` object with full information

### List active payments

```python
payments = client.list_active_payments() -> List[Payment]
```

**Returns:** List of `Payment` objects with all active payments for the merchant

**Example:**
```python
payments = client.list_active_payments()
for payment in payments:
    print(f"ID: {payment.external_id}")
    print(f"Amount: {payment.amount} RUB")
    print(f"Status: {payment.status}")
    print(f"URL: {payment.payment_url}")
    print("---")
```

## Payment Model

The `Payment` object contains the following information:

```python
@dataclass
class Payment:
    id: str                    # Public ID (used in URL)
    external_id: str           # Your internal ID
    amount: float              # Payment amount
    comment: str               # Comment
    status: str                # Status: pending, paid, expired, cancelled
    expires_at: int            # Expiration timestamp (milliseconds)
    created_at: int            # Creation timestamp (milliseconds)
    paid_at: int               # Payment timestamp (milliseconds)
    payment_url: str           # Payment page URL
    is_expired: bool           # Expiration flag
```

**Useful properties:**
- `expires_at_datetime` - `expires_at` as `datetime` object
- `created_at_datetime` - `created_at` as `datetime` object
- `paid_at_datetime` - `paid_at` as `datetime` object

**Example:**
```python
payment = client.get_payment_status(payment_id)
if payment.expires_at_datetime:
    print(f"Expires at: {payment.expires_at_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
```

## Error Handling

The library uses the following exceptions:

- `UnepayException` - Base exception
- `UnepayAPIError` - General API error
- `UnepayAuthError` - Authentication error (invalid API key)
- `UnepayNotFoundError` - Resource not found (404)
- `UnepayValidationError` - Data validation error (400)

**Error handling example:**
```python
from unepay_lib import UnepayClient, UnepayAuthError, UnepayAPIError

try:
    client = UnepayClient(api_key="invalid_key")
    payment = client.create_payment(...)
except UnepayAuthError as e:
    print(f"Authentication error: {e}")
except UnepayAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
```

## Usage Examples

### Create and track payment

```python
from unepay_lib import UnepayClient
import time

client = UnepayClient(api_key="your_api_key")

# Create payment
payment = client.create_payment(
    payment_id="order_123",
    amount=1000.0,
    expires_in=600,
    comment="Payment for order"
)

print(f"Payment created: {payment.payment_url}")

# Track status
while True:
    status = client.get_payment_status(payment.id)
    
    if status.status == "paid":
        print("Payment completed!")
        break
    elif status.status == "expired" or status.is_expired:
        print("Payment expired")
        break
    
    print(f"Status: {status.status}, waiting...")
    time.sleep(5)  # Check every 5 seconds
```

### Get payment statistics

```python
from unepay_lib import UnepayClient
from collections import Counter

client = UnepayClient(api_key="your_api_key")
payments = client.list_active_payments()

# Statistics by status
statuses = Counter(p.status for p in payments)
print("Payment statuses:", dict(statuses))

# Total amount of active payments
total_amount = sum(p.amount for p in payments if p.status == "pending")
print(f"Total pending amount: {total_amount} RUB")

# Number of paid payments
paid_count = sum(1 for p in payments if p.status == "paid")
print(f"Paid payments: {paid_count}")
```

## License

MIT

## Support

If you have questions or issues, create an issue in the project repository.
