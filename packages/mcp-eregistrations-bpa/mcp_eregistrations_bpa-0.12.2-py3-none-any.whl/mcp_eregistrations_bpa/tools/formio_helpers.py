"""Form.io schema manipulation helpers.

This module provides utility functions for manipulating Form.io component trees.
It supports finding, inserting, removing, and updating components within the
nested structure (panels, columns, tabs, etc.).

All functions operate on copies to avoid mutating original data.

Container Type Hierarchy
------------------------
Form.io uses container components to organize form layouts. Each container type
stores its children in a specific property:

+-------------+---------------------------+----------------------------------------+
| Type        | Children Accessor         | Notes                                  |
+-------------+---------------------------+----------------------------------------+
| tabs        | components[]              | Tab panes have null type; each pane    |
|             |                           | contains its own components[]          |
+-------------+---------------------------+----------------------------------------+
| panel       | components[]              | Standard collapsible container         |
+-------------+---------------------------+----------------------------------------+
| columns     | columns[].components[]    | 2-level nesting: columns array with    |
|             |                           | each column having a components array  |
+-------------+---------------------------+----------------------------------------+
| fieldset    | components[]              | HTML fieldset grouping                 |
+-------------+---------------------------+----------------------------------------+
| editgrid    | components[]              | Repeatable rows with inline editing    |
+-------------+---------------------------+----------------------------------------+
| datagrid    | components[]              | Repeatable rows in table format        |
+-------------+---------------------------+----------------------------------------+
| table       | rows[][]                  | HTML table structure: rows array       |
|             |                           | containing arrays of cells             |
+-------------+---------------------------+----------------------------------------+
| well        | components[]              | Visual grouping container              |
+-------------+---------------------------+----------------------------------------+
| container   | components[]              | Data grouping without visual styling   |
+-------------+---------------------------+----------------------------------------+

Path Examples
-------------
When traversing nested components, paths represent the hierarchy from root to
the target component:

    # Example: component inside tabs > tab_pane > panel
    path = ["applicantWelcome", "applicantWelcomepersonalInformation", "applicantBlock"]
    # Meaning: tabs("applicantWelcome") > panel("applicantWelcomepersonalInformation")
    #          > panel("applicantBlock") > [target component]

    # Example: component inside columns
    path = ["myPanel", "twoColumnLayout"]
    # Meaning: panel("myPanel") > columns("twoColumnLayout") > [target component]

The path array is returned by find_component() and used in API responses
to help identify the nesting structure of each component.
"""

from __future__ import annotations

import copy
import re
from typing import Any

# Container component types that can hold nested components
CONTAINER_TYPES = {
    "panel",
    "columns",
    "tabs",
    "well",
    "fieldset",
    "container",
    "editgrid",
    "datagrid",
    "table",
}

# Container types with special child structures (not just "components" array)
# These require additional parameters (column_index, row_index, etc.) when inserting
COLUMN_BASED_CONTAINERS = {"columns"}
# TODO: Table support - tables use rows[i].components[] structure similar to columns
# Implementation deferred until table editing is needed
TABLE_BASED_CONTAINERS = {"table"}

# Maximum recursion depth for tree traversal (prevent stack overflow)
MAX_RECURSION_DEPTH = 100

# BPA-specific default properties for new components
BPA_COMPONENT_DEFAULTS = {
    "registrations": {},
    "determinantIds": [],
    "componentActionId": "",
    "componentFormulaId": "",
    "behaviourId": "",
    "componentValidationId": "",
    "version": "201905",
    "input": True,
    "tableView": True,
}


