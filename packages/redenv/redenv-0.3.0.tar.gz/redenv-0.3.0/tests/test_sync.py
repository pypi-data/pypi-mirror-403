import pytest
import json
from unittest.mock import MagicMock, patch
from redenv.sync import Redenv as RedenvSync
from redenv.crypto import encrypt, derive_key, buffer_to_hex, random_bytes

# --- Test Data Setup (Mirroring test_client.py) ---
PASSWORD = "masterpassword"
SALT = random_bytes(16)
TOKEN_SALT = random_bytes(16)
TOKEN_SECRET = "redenv_sk_test"
TOKEN_ID = "stk_test"

# 1. Setup Keys
PEK = derive_key(PASSWORD, SALT)
token_key = derive_key(TOKEN_SECRET, TOKEN_SALT)
pek_hex = buffer_to_hex(PEK)
encrypted_pek_str = encrypt(pek_hex, token_key)

# 2. Metadata
METADATA = {
    "serviceTokens": json.dumps({
        TOKEN_ID: {
            "salt": buffer_to_hex(TOKEN_SALT),
            "encryptedPEK": encrypted_pek_str,
            "name": "Test Token"
        }
    }),
    "historyLimit": "10"
}

# 3. Secret Data
SECRET_KEY = "SYNC_API_KEY"
SECRET_VAL = "sync-secret-value"
encrypted_secret = encrypt(SECRET_VAL, PEK)

SECRET_HISTORY = [
    {
        "version": 1,
        "value": encrypted_secret,
        "user": "sync-user",
        "createdAt": "2023-01-01T00:00:00Z"
    }
]

ENVIRONMENT_DATA = {
    SECRET_KEY: json.dumps(SECRET_HISTORY)
}

# --- Sync Client Fixtures ---
@pytest.fixture
def mock_redis_sync():
    mock = MagicMock()
    
    # Mock hgetall
    def hgetall_side_effect(key):
        if key == "meta@sync-project":
            return METADATA
        if key == "prod:sync-project":
            return ENVIRONMENT_DATA
        return {}
    mock.hgetall.side_effect = hgetall_side_effect
    
    # Mock hget
    def hget_side_effect(key, field):
        if key == "prod:sync-project" and field == SECRET_KEY:
            return json.dumps(SECRET_HISTORY)
        return None
    mock.hget.side_effect = hget_side_effect
    
    return mock

@pytest.fixture
def sync_client(mock_redis_sync):
    # Important: patch where Redis is IMPORTED in the sync client
    with patch("redenv.sync.client.Redis", return_value=mock_redis_sync):
        client = RedenvSync({
            "project": "sync-project",
            "token_id": TOKEN_ID,
            "token": TOKEN_SECRET,
            "environment": "prod",
            "upstash": {"url": "https://mock", "token": "mock"},
            "log": "none"
        })
        return client

# --- Sync Tests ---
def test_sync_load_decrypts(sync_client, mock_redis_sync):
    secrets = sync_client.load()
    assert secrets[SECRET_KEY] == SECRET_VAL
    # Check that it called Redis
    assert mock_redis_sync.hgetall.called

def test_sync_caching(sync_client, mock_redis_sync):
    # First load
    sync_client.load()
    count_after_first = mock_redis_sync.hgetall.call_count
    
    # Second load (should hit cache)
    sync_client.load()
    assert mock_redis_sync.hgetall.call_count == count_after_first

def test_sync_set_secret(sync_client, mock_redis_sync):
    new_val = "new-sync-val"
    sync_client.set(SECRET_KEY, new_val)
    
    # Verify hset was called
    assert mock_redis_sync.hset.called
    args = mock_redis_sync.hset.call_args
    assert args[0][0] == "prod:sync-project"
    assert args[0][1] == SECRET_KEY
    
    written_json = args[0][2]
    history = json.loads(written_json)
    assert history[0]["version"] == 2

def test_sync_get_version(sync_client, mock_redis_sync):
    # Valid version
    val = sync_client.get_version(SECRET_KEY, 1)
    assert val == SECRET_VAL
    
    # Invalid version
    assert sync_client.get_version(SECRET_KEY, 999) is None
