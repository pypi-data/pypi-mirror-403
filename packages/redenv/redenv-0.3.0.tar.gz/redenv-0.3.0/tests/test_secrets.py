import pytest
from redenv.secrets import Secrets
from redenv.errors import RedenvError

def test_secrets_access():
    data = {"KEY": "value"}
    secrets = Secrets(data)
    assert secrets["KEY"] == "value"
    assert secrets.get("KEY") == "value"
    
    # Missing keys should return None instead of raising KeyError
    assert secrets["MISSING"] is None

def test_secrets_cast_int():
    secrets = Secrets({"PORT": "8080", "BAD": "abc"})
    assert secrets.get("PORT", cast=int) == 8080
    assert secrets.get("BAD", cast=int) == None # Defaults to None on failure
    assert secrets.get("BAD", default=0, cast=int) == 0

def test_secrets_cast_bool():
    secrets = Secrets({
        "FLAG_TRUE": "true",
        "FLAG_1": "1",
        "FLAG_YES": "yes",
        "FLAG_FALSE": "false",
        "FLAG_0": "0"
    })
    
    assert secrets.get("FLAG_TRUE", cast=bool) is True
    assert secrets.get("FLAG_1", cast=bool) is True
    assert secrets.get("FLAG_YES", cast=bool) is True
    assert secrets.get("FLAG_FALSE", cast=bool) is False
    assert secrets.get("FLAG_0", cast=bool) is False

def test_secrets_cast_json():
    secrets = Secrets({"CONFIG": '{"foo": "bar"}'})
    config = secrets.get("CONFIG", cast=dict)
    assert isinstance(config, dict)
    assert config["foo"] == "bar"

def test_secrets_scoping():
    secrets = Secrets({
        "APP_NAME": "MyApp",
        "STRIPE_KEY": "sk_123",
        "STRIPE_SECRET": "wh_456"
    })
    
    stripe = secrets.scope("STRIPE_")
    
    # Prefix should be stripped
    assert stripe["KEY"] == "sk_123"
    assert stripe["SECRET"] == "wh_456"
    # Unrelated keys should be ignored
    assert "APP_NAME" not in stripe
    # Original object should be untouched
    assert secrets["STRIPE_KEY"] == "sk_123"

def test_secrets_require():
    secrets = Secrets({"A": "1", "B": "2"})
    
    # Should pass (chainable)
    assert secrets.require("A", "B") is secrets
    
    # Should fail
    with pytest.raises(RedenvError, match="Missing required secrets: C"):
        secrets.require("A", "C")

def test_secrets_masking():
    secrets = Secrets({"API_KEY": "secret_value"})
    output = str(secrets)
    
    assert "API_KEY" in output
    assert "secret_value" not in output
    assert "********" in output

def test_secrets_raw_access():
    raw_data = {"BASE": "val", "URL": "${BASE}/path"}
    expanded_data = {"BASE": "val", "URL": "val/path"}
    
    secrets = Secrets(expanded_data, raw_data=raw_data)
    
    assert secrets["URL"] == "val/path"
    assert secrets.raw["URL"] == "${BASE}/path"
    assert secrets.raw["BASE"] == "val"
    
    # Test scoping raw access
    stripe_raw = {"STRIPE_KEY": "${BASE}/key"}
    stripe_expanded = {"STRIPE_KEY": "val/key"}
    full_secrets = Secrets(
        {**expanded_data, **stripe_expanded},
        raw_data={**raw_data, **stripe_raw}
    )
    
    stripe_scope = full_secrets.scope("STRIPE_")
    assert stripe_scope["KEY"] == "val/key"
    assert stripe_scope.raw["KEY"] == "${BASE}/key"
