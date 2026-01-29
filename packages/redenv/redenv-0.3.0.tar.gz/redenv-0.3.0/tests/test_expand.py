import pytest
from redenv.expand import expand_secrets
from redenv.errors import RedenvError

def test_basic_expansion():
    secrets = {
        "BASE_URL": "https://api.example.com",
        "AUTH_URL": "${BASE_URL}/auth"
    }
    expanded = expand_secrets(secrets)
    assert expanded["AUTH_URL"] == "https://api.example.com/auth"

def test_recursive_expansion():
    secrets = {
        "A": "value",
        "B": "${A}",
        "C": "${B}"
    }
    expanded = expand_secrets(secrets)
    assert expanded["C"] == "value"

def test_multiple_references():
    secrets = {
        "PROTOCOL": "https",
        "DOMAIN": "example.com",
        "URL": "${PROTOCOL}://${DOMAIN}"
    }
    expanded = expand_secrets(secrets)
    assert expanded["URL"] == "https://example.com"

def test_circular_dependency():
    secrets = {
        "A": "${B}",
        "B": "${A}"
    }
    with pytest.raises(RedenvError, match="Circular dependency detected"):
        expand_secrets(secrets)

def test_missing_reference():
    secrets = {
        "A": "${MISSING}"
    }
    expanded = expand_secrets(secrets)
    assert expanded["A"] == "${MISSING}"

def test_escaped_reference():
    secrets = {
        "A": r"\${NOT_EXPANDED}"
    }
    expanded = expand_secrets(secrets)
    assert expanded["A"] == "${NOT_EXPANDED}"

def test_mixed_escaped_and_normal():
    secrets = {
        "VAR": "value",
        "A": r"\${VAR} and ${VAR}"
    }
    expanded = expand_secrets(secrets)
    assert expanded["A"] == "${VAR} and value"
