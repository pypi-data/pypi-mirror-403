# OpenDBS Python Client

Official Python client library for OpenDBS.

## Installation

```bash
pip install opendbs
```

## Usage

### Initialization

```python
from opendbs import OpenDBS

# Initialize
client = OpenDBS("http://localhost:4402")

# Login
client.login("admin", "admin123")
```

### Basic Operations

```python
# Create Database
client.create_database("shop")

# Create Racks
client.create_rack("shop", "products", type="sql", schema={
    "name": {"type": "string"},
    "price": {"type": "number"}
})
client.create_rack("shop", "users", type="nosql")

# Insert Data
client.insert("shop", "users", {"name": "Alice"})
client.sql("shop", "INSERT INTO products (name, price) VALUES ('Laptop', 999)")

# Find Data
users = client.find("shop", "users", {"name": "Alice"})
```

### Advanced Search

```python
# Fuzzy Search
results = client.fuzzy_search("shop", "users", "field", "Alice")

# Vector Search
results = client.vector_search("shop", "products", "embedding", [0.1, 0.2, 0.3])
```
