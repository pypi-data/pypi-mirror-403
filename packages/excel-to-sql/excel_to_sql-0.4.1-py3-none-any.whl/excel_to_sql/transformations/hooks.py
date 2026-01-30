"""
Pre/post processing hooks system.

Allows executing custom code at various points in the import/export pipeline.
"""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd


@dataclass
class ImportContext:
    """
    Context object passed to import hooks.

    Contains all relevant information about the current import operation.
    """

    file_path: Path
    file_type: str
    raw_df: pd.DataFrame
    mapping: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)


@dataclass
class ExportContext:
    """
    Context object passed to export hooks.

    Contains all relevant information about the current export operation.
    """

    output_path: Path
    query: Optional[str]
    table: Optional[str]
    df: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)


HookFunction = Callable[[ImportContext], None]


class HookSystem:
    """
    Manages pre/post processing hooks for import and export operations.

    Hooks are callable objects that receive context information
    and can modify data or perform side effects.

    Hook Types:
    - pre_import: Before file processing
    - post_import: After database write
    - pre_export: Before query execution
    - post_export: After file creation

    Example:
        hooks = HookSystem()

        @hooks.register_pre_import
        def validate_data(context: ImportContext):
            if context.raw_df.isnull().any().any():
                raise ValueError("Data contains null values")

        @hooks.register_post_import
        def send_notification(context: ImportContext):
            notify_import_complete(context.file_path)
    """

    def __init__(self) -> None:
        """Initialize hook system."""
        self._pre_import_hooks: List[HookFunction] = []
        self._post_import_hooks: List[HookFunction] = []
        self._pre_export_hooks: List[Callable] = []
        self._post_export_hooks: List[Callable] = []

    def register_pre_import(self, func: HookFunction) -> HookFunction:
        """
        Register a pre-import hook.

        Can be used as decorator:

            @hooks.register_pre_import
            def my_hook(context):
                pass

        Args:
            func: Function that accepts ImportContext

        Returns:
            The same function (for decorator usage)
        """
        self._pre_import_hooks.append(func)
        return func

    def register_post_import(self, func: HookFunction) -> HookFunction:
        """
        Register a post-import hook.

        Can be used as decorator.
        See register_pre_import() for usage.
        """
        self._post_import_hooks.append(func)
        return func

    def register_pre_export(self, func: Callable) -> Callable:
        """Register a pre-export hook."""
        self._pre_export_hooks.append(func)
        return func

    def register_post_export(self, func: Callable) -> Callable:
        """Register a post-export hook."""
        self._post_export_hooks.append(func)
        return func

    def execute_pre_import(self, context: ImportContext) -> None:
        """
        Execute all pre-import hooks.

        Args:
            context: Import context with file and data information

        Raises:
            Exception: If any hook raises an exception
        """
        for hook in self._pre_import_hooks:
            hook(context)

    def execute_post_import(self, context: ImportContext) -> None:
        """
        Execute all post-import hooks.

        Args:
            context: Import context with file and data information

        Raises:
            Exception: If any hook raises an exception
        """
        for hook in self._post_import_hooks:
            hook(context)

    def execute_pre_export(self, context: ExportContext) -> None:
        """Execute all pre-export hooks."""
        for hook in self._pre_export_hooks:
            hook(context)

    def execute_post_export(self, context: ExportContext) -> None:
        """Execute all post-export hooks."""
        for hook in self._post_export_hooks:
            hook(context)

    def clear_pre_import(self) -> None:
        """Remove all pre-import hooks."""
        self._pre_import_hooks.clear()

    def clear_post_import(self) -> None:
        """Remove all post-import hooks."""
        self._post_import_hooks.clear()

    def clear_pre_export(self) -> None:
        """Remove all pre-export hooks."""
        self._pre_export_hooks.clear()

    def clear_post_export(self) -> None:
        """Remove all post-export hooks."""
        self._post_export_hooks.clear()

    def clear_all(self) -> None:
        """Remove all hooks."""
        self.clear_pre_import()
        self.clear_post_import()
        self.clear_pre_export()
        self.clear_post_export()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "HookSystem":
        """
        Create HookSystem from configuration dict.

        Args:
            config: Configuration with "hooks" key

        Example:
            config = {
                "hooks": {
                    "pre_import": [
                        {"module": "my_hooks", "function": "validate"}
                    ]
                }
            }
        """
        hooks = cls()

        # TODO: Implement dynamic hook loading from config
        # This would involve importing modules and calling functions

        return hooks
