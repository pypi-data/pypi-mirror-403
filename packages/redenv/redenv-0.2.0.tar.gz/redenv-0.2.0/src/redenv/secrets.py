import json
from typing import Any, Callable, Optional, Type, TypeVar, Union
from .errors import RedenvError

T = TypeVar("T")

class Secrets(dict):
    """
    A specialized dictionary for managing decrypted secrets with 
    type-casting, scoping, and validation capabilities.
    """

    def get(self, key: str, default: Any = None, cast: Optional[Union[Type[T], Callable[[Any], T]]] = None) -> Union[T, Any]:
        """
        Retrieves a secret and optionally casts it to a specific type.
        """
        value = super().get(key)
        
        if value is None:
            return default
            
        if cast is None:
            return value
            
        try:
            # Special handling for boolean strings
            if cast is bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on", "t")
                return bool(value)
                
            # Special handling for JSON types (dict/list)
            if (cast is dict or cast is list) and isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return default
            
            # General casting (int, float, or custom callable)
            return cast(value) # type: ignore
            
        except (ValueError, TypeError):
            return default

    def __getitem__(self, key: str) -> Any:
        """
        Ensures standard dict access still works but raises a 
        helpful error if the key is missing.
        """
        try:
            return super().__getitem__(key)
        except KeyError:
            raise KeyError(f"Secret '{key}' not found in Redenv.")

    def scope(self, prefix: str) -> "Secrets":
        """
        Returns a new Secrets object containing only the keys that start with
        the given prefix. The prefix is stripped from the keys in the new object.
        """
        subset = Secrets()
        for key, value in self.items():
            if key.startswith(prefix):
                new_key = key[len(prefix):]
                if new_key:
                    subset[new_key] = value
        return subset

    def require(self, *keys: str) -> "Secrets":
        """
        Validates that all provided keys exist.
        Raises RedenvError if any key is missing.
        Returns self for chaining.
        """
        missing = [k for k in keys if k not in self]
        if missing:
            raise RedenvError(
                f"Missing required secrets: {', '.join(missing)}",
                "SECRET_NOT_FOUND"
            )
        return self

    def __repr__(self) -> str:
        """
        Masks secret values to prevent accidental leakage in logs.
        """
        masked = {k: "********" for k in self.keys()}
        return f"Secrets({masked})"

    def __str__(self) -> str:
        """
        Returns the masked representation of the secrets.
        """
        return self.__repr__()