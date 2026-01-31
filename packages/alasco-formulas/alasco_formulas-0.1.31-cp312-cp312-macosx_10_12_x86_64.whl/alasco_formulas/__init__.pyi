from typing import Any, Literal, Protocol, Self

class Node(Protocol):
    """A node in the formula evaluation tree.

    Attributes:
        id: Optional unique identifier for the node
        name: Display name for the node
        formula: Formula string to evaluate (e.g., "=10+5" or "=@ref1")
        value: The evaluated result as a string (empty before evaluation)
        is_hidden: Whether the node is hidden
        children: List of child nodes
    """

    id: Any
    name: str
    formula: str
    value: str
    is_hidden: bool
    children: list[Self]

def evaluate(formula: str) -> str:
    """Evaluates a single formula string.

    Args:
        formula: Formula string to evaluate (e.g., "=10+5" or "=@ref1")

    Returns:
        The evaluated result as a string, or an error indication.
    """
    ...

def evaluate_boolean(formula: str) -> str:
    """Evaluates a boolean expression formula string.

    Args:
        formula: Boolean expression string to evaluate (e.g., "1 == 1" or "5 > 3")

    Returns:
        The evaluated result as a string ("true" or "false"), or an error indication.
    """
    ...

def evaluate_tree[T: Node](root: T) -> T:
    """Evaluates a tree of nodes with formulas.

    This function evaluates all formulas in the tree, handling references
    between nodes (e.g., "=@ref1" references another node's value).

    Args:
        root: A Node object representing the root of the tree to evaluate

    Returns:
        The same tree structure with all 'value' fields populated with evaluation results

    Raises:
        TypeError: If the input does not match the Node protocol or attribute types are incorrect
        AttributeError: If required attributes are missing or cannot be accessed
        ValueError: If the input cannot be processed
    """
    ...

def get_tokens(
    formula: str,
) -> list[
    tuple[
        str,
        Literal[
            "number",
            "operator",
            "nodereference",
            "function",
            "aggregation",
            "conditional",
            "parenthesis",
            "unexpected",
        ],
    ]
]:
    """Parses a formula string into tokens with preserved number formats.

    This function parses a formula and returns a list of tokens, where each token
    contains the original string value and its type. Numbers preserve their original
    decimal separator (comma or point) for locale-based formatting.

    Args:
        formula: Formula string to tokenize (e.g., "=3,14 + 2.5")

    Returns:
        A list of tuples, where each tuple contains (value, token_type)

    Raises:
        ValueError: If the input cannot be parsed or is invalid
    """
    ...

def rename_nodes[T: Node](old_root: T, new_root: T) -> T:
    """Updates formulas in new_root based on node renames detected between old_root and new_root.

    This function compares two trees with identical topology to detect node renames and updates
    all formulas in new_root to use the correct unambiguous references. This handles cases where
    renames create or resolve ambiguity (e.g., renaming "ItemA" to "ItemB" when another "ItemB"
    already exists, resulting in "ItemB[1]" and "ItemB[2]").

    Args:
        old_root: A Node object representing the tree before renaming
        new_root: A Node object representing the tree after renaming

    Returns:
        The new_root tree structure with all formulas updated

    Raises:
        TypeError: If the input does not match the Node protocol or attribute types are incorrect
        AttributeError: If required attributes are missing or cannot be accessed
        ValueError: If the input cannot be processed or trees have different topology
    """
    ...

def expand_tree_formulas[T: Node](root: T) -> T:
    """Recursively expands node references in all formulas throughout the tree.

    This function traverses the tree and replaces node references in each formula with their expanded
    formulas until all references point to "leaf" nodes (nodes whose formulas don't contain other references).
    This allows you to see the final line of dependencies without fully evaluating to concrete values.

    Args:
        root: A Node object representing the root of the tree

    Returns:
        The same tree structure with all formulas expanded

    Raises:
        TypeError: If the input does not match the Node protocol or attribute types are incorrect
        AttributeError: If required attributes are missing or cannot be accessed
        ValueError: If the input cannot be processed
    """
    ...
