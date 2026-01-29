# SheetSandbox SDK for Python

A simple and easy-to-understand Python SDK for SheetSandbox - Turn Google Sheets into your production-ready database.

## 🎯 Features

- ✅ **Simple & Clean** - Easy to understand code without complex parts
- ✅ **Basic CRUD Operations** - Get, GetById, Post, and Token Verification
- ✅ **Pythonic API** - Follows Python conventions and best practices
- ✅ **Lightweight** - Minimal dependencies
- ✅ **Ready to Extend** - Clean architecture for future enhancements

## 📦 Installation

```bash
pip install sheetsandbox
```

## 🚀 Quick Start

```python
from sheetsandbox import SheetSandbox

# Initialize the client
client = SheetSandbox('your-api-token')

# Verify your token
result = client.verify_token()
print(result)

# Create a record
result = client.post('UserFeedback', {
    'Subject': 'John Doe',
    'Message': 'john@example.com',
    'type': 'active'
})

# Get all records
result = client.get('UserFeedback')

# Get a specific record
result = client.get_by_id('UserFeedback', 1)
```

## 📖 API Reference

### Constructor

```python
client = SheetSandbox(token, base_url=None, timeout=30)
```

**Parameters:**
- `token` (str, required) - Your SheetSandbox API token
- `base_url` (str, optional) - API base URL (default: 'http://localhost:3001/api')
- `timeout` (int, optional) - Request timeout in seconds (default: 30)

### Methods

#### `verify_token()`

Verify if your API token is valid.

```python
result = client.verify_token()

if result['success']:
    print("Token is valid!")
else:
    print(f"Error: {result['error']}")
```

**Returns:** `dict`
- `success` (bool) - Operation status
- `data` (dict) - Verification response data
- `status` (str) - 'success' or 'error'
- `error` (str) - Error message (if failed)

---

#### `get(table_name)`

Get all records from a table.

```python
result = client.get('UserFeedback')

if result['success']:
    for record in result['data']:
        print(record)
```

**Returns:** `dict`
- `success` (bool) - Operation status
- `data` (list) - Array of records
- `status` (str) - 'success' or 'error'
- `error` (str) - Error message (if failed)

---

#### `get_by_id(table_name, record_id)`

Get a specific record by ID.

```python
result = client.get_by_id('UserFeedback', 1)

if result['success']:
    print(result['data'])  # Single record
```

**Parameters:**
- `table_name` (str) - Name of the table
- `record_id` (int|str) - Record ID (1-based index)

**Returns:** `dict`
- `success` (bool) - Operation status
- `data` (dict) - Record data
- `status` (str) - 'success' or 'error'
- `error` (str) - Error message (if failed)

---

#### `post(table_name, data)`

Create a new record.

```python
result = client.post('UserFeedback', {
    'Subject': 'Feature Request',
    'Message': 'Add dark mode support',
    'type': 'feature'
})

if result['success']:
    print('Record created!')
```

**Parameters:**
- `table_name` (str) - Name of the table
- `data` (dict) - Record data to create

**Returns:** `dict`
- `success` (bool) - Operation status
- `data` (dict) - Created record data
- `status` (str) - 'success' or 'error'
- `error` (str) - Error message (if failed)

---

#### `set_token(new_token)`

Update the API token.

```python
client.set_token('new-api-token')
```

---

#### `set_base_url(new_base_url)`

Update the base URL.

```python
client.set_base_url('https://api.sheetsandbox.com')
```

---

#### `get_config()`

Get current configuration.

```python
config = client.get_config()
print(config)
# {'base_url': '...', 'timeout': 30, 'has_token': True}
```

## 💡 Examples

### Waitlist Signup

```python
from sheetsandbox import SheetSandbox
from datetime import datetime

client = SheetSandbox('your-api-token')

def add_to_waitlist(email, name):
    result = client.post('Waitlist', {
        'email': email,
        'name': name,
        'timestamp': datetime.now().isoformat()
    })
    
    if result['success']:
        print('✅ Added to waitlist!')
    else:
        print(f"❌ Error: {result['error']}")

add_to_waitlist('user@example.com', 'Jane Doe')
```

### Feedback Form

```python
def submit_feedback(feedback):
    result = client.post('Feedback', {
        'message': feedback['message'],
        'rating': feedback['rating'],
        'email': feedback['email'],
        'submitted_at': datetime.now().isoformat()
    })
    
    return result['success']

# Usage
feedback_data = {
    'message': 'Great product!',
    'rating': 5,
    'email': 'happy@customer.com'
}

if submit_feedback(feedback_data):
    print('Feedback submitted successfully!')
```

### Get User Feedback List

```python
def get_feedback_list():
    result = client.get('UserFeedback')
    
    if result['success']:
        for feedback in result['data']:
            print(f"{feedback['Subject']} - {feedback['Message']}")
    else:
        print(f"Error: {result['error']}")

get_feedback_list()
```

### Token Verification

```python
def check_token():
    result = client.verify_token()
    
    if result['success']:
        print('✅ Token is valid and working!')
        print(f"API Response: {result['data']}")
    else:
        print(f"❌ Token verification failed: {result['error']}")

check_token()
```

### Complete CRUD Example

```python
from sheetsandbox import SheetSandbox

client = SheetSandbox('your-api-token')

# Verify token first
if not client.verify_token()['success']:
    print("Invalid token!")
    exit()

# Create a new user
new_user = client.post('Users', {
    'name': 'Alice Johnson',
    'email': 'alice@example.com',
    'role': 'developer'
})

if new_user['success']:
    print(f"Created user: {new_user['data']}")

# Get all users
all_users = client.get('Users')
if all_users['success']:
    print(f"Total users: {len(all_users['data'])}")

# Get specific user
user = client.get_by_id('Users', 1)
if user['success']:
    print(f"First user: {user['data']}")
```

## 🔧 Error Handling

All methods return a consistent response format:

```python
result = client.get('Users')

if result['success']:
    # Operation succeeded
    print(result['data'])
else:
    # Operation failed
    print(result['error'])
```

### Exception Handling

```python
try:
    result = client.post('Users', {
        'name': 'Test User',
        'email': 'test@example.com'
    })
    
    if result['success']:
        print('Success!')
    else:
        print(f"API Error: {result['error']}")
        
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## 🛣️ Roadmap

This is a simplified version designed to be easy to understand and extend. Future enhancements may include:

- [ ] Async/await support with `asyncio`
- [ ] Batch operations (create multiple records at once)
- [ ] Advanced filtering and sorting
- [ ] Duplicate prevention
- [ ] Update and delete operations
- [ ] Pagination support
- [ ] Retry logic with exponential backoff
- [ ] Type hints and better IDE support
- [ ] Data validation

## 📝 License

MIT

## 🔗 Links

- [Website](https://sheetsandbox.com)
- [Documentation](https://sheetsandbox.com/docs)
- [GitHub](https://github.com/sheetsandbox/sheetsandbox-python)
- [PyPI Package](https://pypi.org/project/sheetsandbox/)

## 💬 Support

For issues and questions, please visit our [GitHub Issues](https://github.com/sheetsandbox/sheetsandbox-python/issues).

## 🐍 Python Version Support

- Python 3.7+
- Tested on Python 3.8, 3.9, 3.10, 3.11, and 3.12

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request