def find_component(
    components: list[dict[str, Any]],
    key: str,
    path: list[str] | None = None,
    _depth: int = 0,
) -> tuple[dict[str, Any], list[str]] | None:
    """Find a component by key in the component tree.

    Searches recursively through nested components (panels, columns, tabs).

    Args:
        components: List of Form.io components to search.
        key: The component key to find.
        path: Current path (used internally for recursion).
        _depth: Current recursion depth (internal use).

    Returns:
        Tuple of (component, path) if found, None otherwise.
        The path is a list of parent keys leading to the component.

    Raises:
        RecursionError: If nesting exceeds MAX_RECURSION_DEPTH.

    Example:
        >>> components = [{"key": "panel1", "type": "panel", "components": [
        ...     {"key": "name", "type": "textfield"}
        ... ]}]
        >>> result = find_component(components, "name")
        >>> result[0]["key"]
        'name'
        >>> result[1]
        ['panel1']
    """
    if _depth > MAX_RECURSION_DEPTH:
        raise RecursionError(
            f"Component tree exceeds maximum depth of {MAX_RECURSION_DEPTH}"
        )

    if path is None:
        path = []

    for comp in components:
        if not isinstance(comp, dict):
            continue

        comp_key = comp.get("key")
        if comp_key == key:
            return (comp, path)

        new_path = path + [comp_key] if comp_key else path

        # Search in nested components
        nested = comp.get("components", [])
        if nested:
            result = find_component(nested, key, new_path, _depth + 1)
            if result:
                return result

        # Search in columns
        columns = comp.get("columns", [])
        for col in columns:
            if isinstance(col, dict):
                col_components = col.get("components", [])
                if col_components:
                    result = find_component(col_components, key, new_path, _depth + 1)
                    if result:
                        return result

        # Search in tabs
        tabs = comp.get("tabs", [])
        for tab in tabs:
            if isinstance(tab, dict):
                tab_components = tab.get("components", [])
                if tab_components:
                    result = find_component(tab_components, key, new_path, _depth + 1)
                    if result:
                        return result

        # Search in table rows (rows[][] structure)
        rows = comp.get("rows", [])
        for row in rows:
            if isinstance(row, list):
                for cell in row:
                    if isinstance(cell, dict):
                        cell_components = cell.get("components", [])
                        if cell_components:
                            result = find_component(
                                cell_components, key, new_path, _depth + 1
                            )
                            if result:
                                return result

    return None


def find_component_parent(
    components: list[dict[str, Any]],
    key: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int]:
    """Find the parent container and index of a component.

    Args:
        components: List of Form.io components.
        key: The component key to find.

    Returns:
        Tuple of (parent_component, siblings_list, index).
        parent_component is None if the component is at root level.
        siblings_list is the list containing the component.
        index is the position of the component in siblings_list.

    Raises:
        ValueError: If component is not found.
        RecursionError: If nesting exceeds MAX_RECURSION_DEPTH.
    """

    def _search(
        comps: list[dict[str, Any]], parent: dict[str, Any] | None, depth: int = 0
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], int] | None:
        if depth > MAX_RECURSION_DEPTH:
            raise RecursionError(
                f"Component tree exceeds maximum depth of {MAX_RECURSION_DEPTH}"
            )

        for i, comp in enumerate(comps):
            if not isinstance(comp, dict):
                continue

            if comp.get("key") == key:
                return (parent, comps, i)

            # Search in nested components
            nested = comp.get("components", [])
            if nested:
                result = _search(nested, comp, depth + 1)
                if result:
                    return result

            # Search in columns
            columns = comp.get("columns", [])
            for col in columns:
                if isinstance(col, dict):
                    col_components = col.get("components", [])
                    if col_components:
                        result = _search(col_components, comp, depth + 1)
                        if result:
                            return result

            # Search in tabs
            tabs = comp.get("tabs", [])
            for tab in tabs:
                if isinstance(tab, dict):
                    tab_components = tab.get("components", [])
                    if tab_components:
                        result = _search(tab_components, comp, depth + 1)
                        if result:
                            return result

            # Search in table rows (rows[][] structure)
            rows = comp.get("rows", [])
            for row in rows:
                if isinstance(row, list):
                    for cell in row:
                        if isinstance(cell, dict):
                            cell_components = cell.get("components", [])
                            if cell_components:
                                result = _search(cell_components, comp, depth + 1)
                                if result:
                                    return result

        return None

    result = _search(components, None)
    if result is None:
        raise ValueError(f"Component with key '{key}' not found")
    return result


