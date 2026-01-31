"""
Ant Client - Python client for Anthive REST API.

Simple, secure, and fast client for querying single-cell expression databases.
"""

import requests
from typing import Optional, Dict, Any, List
from functools import lru_cache
from urllib.parse import quote
import pandas as pd


def _extract_value(value):
    """
    Extract actual value from widget objects.

    Handles WidgetValue objects from antclient.widgets.
    """
    # Check if it's a WidgetValue (from widgets module)
    if hasattr(value, 'widget') and hasattr(value, 'value'):
        return value.value
    # Check if it's a raw widget
    elif hasattr(value, 'value') and hasattr(value, 'observe'):
        return value.value
    # Regular value
    else:
        return value


def _encode_db_id(db_id: str) -> str:
    """
    URL-encode database ID for use in URL paths.

    Database IDs can contain forward slashes (e.g., "Project/Experiment"),
    which must be percent-encoded as %2F for URLs.

    Args:
        db_id: Database identifier (may contain /)

    Returns:
        URL-encoded database ID safe for use in paths
    """
    return quote(db_id, safe='')


class SQLTemplates:
    """Dynamic SQL template methods."""

    def __init__(self, client):
        self._client = client
        self._templates = None

    def _load_templates(self):
        """Load available templates from server."""
        if self._templates is None:
            response = self._client._get("/query-templates")
            self._templates = {t['id']: t for t in response['templates']}
        return self._templates

    def __getattr__(self, name):
        """Dynamically create methods for each template."""
        templates = self._load_templates()

        if name not in templates:
            raise AttributeError(f"Template '{name}' not found. Available: {list(templates.keys())}")

        template = templates[name]

        def template_method(db: str, limit: Optional[int] = 100, **parameters):
            """
            Execute SQL template query.

            Args:
                db: Database ID
                limit: Maximum rows to return (None for no limit)
                **parameters: Template parameters (e.g., layer, gene_1, obscat_1_col, etc.)

            Returns:
                pandas.DataFrame with query results
            """
            return self._client.execute_template(db, name, parameters, limit)

        # Copy docstring from template
        template_method.__doc__ = f"""
        {template['name']}

        {template['description']}

        Args:
            db: Database ID
            limit: Maximum rows to return (None for no limit)
            **parameters: Template parameters

        Returns:
            pandas.DataFrame with query results
        """
        template_method.__name__ = name

        return template_method

    def list(self) -> List[Dict[str, Any]]:
        """List all available SQL templates."""
        templates = self._load_templates()
        return [
            {
                'id': t['id'],
                'name': t['name'],
                'description': t['description'],
                'category': t['category']
            }
            for t in templates.values()
        ]


