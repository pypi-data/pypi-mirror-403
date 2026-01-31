"""Registry and base classes for issue checkers."""

import ast
from typing import List, Dict, Any


class BaseChecker:
    """Base class for all issue checkers."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the checker.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}

    def check(self, module_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Performs the check on the module data.

        Args:
            module_info: Analyzed module data.

        Returns:
            List of found issues.
        """
        raise NotImplementedError

    def get_category(self) -> str:
        """Returns the category name for this checker."""
        raise NotImplementedError