def get_all_component_keys(
    components: list[dict[str, Any]],
    include_duplicates: bool = False,
) -> set[str] | list[str]:
    """Get all component keys in the tree.

    Args:
        components: List of Form.io components.
        include_duplicates: If True, returns list with duplicates preserved.
            If False (default), returns set of unique keys.

    Returns:
        Set of unique keys, or list with duplicates if include_duplicates=True.

    Raises:
        RecursionError: If nesting exceeds MAX_RECURSION_DEPTH.
    """
    # Handle non-list components (BPA API may return int or other types)
    if not isinstance(components, list):
        return [] if include_duplicates else set()

    keys: list[str] = []

    def _collect(comps: list[dict[str, Any]], depth: int = 0) -> None:
        if depth > MAX_RECURSION_DEPTH:
            raise RecursionError(
                f"Component tree exceeds maximum depth of {MAX_RECURSION_DEPTH}"
            )

        # Skip if comps is not a list (defensive for recursive calls)
        if not isinstance(comps, list):
            return

        for comp in comps:
            if not isinstance(comp, dict):
                continue

            key = comp.get("key")
            if key:
                keys.append(key)

            # Collect from nested components
            nested = comp.get("components", [])
            if nested and isinstance(nested, list):
                _collect(nested, depth + 1)

            # Collect from columns
            columns = comp.get("columns", [])
            if isinstance(columns, list):
                for col in columns:
                    if isinstance(col, dict):
                        col_components = col.get("components", [])
                        if col_components and isinstance(col_components, list):
                            _collect(col_components, depth + 1)

            # Collect from tabs
            tabs = comp.get("tabs", [])
            if isinstance(tabs, list):
                for tab in tabs:
                    if isinstance(tab, dict):
                        tab_components = tab.get("components", [])
                        if tab_components and isinstance(tab_components, list):
                            _collect(tab_components, depth + 1)

            # Collect from table rows (rows[][] structure)
            rows = comp.get("rows", [])
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, list):
                        for cell in row:
                            if isinstance(cell, dict):
                                cell_comps = cell.get("components", [])
                                if cell_comps and isinstance(cell_comps, list):
                                    _collect(cell_comps, depth + 1)

    _collect(components)

    if include_duplicates:
        return keys
    return set(keys)


def validate_component_key_unique(
    components: list[dict[str, Any]],
    key: str,
) -> bool:
    """Check if a key is unique within the component tree.

    Args:
        components: Existing Form.io components.
        key: Key to check for uniqueness.

    Returns:
        True if key is unique, False if it already exists.
    """
    existing = get_all_component_keys(components)
    return key not in existing


