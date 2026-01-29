# QBDQuery

A Python package for querying QuickBooks Desktop data.

https://pypi.org/project/qbdquery/0.1.1/

## Features

- Query any QuickBooks Desktop list or transaction type
- Select specific fields to return
- Filter and search capabilities
- Automatic connection management
- Merge duplicate records (customers, vendors, accounts, items, and more)


## Installation

```bash
pip install qbdquery
```

## Requirements

- Windows 10+ 
- QuickBooks Desktop (must be running upon inital connection to a company file)
- Python 3.7+

## Quick Start

### Basic Customer Query

```python
from qbdquery import QuickBooksClient

# Create client (uses currently open QuickBooks file by default)
client = QuickBooksClient()

# Query customers with automatic session management
with client.session():
    customers = client.query_customers()
    for customer in customers:
        print(f"{customer['FullName']}: {customer['Email']}")
```

### Specify a Company File

```python
# Connect to a specific company file
client = QuickBooksClient(
    company_file=r"C:\Path\To\Your\Company.QBW"
)

with client.session():
    customers = client.query_customers()
```

### Query with Field Selection

```python
with client.session():
    # Only get specific fields
    customers = client.query_customers(
        fields=["ListID", "FullName", "Email", "Phone", "Balance"]
    )
```

### Search Customers

```python
with client.session():
    # Search by name
    results = client.query_customers(name="smith")

    # Search with field selection
    results = client.query_customers(
        name="acme",
        fields=["FullName", "Email"],
        include_inactive=False
    )

    # Search by email
    results = client.query_customers(
        search={"Email": "gmail.com"}
    )

    # Combine name and field search
    results = client.query_customers(
        name="acme",
        search={"Email": "example.com"},
        fields=["FullName", "Email", "Phone"]
    )
```

### Generic Query Method

Query any QuickBooks entity type:

```python
with client.session():
    # Query invoices by reference number
    invoices = client.query(
        entity_type="Invoice",
        name="INV-2024",  # Searches RefNumber field
        fields=["TxnID", "RefNumber", "TxnDate", "BalanceRemaining"],
        filters={"PaidStatus": "NotPaidOnly"}
    )

    # Query items by name
    items = client.query(
        entity_type="Item",
        name="widget",
        fields=["FullName", "Type", "Price"],
        include_inactive=False
    )
```

### Convenience Methods

```python
with client.session():
    # Query vendors by name
    vendors = client.query_vendors(
        name="supply",
        fields=["Name", "Email", "Balance"],
        include_inactive=False
    )

    # Query items with multiple criteria
    items = client.query_items(
        name="widget",
        search={"Type": "Service"},
        fields=["FullName", "Type", "Description", "Price"]
    )
```

### Custom Filters

```python
with client.session():
    # Advanced filtering
    invoices = client.query(
        entity_type="Invoice",
        filters={
            "TxnDateRangeFilter": {
                "FromTxnDate": "2024-01-01",
                "ToTxnDate": "2024-12-31"
            },
            "PaidStatus": "NotPaidOnly",
            "MaxReturned": 500
        }
    )
```

## Merging Records

QBDQuery supports merging duplicate records in QuickBooks. When records are merged, all references to the source records (invoices, transactions, etc.) are automatically updated to point to the destination record, and the source records are deleted.

### Basic Merge

```python
with client.session():
    # Merge multiple customers into one
    # The first ID is the destination (kept), the rest are sources (deleted)
    results = client.merge_customers(
        destination="80000001-1234567890",  # ListID to keep
        sources=["80000002-1234567890", "80000003-1234567890"]  # ListIDs to delete
    )

    for result in results:
        if result["success"]:
            print(f"Merged {result['source_list_id']} into {result['merged_to_list_id']}")
        else:
            print(f"Failed: {result['status_message']}")
```

### Merge Vendors

```python
with client.session():
    # Merge duplicate vendors
    results = client.merge_vendors(
        destination="80000010-1234567890",
        sources=["80000011-1234567890"]
    )
```

### Merge Accounts

```python
with client.session():
    # Merge duplicate accounts
    results = client.merge_accounts(
        destination="80000020-1234567890",
        sources=["80000021-1234567890", "80000022-1234567890"]
    )
```

### Generic Merge

```python
with client.session():
    # Merge any supported entity type
    results = client.merge(
        destination="80000001-1234567890",
        sources=["80000002-1234567890"],
        entity_type="Customer"  # Optional: Customer, Vendor, Account, OtherName, Item, Class
    )
```

### Finding Duplicates to Merge

```python
with client.session():
    # Find potential duplicate customers by name
    customers = client.query_customers(
        name="Smith",
        fields=["ListID", "FullName", "Email", "Balance"]
    )

    # Review duplicates and merge
    if len(customers) > 1:
        destination = customers[0]["ListID"]  # Keep the first one
        sources = [c["ListID"] for c in customers[1:]]  # Merge the rest

        results = client.merge_customers(destination, sources)
```

