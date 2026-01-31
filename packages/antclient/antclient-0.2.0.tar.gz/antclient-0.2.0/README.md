# AntClient

[![PyPI version](https://badge.fury.io/py/antclient.svg)](https://badge.fury.io/py/antclient)
[![Python](https://img.shields.io/pypi/pyversions/antclient.svg)](https://pypi.org/project/antclient/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python client library for Anthive REST API - Simple, secure, and fast querying of single-cell expression databases.

## Features

- **Simple API**: Intuitive methods for common operations
- **Primary Data Retrieval**: `get_cell_data()` for flexible gene and metadata queries
- **SQL Templates**: Pre-built queries for complex aggregations
- **Secure**: Bearer token authentication support
- **Fast**: Built on requests with connection pooling
- **Type-safe**: Full type hints for IDE support
- **URL Encoding**: Automatic handling of database names with special characters

## Installation

```bash
# From PyPI
pip install antclient

# From source
pip install .

# Development mode
pip install -e .
```

## Quick Start

```python
from antclient import AntClient

# Connect to Anthive server
client = AntClient("http://localhost:8000", token="your-secret-token")

# List available databases
databases = client.get_databases()
print(f"Found {len(databases)} databases")

# Select first database
db = databases[0]['id']

# Get database info
info = client.get_database_info(db)
print(f"Database: {info['n_cells']} cells, {info['n_genes']} genes")

# Get cell data with genes and metadata
df = client.get_cell_data(
    db,
    genes=["CD3D", "CD4", "CD8A"],
    obs=["cell_type", "donor"]
)
print(df.head())
```

## Primary Data Retrieval

The `get_cell_data()` method is the primary way to retrieve expression data and metadata:

```python
# Get specific genes with metadata
df = client.get_cell_data(
    db,
    genes=["CD3D", "CD4", "CD8A"],
    obs=["cell_type", "n_counts", "donor"],
    limit=1000
)

# Get only metadata (no genes)
df = client.get_cell_data(
    db,
    obs=["cell_type", "tissue"]
)

# Get only gene expression (no metadata)
df = client.get_cell_data(
    db,
    genes=["CD3D", "CD4"],
    obs=[]  # Empty list = no metadata
)
```

Returns a DataFrame with cells as rows and genes + metadata as columns.

## SQL Templates

SQL templates provide server-side aggregations for complex queries:

```python
import antclient.sql as sql

# Top expressed genes (aggregates ALL genes)
df = sql.top_genes_by_expression(client, db, "X", limit=20)

# Gene expression grouped by metadata
df = sql.gene_expression_by_metadata(
    client, db, "X", "CD4", "cell_type", limit=20
)

# Top genes in specific cell type
df = sql.genes_in_cell_type(
    client, db, "X", "cell_type", "T cell", limit=10
)

# Count cells by metadata category
df = sql.cells_by_metadata(client, db, "cell_type", limit=10)

# Numerical metadata statistics
df = sql.metadata_distribution(client, db, "n_counts")

# Correlation between numerical fields
df = sql.correlation_two_numeric(
    client, db, "n_genes", "n_counts", "cell_type"
)
```

## Gene Search

```python
# Search for genes (case-insensitive by default)
genes = client.search_genes(db, query="CD", limit=10)

# Case-sensitive search
genes = client.search_genes(db, query="CD", case_sensitive=True, limit=10)
```

## Custom SQL Queries

Execute custom SQL queries:

```python
# Custom SQL
df = client.execute_sql(
    db,
    query="""
        SELECT
            o.cell_id,
            c.count as expression,
            o.cell_type
        FROM layer_X c
        JOIN obs o ON c.cell_id = o.cell_id
        WHERE c.gene_id = 'CD4'
        ORDER BY c.count DESC
    """,
    limit=50
)
```

## Metadata Exploration

```python
# Get metadata fields
fields = client.get_metadata_fields(db)
print("Numerical fields:", fields['numerical'])
print("Categorical fields:", fields['categorical'])

# Search categorical metadata
cell_types = client.search_categorical_metadata(
    db=db,
    field='cell_type',
    query='T',
    limit=20
)

# Get numerical metadata statistics
stats = client.get_numerical_metadata_stats(
    db=db,
    field='n_counts'
)
print(f"Count range: {stats['min']} - {stats['max']}")
```

## Authentication

```python
# With authentication
client = AntClient(
    "https://anthive.example.com",
    token="your-secret-token"
)

# Without authentication (if server doesn't require it)
client = AntClient("http://localhost:8000")
```

## Remote Server Connection

```python
# Connect to remote server
client = AntClient(
    "https://anthive.example.com:8000",
    token="your-token",
    verify_ssl=True  # Set to False to disable SSL verification (not recommended)
)

# All operations work the same
databases = client.get_databases()
```

## Database Names with Special Characters

Database names containing forward slashes or other special characters are automatically URL-encoded:

```python
# This works automatically (v0.2.0+)
db = "Project/Experiment/Dataset"
info = client.get_database_info(db)  # Forward slash encoded as %2F
```

## Error Handling

```python
from requests.exceptions import HTTPError

try:
    df = client.get_cell_data(db, genes=["CD4"])
except HTTPError as e:
    if "404" in str(e):
        print("Database or gene not found")
    elif "500" in str(e):
        print("Server error")
    else:
        print(f"API error: {e}")
```

## API Reference

### Core Methods

- `get_databases()` - List all databases
- `get_database_info(db)` - Get database metadata
- `get_layers(db)` - Get available data layers
- `search_genes(db, query, ...)` - Search for genes
- `get_metadata_fields(db)` - Get metadata field names
- `get_cell_data(db, genes, obs, ...)` - **Primary data retrieval method**
- `search_categorical_metadata(db, field, query, ...)` - Search metadata values
- `get_numerical_metadata_stats(db, field, ...)` - Get metadata statistics
- `execute_sql(db, query, limit)` - Execute custom SQL
- `execute_template(db, template_id, parameters, limit)` - Execute template
- `get_gene(db, gene_id)` - Get gene information
- `list_templates()` - List available templates

### SQL Template Functions

Available in `antclient.sql` module:

- `top_genes_by_expression(client, db, layer, limit)` - Most expressed genes
- `gene_expression_by_metadata(client, db, layer, gene, field, limit)` - Group by metadata
- `genes_in_cell_type(client, db, layer, field, value, limit)` - Top genes in type
- `cells_by_metadata(client, db, field, limit)` - Count by category
- `metadata_distribution(client, db, field, limit)` - Numerical statistics
- `correlation_two_numeric(client, db, field1, field2, cat_field, limit)` - Correlation

## Development

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black antclient/

# Lint
flake8 antclient/
```

## Requirements

- Python >= 3.8
- requests >= 2.25.0
- pandas >= 1.3.0

## Changelog

See [CHANGELOG.md](https://github.com/yourusername/anthive/blob/main/antclient/CHANGELOG.md) for version history.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.

## Links

- **Documentation**: [Full documentation](https://github.com/yourusername/anthive)
- **GitHub**: [Source code](https://github.com/yourusername/anthive)
- **PyPI**: [Package](https://pypi.org/project/antclient/)
- **Issues**: [Bug reports](https://github.com/yourusername/anthive/issues)

## Examples

Check out the [demo notebooks](https://github.com/yourusername/anthive/tree/main/) for complete examples:
- `demo_antclient.ipynb` - Complete API walkthrough
- `demo_gene_distribution.ipynb` - Gene expression distribution visualization