def insert_component(
    components: list[dict[str, Any]],
    component: dict[str, Any],
    parent_key: str | None = None,
    position: int | None = None,
    column_index: int | str | None = None,
    row_index: int | str | None = None,
    cell_index: int | str | None = None,
) -> list[dict[str, Any]]:
    """Insert a component into the tree.

    Creates a deep copy of the components and inserts the new component.
    Does not mutate the original list.

    Args:
        components: Original Form.io components list.
        component: Component to insert.
        parent_key: Key of parent container to insert into.
                   If None, inserts at root level.
        position: Position to insert at (0-indexed).
                 If None, appends to end.
        column_index: For columns-type parents, which column to insert into.
                     Use int (0-indexed) for specific column, or "all" to
                     insert into every column. Required for columns component.
        row_index: For table-type parents, which row to insert into.
                  Use int (0-indexed) for specific row, or "all" to insert
                  into every row. Required for table component.
        cell_index: For table-type parents, which cell in the row to insert into.
                   Use int (0-indexed) for specific cell, or "all" to insert
                   into every cell. Required for table component.

    Returns:
        New components list with the component inserted.

    Raises:
        ValueError: If parent_key is specified but not found,
                   or if parent is not a container type,
                   or if column_index is missing for columns parent,
                   or if row_index/cell_index is missing for table parent,
                   or if column_index and row_index/cell_index are both specified.
    """
    # NOTE: Deep copy ensures immutability - input components are never mutated.
    # For large forms (500+ components), this may impact performance (~50-100ms).
    # If performance becomes critical, consider structural sharing optimization.
    result = copy.deepcopy(components)
    new_comp = copy.deepcopy(component)

    # Add BPA defaults if not present
    for key, value in BPA_COMPONENT_DEFAULTS.items():
        if key not in new_comp:
            new_comp[key] = copy.deepcopy(value)

    # Validate mutual exclusivity of column_index and row_index/cell_index
    if column_index is not None and (row_index is not None or cell_index is not None):
        raise ValueError(
            "Cannot specify both column_index and row_index/cell_index. "
            "Use column_index for columns components, "
            "or row_index/cell_index for table components."
        )

    if parent_key is None:
        # Insert at root level
        if position is None:
            result.append(new_comp)
        else:
            result.insert(position, new_comp)
    else:
        # Find parent and insert
        parent_result = find_component(result, parent_key)
        if parent_result is None:
            raise ValueError(f"Parent component '{parent_key}' not found")

        parent_comp = parent_result[0]
        parent_type = parent_comp.get("type", "")

        if parent_type not in CONTAINER_TYPES:
            raise ValueError(
                f"Component '{parent_key}' (type: {parent_type}) is not a container. "
                f"Valid container types: {', '.join(sorted(CONTAINER_TYPES))}"
            )

        # Special handling for columns type
        if parent_type in COLUMN_BASED_CONTAINERS:
            columns = parent_comp.get("columns", [])
            num_columns = len(columns)

            if column_index is None:
                raise ValueError(
                    f"Parent '{parent_key}' is a columns component with "
                    f"{num_columns} columns. Specify column_index "
                    f"(0-{num_columns - 1}) to target a specific column, "
                    f'or "all" to insert into every column. '
                    f"Use form_component_get('{parent_key}') to inspect structure."
                )

            # Handle "all" - insert into every column
            if column_index == "all":
                for col_idx, col in enumerate(columns):
                    if "components" not in col:
                        col["components"] = []
                    # Deep copy for each column to avoid shared references
                    col_comp = copy.deepcopy(new_comp)
                    # Append unique suffix to key to avoid duplicates
                    if "key" in col_comp:
                        col_comp["key"] = f"{col_comp['key']}_{col_idx}"
                    if position is None:
                        col["components"].append(col_comp)
                    else:
                        col["components"].insert(position, col_comp)
                return result

            # Validate numeric column_index
            if not isinstance(column_index, int):
                raise ValueError(
                    f'column_index must be an int or "all", got: {column_index!r}'
                )

            if column_index < 0 or column_index >= num_columns:
                raise ValueError(
                    f"column_index {column_index} is out of range. "
                    f"Valid range: 0-{num_columns - 1} "
                    f"({num_columns} columns available)."
                )

            # Insert into the specified column's components array
            target_column = columns[column_index]
            if "components" not in target_column:
                target_column["components"] = []

            if position is None:
                target_column["components"].append(new_comp)
            else:
                target_column["components"].insert(position, new_comp)

            return result

        # Special handling for table type
        if parent_type in TABLE_BASED_CONTAINERS:
            rows = parent_comp.get("rows", [])
            num_rows = len(rows)

            if row_index is None or cell_index is None:
                raise ValueError(
                    f"Parent '{parent_key}' is a table component with "
                    f"{num_rows} rows. Specify both row_index and cell_index "
                    f"to target a specific cell. Use row_index=0..{num_rows - 1} "
                    f'and cell_index=0..<num_cells>, or "all" for either. '
                    f"Use form_component_get('{parent_key}') to inspect structure."
                )

            # Determine which rows to target
            if row_index == "all":
                target_row_indices = list(range(num_rows))
            else:
                if not isinstance(row_index, int):
                    raise ValueError(
                        f'row_index must be an int or "all", got: {row_index!r}'
                    )
                if row_index < 0 or row_index >= num_rows:
                    raise ValueError(
                        f"row_index {row_index} is out of range. "
                        f"Valid range: 0-{num_rows - 1} "
                        f"({num_rows} rows available)."
                    )
                target_row_indices = [row_index]

            # Process each target row
            for r_idx in target_row_indices:
                row = rows[r_idx]
                if not isinstance(row, list):
                    continue

                num_cells = len(row)

                # Determine which cells to target
                if cell_index == "all":
                    target_cell_indices = list(range(num_cells))
                else:
                    if not isinstance(cell_index, int):
                        raise ValueError(
                            f'cell_index must be an int or "all", got: {cell_index!r}'
                        )
                    if cell_index < 0 or cell_index >= num_cells:
                        raise ValueError(
                            f"cell_index {cell_index} is out of range for row {r_idx}. "
                            f"Valid range: 0-{num_cells - 1} "
                            f"({num_cells} cells in row)."
                        )
                    target_cell_indices = [cell_index]

                # Process each target cell
                for c_idx in target_cell_indices:
                    cell = row[c_idx]
                    if not isinstance(cell, dict):
                        continue

                    if "components" not in cell:
                        cell["components"] = []

                    # Deep copy for each cell to avoid shared references
                    cell_comp = copy.deepcopy(new_comp)

                    # Append suffix to avoid key duplicates across cells
                    # Both "all": key_0_0, key_0_1; one "all": key_0, key_1
                    if "key" in cell_comp:
                        if row_index == "all" and cell_index == "all":
                            cell_comp["key"] = f"{cell_comp['key']}_{r_idx}_{c_idx}"
                        elif row_index == "all":
                            cell_comp["key"] = f"{cell_comp['key']}_{r_idx}"
                        elif cell_index == "all":
                            cell_comp["key"] = f"{cell_comp['key']}_{c_idx}"
                        # If neither is "all", keep original key

                    if position is None:
                        cell["components"].append(cell_comp)
                    else:
                        cell["components"].insert(position, cell_comp)

            return result

        # Standard container handling (panel, tabs, etc.)
        # Ensure components list exists
        if "components" not in parent_comp:
            parent_comp["components"] = []

        if position is None:
            parent_comp["components"].append(new_comp)
        else:
            parent_comp["components"].insert(position, new_comp)

    return result


