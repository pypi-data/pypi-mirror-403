import re
from typing import Dict
from .errors import RedenvError

# Match ${VAR} not preceded by a backslash
REFERENCE_REGEX = re.compile(r"(?<!\\)\$\{([a-zA-Z0-9_]+)\}")

def expand_secrets(secrets: Dict[str, str]) -> Dict[str, str]:
    r"""
    Expands variable references in a dictionary of secrets.
    Supports recursion, cycle detection, and escaped references (\${VAR}).
    """
    expanded: Dict[str, str] = {}
    cache: Dict[str, str] = {}
    stack: list[str] = []

    def resolve(key: str) -> str:
        if key in cache:
            return cache[key]

        if key in stack:
            cycle = " -> ".join(stack + [key])
            raise RedenvError(f"Circular dependency detected: {cycle}", "INVALID_INPUT")

        stack.append(key)
        value = secrets[key]

        def replacer(match: re.Match) -> str:
            ref_key = match.group(1)
            return resolve(ref_key) if ref_key in secrets else match.group(0)

        # Expand all unescaped references
        resolved = REFERENCE_REGEX.sub(replacer, value)

        # Convert escaped references \${VAR} -> ${VAR}
        resolved = resolved.replace(r"\${", "${")

        cache[key] = resolved
        stack.pop()
        return resolved

    for key in secrets:
        expanded[key] = resolve(key)

    return expanded
