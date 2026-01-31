"""
SQL template functions for Anthive client.

These functions provide typed, autocomplete-friendly access to SQL query templates.
Each function corresponds to a query template in the Anthive REST API.

All parameters can be either regular values (strings, ints) or widgets - the functions
automatically extract the value from widgets.
"""

from typing import Optional
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


def _format_layer(layer: str) -> str:
    """
    Format layer name for SQL query.

    Args:
        layer: Layer name (e.g., 'X' or 'layer_X')

    Returns:
        Formatted table name (e.g., 'layer_X')
    """
    if not layer.startswith('layer_'):
        return f'layer_{layer}'
    return layer


def top_genes_by_expression(
    client,
    db: str,
    layer: str,
    limit: Optional[int] = 100
) -> pd.DataFrame:
    """
    Find genes with highest expression in a specific layer.

    Args:
        client: AntClient instance
        db: Database ID or widget
        layer: Data layer name or widget (e.g., 'X' or 'layer_X')
        limit: Maximum rows to return or widget (None for no limit)

    Returns:
        DataFrame with columns: gene_id, total_expression
    """
    db = _extract_value(db)
    layer = _extract_value(layer)
    if limit is not None:
        limit = _extract_value(limit)

    return client.execute_template(
        db=db,
        template_id='top_genes_by_expression',
        parameters={'layer': _format_layer(layer)},
        limit=limit
    )


def gene_expression_by_metadata(
    client,
    db: str,
    layer: str,
    gene_1: str,
    obscat_1_col: str,
    limit: Optional[int] = 100
) -> pd.DataFrame:
    """
    Compare expression of a gene across different cell types or metadata categories.

    Args:
        client: AntClient instance
        db: Database ID or widget
        layer: Data layer name or widget (e.g., 'X' or 'layer_X')
        gene_1: Gene ID or widget
        obscat_1_col: Categorical metadata field or widget
        limit: Maximum rows to return or widget (None for no limit)

    Returns:
        DataFrame with columns: category, avg_expression, total_expression, cell_count
    """
    db = _extract_value(db)
    layer = _extract_value(layer)
    gene_1 = _extract_value(gene_1)
    obscat_1_col = _extract_value(obscat_1_col)
    if limit is not None:
        limit = _extract_value(limit)

    return client.execute_template(
        db=db,
        template_id='gene_expression_by_metadata',
        parameters={
            'layer': _format_layer(layer),
            'gene_1': gene_1,
            'obscat_1_col': obscat_1_col
        },
        limit=limit
    )


def cells_by_metadata(
    client,
    db: str,
    obscat_1_col: str,
    limit: Optional[int] = 100
) -> pd.DataFrame:
    """
    Count cells grouped by a categorical metadata field.

    This function groups cells by the specified categorical field and returns
    counts for each category. It does NOT filter cells by a specific value.

    Args:
        client: AntClient instance
        db: Database ID or widget
        obscat_1_col: Categorical metadata field to group by (e.g., 'cell_type')
        limit: Maximum rows to return or widget (None for no limit)

    Returns:
        DataFrame with columns: category (metadata values), cell_count (counts)

    Example:
        >>> df = cells_by_metadata(client, "mydb", "cell_type", limit=10)
        >>> # Returns counts: T cell: 1000, B cell: 500, etc.

    Note:
        To filter cells by a specific value, use client.execute_sql() instead:
        >>> df = client.execute_sql(db, "SELECT * FROM obs WHERE cell_type = 'T cell'")
    """
    db = _extract_value(db)
    obscat_1_col = _extract_value(obscat_1_col)
    if limit is not None:
        limit = _extract_value(limit)

    return client.execute_template(
        db=db,
        template_id='cells_by_metadata',
        parameters={'obscat_1_col': obscat_1_col},
        limit=limit
    )


def genes_in_cell_type(
    client,
    db: str,
    layer: str,
    obscat_1_col: str,
    obscat_1_opt: str,
    limit: Optional[int] = 20
) -> pd.DataFrame:
    """
    Find top expressed genes in cells of a specific type.

    Args:
        client: AntClient instance
        db: Database ID or widget
        layer: Data layer name or widget (e.g., 'X' or 'layer_X')
        obscat_1_col: Categorical metadata field or widget (e.g., 'cell_type')
        obscat_1_opt: Specific value or widget to filter by (e.g., 'T cell')
        limit: Maximum rows to return or widget (default: 20)

    Returns:
        DataFrame with columns: gene_id, total_expression, expressing_cells
    """
    db = _extract_value(db)
    layer = _extract_value(layer)
    obscat_1_col = _extract_value(obscat_1_col)
    obscat_1_opt = _extract_value(obscat_1_opt)
    if limit is not None:
        limit = _extract_value(limit)

    return client.execute_template(
        db=db,
        template_id='genes_in_cell_type',
        parameters={
            'layer': _format_layer(layer),
            'obscat_1_col': obscat_1_col,
            'obscat_1_opt': obscat_1_opt
        },
        limit=limit
    )


def metadata_distribution(
    client,
    db: str,
    obsnum_1_col: str,
    limit: Optional[int] = 100
) -> pd.DataFrame:
    """
    Get statistics for a numerical metadata field.

    Args:
        client: AntClient instance
        db: Database ID or widget
        obsnum_1_col: Numerical metadata field or widget
        limit: Maximum rows to return or widget (None for no limit)

    Returns:
        DataFrame with columns: min_value, max_value, avg_value, median_value
    """
    db = _extract_value(db)
    obsnum_1_col = _extract_value(obsnum_1_col)
    if limit is not None:
        limit = _extract_value(limit)

    return client.execute_template(
        db=db,
        template_id='metadata_distribution',
        parameters={'obsnum_1_col': obsnum_1_col},
        limit=limit
    )


def correlation_two_numeric(
    client,
    db: str,
    obsnum_1_col: str,
    obsnum_2_col: str,
    obscat_1_col: str,
    limit: Optional[int] = 100
) -> pd.DataFrame:
    """
    Compare two numerical metadata fields.

    Args:
        client: AntClient instance
        db: Database ID or widget
        obsnum_1_col: First numerical metadata field or widget
        obsnum_2_col: Second numerical metadata field or widget
        obscat_1_col: Categorical metadata field or widget
        limit: Maximum rows to return or widget (None for no limit)

    Returns:
        DataFrame with columns: {obsnum_1_col}, {obsnum_2_col}, {obscat_1_col}
    """
    db = _extract_value(db)
    obsnum_1_col = _extract_value(obsnum_1_col)
    obsnum_2_col = _extract_value(obsnum_2_col)
    obscat_1_col = _extract_value(obscat_1_col)
    if limit is not None:
        limit = _extract_value(limit)

    return client.execute_template(
        db=db,
        template_id='correlation_two_numeric',
        parameters={
            'obsnum_1_col': obsnum_1_col,
            'obsnum_2_col': obsnum_2_col,
            'obscat_1_col': obscat_1_col
        },
        limit=limit
    )