def remove_component(
    components: list[dict[str, Any]],
    key: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Remove a component from the tree.

    Creates a deep copy and removes the component.

    Args:
        components: Original Form.io components list.
        key: Key of component to remove.

    Returns:
        Tuple of (new_components, removed_component).

    Raises:
        ValueError: If component is not found.
    """
    # Deep copy ensures immutability (see insert_component for performance notes)
    result = copy.deepcopy(components)

    # Find and remove
    parent, siblings, index = find_component_parent(result, key)
    removed = siblings.pop(index)

    return (result, removed)


def update_component(
    components: list[dict[str, Any]],
    key: str,
    updates: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Update properties of a component.

    Merges updates into the existing component. Deep merges nested dicts.

    Args:
        components: Original Form.io components list.
        key: Key of component to update.
        updates: Properties to update/add.

    Returns:
        Tuple of (new_components, previous_state).
        previous_state contains the component's state before update.

    Raises:
        ValueError: If component is not found.
    """
    # Deep copy ensures immutability (see insert_component for performance notes)
    result = copy.deepcopy(components)

    found = find_component(result, key)
    if found is None:
        raise ValueError(f"Component with key '{key}' not found")

    comp = found[0]
    previous_state = copy.deepcopy(comp)

    # Deep merge updates
    _deep_merge(comp, updates)

    return (result, previous_state)


def move_component(
    components: list[dict[str, Any]],
    key: str,
    new_parent_key: str | None = None,
    new_position: int | None = None,
    column_index: int | str | None = None,
    row_index: int | str | None = None,
    cell_index: int | str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str | int | None]]:
    """Move a component to a new location in the tree.

    Args:
        components: Original Form.io components list.
        key: Key of component to move.
        new_parent_key: New parent container key, or None for root.
        new_position: Position in new parent, or None for end.
        column_index: For columns-type parents, which column to move into.
                     Use int (0-indexed) for specific column, or "all" to
                     move into every column (creates copies). Required for columns.
        row_index: For table-type parents, which row to move into.
                  Use int (0-indexed) for specific row, or "all" to move
                  into every row (creates copies). Required for tables.
        cell_index: For table-type parents, which cell in the row to move into.
                   Use int (0-indexed) for specific cell, or "all" to move
                   into every cell (creates copies). Required for tables.

    Returns:
        Tuple of (new_components, move_info).
        move_info contains old_parent, old_position, new_parent, new_position,
        column_index, row_index, and cell_index (if applicable).

    Raises:
        ValueError: If component or new parent not found,
                   or if column_index is missing for columns parent,
                   or if row_index/cell_index is missing for table parent.
    """
    # First remove the component
    result, removed = remove_component(components, key)

    # Track old position
    old_parent, _, old_index = find_component_parent(components, key)
    old_parent_key = old_parent.get("key") if old_parent else None

    # Insert at new location (all indices passed for columns/table support)
    result = insert_component(
        result,
        removed,
        new_parent_key,
        new_position,
        column_index,
        row_index,
        cell_index,
    )

    # Determine actual new position
    actual_position: int | None = None
    if new_parent_key:
        new_parent = find_component(result, new_parent_key)
        if new_parent:
            parent_comp = new_parent[0]
            parent_type = parent_comp.get("type", "")
            # For columns, get position from specific column
            if parent_type in COLUMN_BASED_CONTAINERS and column_index is not None:
                columns = parent_comp.get("columns", [])
                # For "all", use first column for position calculation
                col_idx = 0 if column_index == "all" else column_index
                if isinstance(col_idx, int) and 0 <= col_idx < len(columns):
                    col_components = columns[col_idx].get("components", [])
                    actual_position = (
                        new_position
                        if new_position is not None
                        else len(col_components) - 1
                    )
            # For tables, get position from specific cell
            elif parent_type in TABLE_BASED_CONTAINERS and row_index is not None:
                rows = parent_comp.get("rows", [])
                # For "all", use first row/cell for position calculation
                r_idx = 0 if row_index == "all" else row_index
                c_idx = 0 if cell_index == "all" else cell_index
                if isinstance(r_idx, int) and isinstance(c_idx, int):
                    if 0 <= r_idx < len(rows) and isinstance(rows[r_idx], list):
                        row = rows[r_idx]
                        if 0 <= c_idx < len(row) and isinstance(row[c_idx], dict):
                            cell_components = row[c_idx].get("components", [])
                            actual_position = (
                                new_position
                                if new_position is not None
                                else len(cell_components) - 1
                            )
            else:
                new_siblings = parent_comp.get("components", [])
                actual_position = (
                    new_position if new_position is not None else len(new_siblings) - 1
                )
        else:
            actual_position = new_position
    else:
        actual_position = new_position if new_position is not None else len(result) - 1

    move_info: dict[str, str | int | None] = {
        "old_parent": old_parent_key,
        "old_position": old_index,
        "new_parent": new_parent_key,
        "new_position": actual_position,
        "column_index": column_index,
        "row_index": row_index,
        "cell_index": cell_index,
    }

    return (result, move_info)


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Deep merge source dict into target dict (mutates target).

    Args:
        target: Dict to merge into.
        source: Dict to merge from.
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