class AntClient:
    """
    Ant Client - Simple interface to Anthive REST API.

    Example:
        >>> client = AntClient("http://localhost:8000", token="secret")
        >>> dbs = client.get_databases()
        >>> df = client.sql.top_genes_by_expression(db=dbs[0]['id'], layer='layer_X', limit=10)
    """

    def __init__(self, base_url: str, token: Optional[str] = None, verify_ssl: bool = True):
        """
        Initialize Anthive client.

        Args:
            base_url: Base URL of Anthive REST API (e.g., 'http://localhost:8000')
            token: Bearer token for authentication (optional)
            verify_ssl: Verify SSL certificates (default: True)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()

        # Set authorization header
        if self.token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })

        # Initialize SQL templates namespace
        self.sql = SQLTemplates(self)

    def _get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, verify=self.verify_ssl, **kwargs)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, json_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=json_data, verify=self.verify_ssl, **kwargs)
        response.raise_for_status()
        return response.json()

    # ========== Core API Methods ==========

    def get_databases(self) -> List[Dict[str, Any]]:
        """
        List all available databases.

        Returns:
            List of database info dicts with keys: id, path, n_cells, n_genes, layers
        """
        result = self._get("/databases")
        return result['databases']

    def get_database_info(self, db: str) -> Dict[str, Any]:
        """
        Get detailed information about a database.

        Args:
            db: Database ID

        Returns:
            Dict with database metadata
        """
        db = _extract_value(db)
        return self._get(f"/databases/{_encode_db_id(db)}/info")

    def get_layers(self, db: str) -> List[str]:
        """
        Get available data layers for a database.

        Args:
            db: Database ID

        Returns:
            List of layer names
        """
        db = _extract_value(db)
        result = self._get(f"/databases/{_encode_db_id(db)}/layers")
        return result['layers']

    def search_genes(self, db: str, query: str, limit: Optional[int] = None,
                     case_sensitive: bool = False) -> List[str]:
        """
        Search for genes by substring.

        Args:
            db: Database ID
            query: Search substring
            limit: Maximum results (optional)
            case_sensitive: Case-sensitive search (default: False)

        Returns:
            List of matching gene IDs
        """
        db = _extract_value(db)
        query = _extract_value(query)
        if limit is not None:
            limit = _extract_value(limit)
        params = {'q': query, 'case_sensitive': case_sensitive}
        if limit:
            params['limit'] = limit
        result = self._get(f"/databases/{_encode_db_id(db)}/genes", params=params)
        return result['genes']

    def get_metadata_fields(self, db: str) -> Dict[str, List[str]]:
        """
        Get metadata field names and types.

        Args:
            db: Database ID

        Returns:
            Dict with keys: 'numerical', 'categorical', 'all'
        """
        db = _extract_value(db)
        return self._get(f"/databases/{_encode_db_id(db)}/metadata/fields")

    def search_categorical_metadata(self, db: str, field: str, query: str,
                                     limit: Optional[int] = None,
                                     case_sensitive: bool = False) -> List[str]:
        """
        Search categorical metadata values.

        Args:
            db: Database ID
            field: Metadata field name
            query: Search substring
            limit: Maximum results (optional)
            case_sensitive: Case-sensitive search (default: False)

        Returns:
            List of matching values
        """
        db = _extract_value(db)
        field = _extract_value(field)
        query = _extract_value(query)
        if limit is not None:
            limit = _extract_value(limit)
        params = {'field': field, 'q': query, 'case_sensitive': case_sensitive}
        if limit:
            params['limit'] = limit
        result = self._get(f"/databases/{_encode_db_id(db)}/metadata/categorical", params=params)
        return result['values']

    def get_numerical_metadata_stats(self, db: str, field: str,
                                      min_value: Optional[float] = None,
                                      max_value: Optional[float] = None) -> Dict[str, Any]:
        """
        Get statistics for numerical metadata field.

        Args:
            db: Database ID
            field: Metadata field name
            min_value: Minimum value filter (optional)
            max_value: Maximum value filter (optional)

        Returns:
            Dict with statistics (min, max, mean, median, etc.)
        """
        db = _extract_value(db)
        field = _extract_value(field)
        if min_value is not None:
            min_value = _extract_value(min_value)
        if max_value is not None:
            max_value = _extract_value(max_value)
        params = {'field': field}
        if min_value is not None:
            params['min'] = min_value
        if max_value is not None:
            params['max'] = max_value
        return self._get(f"/databases/{_encode_db_id(db)}/metadata/numerical", params=params)

    def execute_sql(self, db: str, query: str, limit: Optional[int] = 100) -> pd.DataFrame:
        """
        Execute custom SQL query.

        Args:
            db: Database ID
            query: SQL query string
            limit: Maximum rows to return (None for no limit)

        Returns:
            pandas.DataFrame with query results
        """
        db = _extract_value(db)
        query = _extract_value(query)
        if limit is not None:
            limit = _extract_value(limit)
        payload = {'query': query, 'limit': limit}
        result = self._post(f"/databases/{_encode_db_id(db)}/query/sql", payload)
        return pd.DataFrame(result['data'])

    def execute_template(self, db: str, template_id: str, parameters: Dict[str, str],
                         limit: Optional[int] = 100) -> pd.DataFrame:
        """
        Execute SQL template query.

        Args:
            db: Database ID
            template_id: Template ID
            parameters: Template parameters (e.g., {'layer': 'layer_X', 'gene_1': 'CD4'})
            limit: Maximum rows to return (None for no limit)

        Returns:
            pandas.DataFrame with query results
        """
        db = _extract_value(db)
        template_id = _extract_value(template_id)
        if limit is not None:
            limit = _extract_value(limit)
        # Extract values from parameters dict
        parameters = {k: _extract_value(v) for k, v in parameters.items()}
        payload = {'parameters': parameters, 'limit': limit}
        result = self._post(f"/databases/{_encode_db_id(db)}/query/template/{template_id}", payload)
        return pd.DataFrame(result['data'])

    def get_gene_info(self, db: str, gene_id: str) -> Dict[str, Any]:
        """
        Get information about a specific gene.

        Args:
            db: Database ID
            gene_id: Gene ID

        Returns:
            Dict with gene information
        """
        db = _extract_value(db)
        gene_id = _extract_value(gene_id)
        return self._get(f"/databases/{_encode_db_id(db)}/genes/{gene_id}")

    def get_cell_data(
        self,
        db: str,
        genes: Optional[List[str]] = None,
        obs: Optional[List[str]] = None,
        layer: str = "X",
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get cell data matrix with gene expression and observation metadata.

        This is the primary data retrieval method that returns a wide-format
        table with cells as rows and genes/metadata as columns.

        Args:
            db: Database ID or widget
            genes: List of gene IDs to include (None = no genes)
            obs: List of observation (metadata) column names to include (None = all)
            layer: Data layer to query (default: "X")
            limit: Maximum number of cells to return (None = no limit)

        Returns:
            DataFrame with cells as rows, genes and metadata as columns

        Example:
            >>> # Get specific genes with metadata
            >>> df = client.get_cell_data(
            ...     db="mydb",
            ...     genes=["CD3D", "CD4", "CD8A"],
            ...     obs=["cell_type", "donor", "n_genes"]
            ... )
            >>>
            >>> # Get only metadata (no expression)
            >>> df = client.get_cell_data(
            ...     db="mydb",
            ...     obs=["cell_type", "tissue"]
            ... )
            >>>
            >>> # Get only gene expression (no metadata)
            >>> df = client.get_cell_data(
            ...     db="mydb",
            ...     genes=["CD3D", "CD4"],
            ...     obs=[]  # Empty list = no metadata
            ... )
        """
        db = _extract_value(db)
        layer = _extract_value(layer)
        if limit is not None:
            limit = _extract_value(limit)

        # Extract values from lists
        if genes is not None:
            genes = [_extract_value(g) for g in genes]
        if obs is not None:
            obs = [_extract_value(o) for o in obs]

        # Build query parameters
        params = {"layer": layer}
        if genes:
            params["genes"] = ",".join(genes)
        if obs is not None:  # Explicitly check None (empty list means no metadata)
            params["metadata"] = ",".join(obs)
        if limit:
            params["limit"] = limit

        result = self._get(f"/databases/{_encode_db_id(db)}/cells", params=params)
        return pd.DataFrame(result['data'])

    # ========== Convenience Methods ==========

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available SQL templates.

        Returns:
            List of template info dicts
        """
        return self.sql.list()