> **Warning**: Merging is permanent and cannot be undone. Source records are deleted after merge. Always backup your QuickBooks company file before performing merge operations.

## Supported Entity Types

- **Lists**: Customer, Vendor, Employee, Item, Account
- **Transactions**: Invoice, Bill, Check, CreditMemo, Estimate, PurchaseOrder, SalesOrder, SalesReceipt
- **Merge-supported**: Customer, Vendor, Account, OtherName, Item, Class
- And more via the generic `query()` method

## API Reference

### QuickBooksClient

#### `__init__(company_file=None, app_name="QBDQuery Python Client", qbxml_version="13.0")`

Initialize the QuickBooks client.

- `company_file`: Path to company file. If `None`, uses currently open file.
- `app_name`: Application name shown in QuickBooks.
- `qbxml_version`: QBXML version to use (default: "13.0").

#### `session()`

Context manager for QuickBooks session. Always use this when querying.

#### `query(entity_type, name=None, search=None, fields=None, filters=None, max_results=None, include_inactive=True)`

Generic query method for any QuickBooks entity.

- `entity_type`: Type of entity (e.g., "Customer", "Invoice")
- `name`: Filter by name or reference number (FullName/Name/RefNumber)
- `search`: Dict of field:value pairs to search (e.g., `{"Email": "example"}`)
- `fields`: List of field names to return
- `filters`: Dictionary of filter criteria
- `max_results`: Maximum number of results
- `include_inactive`: Whether to include inactive records

#### Convenience Methods

- `query_customers(name=None, search=None, fields=None, include_inactive=True, max_results=None)`
- `query_vendors(name=None, search=None, fields=None, include_inactive=True, max_results=None)`
- `query_employees(name=None, search=None, fields=None, include_inactive=True, max_results=None)`
- `query_items(name=None, search=None, fields=None, include_inactive=True, max_results=None)`
- `query_accounts(name=None, search=None, fields=None, include_inactive=True, max_results=None)`
- `query_invoices(name=None, search=None, fields=None, filters=None, max_results=None)`

#### Merge Methods

##### `merge(destination, sources, entity_type=None)`

Generic merge method for any supported QuickBooks entity.

- `destination`: ListID of the record to keep (merge INTO)
- `sources`: List of ListIDs to merge FROM (will be deleted)
- `entity_type`: Entity type (e.g., "Customer", "Vendor", "Account"). If `None`, attempts across all supported types.
- **Returns**: List of dicts with keys: `success`, `merged_to_list_id`, `status_code`, `status_message`, `source_list_id`, `entity_type`

##### `merge_customers(destination, sources)`

Merge multiple customers into a single destination customer. Updates all invoices, payments, and estimates to reference the destination.

- `destination`: ListID of the customer to keep
- `sources`: List of customer ListIDs to merge and delete

##### `merge_vendors(destination, sources)`

Merge multiple vendors into a single destination vendor. Updates all bills and purchase orders to reference the destination.

- `destination`: ListID of the vendor to keep
- `sources`: List of vendor ListIDs to merge and delete

##### `merge_accounts(destination, sources)`

Merge multiple accounts into a single destination account. Updates all transactions to reference the destination.

- `destination`: ListID of the account to keep
- `sources`: List of account ListIDs to merge and delete


### Example: Export Customer List to CSV

```python
import csv
from qbdquery import QuickBooksClient

client = QuickBooksClient()

with client.session():
    customers = client.query_customers(
        fields=["FullName", "Email", "Phone", "Balance"],
        include_inactive=False
    )

    with open('customers.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["FullName", "Email", "Phone", "Balance"])
        writer.writeheader()
        writer.writerows(customers)
```

### Example: Find Overdue Invoices

```python
from qbdquery import QuickBooksClient
from datetime import date

client = QuickBooksClient()

with client.session():
    invoices = client.query_invoices(
        fields=["RefNumber", "CustomerRef", "TxnDate", "DueDate", "BalanceRemaining"],
        filters={"PaidStatus": "NotPaidOnly"}
    )

    today = date.today()
    for invoice in invoices:
        # Check if overdue (you'll need to parse the date)
        print(f"Invoice {invoice['RefNumber']}: ${invoice['BalanceRemaining']}")
```

## Error Handling

```python
from qbdquery import QuickBooksClient, QBDConnectionError, QBDSessionError

client = QuickBooksClient()

try:
    with client.session():
        customers = client.query_customers()
except QBDConnectionError as e:
    print(f"Failed to connect to QuickBooks: {e}")
except QBDSessionError as e:
    print(f"Session error: {e}")
```

## License

MIT License