# =============================================================================
# Component Builders - Convenience functions for creating common components
# =============================================================================


def build_textfield(
    key: str,
    label: str,
    *,
    required: bool = False,
    placeholder: str = "",
    tooltip: str = "",
    description: str = "",
    size: str = "md",
    hidden: bool = False,
    disabled: bool = False,
    default_value: str = "",
) -> dict[str, Any]:
    """Build a textfield component with BPA-specific properties.

    Args:
        key: Unique component key (e.g., "applicantFullName").
        label: Display label.
        required: Whether field is required.
        placeholder: Placeholder text.
        tooltip: Tooltip text.
        description: Field description.
        size: Field size ("sm", "md", "lg").
        hidden: Whether field is hidden.
        disabled: Whether field is disabled.
        default_value: Default value.

    Returns:
        Complete textfield component definition.
    """
    component: dict[str, Any] = {
        "type": "textfield",
        "key": key,
        "label": label,
        "size": size,
        "validate": {"required": required},
        "input": True,
        "tableView": True,
        **BPA_COMPONENT_DEFAULTS,
    }

    if placeholder:
        component["placeholder"] = placeholder
    if tooltip:
        component["tooltip"] = tooltip
    if description:
        component["description"] = description
    if hidden:
        component["hidden"] = True
    if disabled:
        component["disabled"] = True
    if default_value:
        component["defaultValue"] = default_value

    return component


def build_number(
    key: str,
    label: str,
    *,
    required: bool = False,
    min_value: float | None = None,
    max_value: float | None = None,
    decimal_limit: int | None = None,
    default_value: float | None = None,
) -> dict[str, Any]:
    """Build a number component.

    Args:
        key: Unique component key.
        label: Display label.
        required: Whether field is required.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        decimal_limit: Maximum decimal places.
        default_value: Default value.

    Returns:
        Complete number component definition.
    """
    component: dict[str, Any] = {
        "type": "number",
        "key": key,
        "label": label,
        "validate": {"required": required},
        "input": True,
        "tableView": True,
        **BPA_COMPONENT_DEFAULTS,
    }

    if min_value is not None:
        component["validate"]["min"] = min_value
    if max_value is not None:
        component["validate"]["max"] = max_value
    if decimal_limit is not None:
        component["decimalLimit"] = decimal_limit
    if default_value is not None:
        component["defaultValue"] = default_value

    return component


def build_select(
    key: str,
    label: str,
    *,
    required: bool = False,
    data_source: str = "values",
    values: list[dict[str, str]] | None = None,
    catalog: str | None = None,
    multiple: bool = False,
    placeholder: str = "",
) -> dict[str, Any]:
    """Build a select/dropdown component.

    Args:
        key: Unique component key.
        label: Display label.
        required: Whether field is required.
        data_source: Data source type ("values", "Catalogue", "url").
        values: List of {"label": ..., "value": ...} options.
        catalog: Catalog name (when data_source is "Catalogue").
        multiple: Allow multiple selections.
        placeholder: Placeholder text.

    Returns:
        Complete select component definition.
    """
    component: dict[str, Any] = {
        "type": "select",
        "key": key,
        "label": label,
        "validate": {"required": required},
        "input": True,
        "tableView": True,
        "data": {"dataSrc": data_source},
        **BPA_COMPONENT_DEFAULTS,
    }

    if data_source == "values" and values:
        component["data"]["values"] = values
    elif data_source == "Catalogue" and catalog:
        component["data"]["catalog"] = catalog
        component["data"]["systemSource"] = "BPA"

    if multiple:
        component["multiple"] = True
    if placeholder:
        component["placeholder"] = placeholder

    return component


def build_checkbox(
    key: str,
    label: str,
    *,
    required: bool = False,
    default_value: bool = False,
) -> dict[str, Any]:
    """Build a checkbox component.

    Args:
        key: Unique component key.
        label: Display label.
        required: Whether field is required.
        default_value: Default checked state.

    Returns:
        Complete checkbox component definition.
    """
    return {
        "type": "checkbox",
        "key": key,
        "label": label,
        "validate": {"required": required},
        "defaultValue": default_value,
        "input": True,
        "tableView": True,
        **BPA_COMPONENT_DEFAULTS,
    }


def build_textarea(
    key: str,
    label: str,
    *,
    required: bool = False,
    rows: int = 3,
    placeholder: str = "",
) -> dict[str, Any]:
    """Build a textarea component.

    Args:
        key: Unique component key.
        label: Display label.
        required: Whether field is required.
        rows: Number of visible rows.
        placeholder: Placeholder text.

    Returns:
        Complete textarea component definition.
    """
    component: dict[str, Any] = {
        "type": "textarea",
        "key": key,
        "label": label,
        "rows": rows,
        "validate": {"required": required},
        "input": True,
        "tableView": True,
        **BPA_COMPONENT_DEFAULTS,
    }

    if placeholder:
        component["placeholder"] = placeholder

    return component


def build_panel(
    key: str,
    title: str,
    *,
    components: list[dict[str, Any]] | None = None,
    collapsible: bool = False,
    collapsed: bool = False,
) -> dict[str, Any]:
    """Build a panel container component.

    Args:
        key: Unique component key.
        title: Panel title.
        components: Nested components.
        collapsible: Whether panel can be collapsed.
        collapsed: Initial collapsed state.

    Returns:
        Complete panel component definition.
    """
    panel: dict[str, Any] = {
        "type": "panel",
        "key": key,
        "title": title,
        "components": components or [],
        "input": False,
        "tableView": False,
        **BPA_COMPONENT_DEFAULTS,
    }

    if collapsible:
        panel["collapsible"] = True
        panel["collapsed"] = collapsed

    return panel


def build_columns(
    key: str,
    *,
    column_count: int = 2,
    components_per_column: list[list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build a columns layout component.

    Args:
        key: Unique component key.
        column_count: Number of columns (default 2).
        components_per_column: List of component lists for each column.

    Returns:
        Complete columns component definition.
    """
    columns = []
    width = 12 // column_count  # Bootstrap grid (12 columns)

    for i in range(column_count):
        col_components = (
            components_per_column[i]
            if components_per_column and i < len(components_per_column)
            else []
        )
        columns.append(
            {
                "components": col_components,
                "width": width,
                "offset": 0,
                "push": 0,
                "pull": 0,
                "size": "md",
            }
        )

    return {
        "type": "columns",
        "key": key,
        "columns": columns,
        "input": False,
        "tableView": False,
        **BPA_COMPONENT_DEFAULTS,
    }


# =============================================================================
# Validation Functions
# =============================================================================


def validate_component(component: dict[str, Any]) -> list[str]:
    """Validate a component structure.

    Args:
        component: Component to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    # Required fields
    if not component.get("key"):
        errors.append("Component must have a 'key' property")
    elif not _is_valid_key(component["key"]):
        errors.append(
            f"Invalid key format '{component['key']}'. "
            "Keys must be alphanumeric with underscores, starting with a letter."
        )

    if not component.get("type"):
        errors.append("Component must have a 'type' property")

    # Type-specific validation
    comp_type = component.get("type", "")

    if comp_type in ("textfield", "textarea", "number", "select", "checkbox"):
        if not component.get("label"):
            errors.append(
                f"Component type '{comp_type}' should have a 'label' property"
            )

    if comp_type == "select":
        data = component.get("data", {})
        data_src = data.get("dataSrc", "values")
        if data_src == "values" and not data.get("values"):
            # Values source but no values - just a warning
            pass
        elif data_src == "Catalogue" and not data.get("catalog"):
            errors.append(
                "Select with Catalogue source must have 'data.catalog' property"
            )

    return errors


def _is_valid_key(key: str) -> bool:
    """Check if a key follows valid naming conventions.

    Args:
        key: Component key to validate.

    Returns:
        True if key is valid.
    """
    # Must start with letter, contain only alphanumeric and underscores
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", key))


def validate_form_schema(schema: dict[str, Any]) -> list[str]:
    """Validate a complete form schema.

    Args:
        schema: Form schema with components.

    Returns:
        List of validation error messages.
    """
    errors: list[str] = []

    if "components" not in schema:
        errors.append("Form schema must have 'components' array")
        return errors

    components = schema["components"]
    if not isinstance(components, list):
        errors.append("'components' must be an array")
        return errors

    # Check for duplicate keys using list with duplicates preserved
    all_keys = get_all_component_keys(components, include_duplicates=True)
    seen: set[str] = set()
    for key in all_keys:
        if key in seen:
            errors.append(f"Duplicate component key: '{key}'")
        else:
            seen.add(key)

    # Validate each component
    for i, comp in enumerate(components):
        comp_errors = validate_component(comp)
        for error in comp_errors:
            errors.append(f"Component [{i}]: {error}")

    return errors
